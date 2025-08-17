#!/usr/bin/env python3
"""
Extract processor for parquet-based pipeline.
Handles extraction of data from source databases to parquet archive.
"""

import dlt
from dlt.sources.sql_database import sql_database
from typing import Optional, Any, Dict, List, Tuple
from datetime import datetime
import logging
import os

from .config_models import ConfigurationModel, TableConfig
from .archive_manager import ArchiveManager
from ..utils.logging_setup import get_logger
from ..utils.schema_analyzer import SchemaAnalyzer


class ExtractProcessor:
    """Processes data extraction to parquet archive."""
    
    def __init__(self, config: ConfigurationModel, logger: Optional[logging.Logger] = None):
        """
        Initialize extract processor.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.extract_logger = get_logger("extract_processor")
        
        # Initialize archive manager
        self.archive_manager = ArchiveManager(
            archive_path=self.config.archive.storage_path,
            manifest_path=self.config.archive.manifest_path,
            retention_days=self.config.archive.retention_days,
            logger=self.extract_logger
        )
        
        # Initialize schema analyzer
        if self.config.pipeline.pipeline_mode.value in ['direct', 'extract_only', 'two_stage']:
            source_conn = self.config.connections["source"].connection_string
            self.schema_analyzer = SchemaAnalyzer(source_conn, self.extract_logger)
        else:
            self.schema_analyzer = None
        
        # Set naming convention environment variable
        os.environ["SCHEMA__NAMING"] = self.config.pipeline.naming_convention.value
    
    def extract_table(
        self,
        table_name: str,
        table_config: TableConfig,
        batch_id: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract a single table to parquet archive.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            batch_id: Optional custom batch ID
            custom_metadata: Additional metadata
            
        Returns:
            Tuple of (batch_id, extraction_results)
        """
        try:
            self.extract_logger.info(f"Starting extraction for table: {table_name}")
            
            # Prepare metadata
            metadata = {
                "table_name": table_name,
                "source_table": table_config.source_table,
                "extraction_time": datetime.now().isoformat(),
                "pipeline_mode": self.config.pipeline.pipeline_mode.value,
                "incremental_enabled": table_config.incremental.enabled,
                "extraction_type": "incremental" if table_config.incremental.enabled else "full"
            }
            
            if custom_metadata:
                metadata.update(custom_metadata)
            
            # Add source stats if requested
            if self.config.extract.metadata.get("include_source_stats", True):
                try:
                    source_stats = self._get_source_table_stats(table_config)
                    metadata["source_stats"] = source_stats
                except Exception as e:
                    self.extract_logger.warning(f"Failed to get source stats: {e}")
            
            # Add schema info if requested
            if self.config.extract.metadata.get("include_schema_info", True):
                try:
                    schema_info = self._get_table_schema_info(table_config)
                    metadata["schema_info"] = schema_info
                except Exception as e:
                    self.extract_logger.warning(f"Failed to get schema info: {e}")
            
            # Create extraction batch
            if batch_id is None:
                batch_id, batch = self.archive_manager.create_extraction_batch(
                    table_name=table_name,
                    source_query=self._build_source_query(table_config),
                    watermark_value=self._get_watermark_value(table_config),
                    metadata=metadata
                )
            else:
                batch_id, batch = self.archive_manager.create_extraction_batch(
                    table_name=table_name,
                    source_query=self._build_source_query(table_config),
                    watermark_value=self._get_watermark_value(table_config),
                    metadata=metadata,
                    timestamp=datetime.now()
                )
            
            # Create DLT source
            source = self._create_dlt_source(table_config)
            
            # Extract data using DLT
            data = self._extract_data_with_dlt(source, table_config)
            
            # Determine partitioning
            partition_cols = self._get_partition_columns(table_config)
            
            # Store in archive
            file_info = self.archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=data,
                partition_cols=partition_cols,
                compression=self.config.archive.compression,
                metadata=metadata
            )
            
            # Prepare results
            results = {
                "batch_id": batch_id,
                "table_name": table_name,
                "status": "completed",
                "row_count": file_info.row_count,
                "file_size_bytes": file_info.size_bytes,
                "file_path": str(file_info.path),
                "extraction_time": datetime.now().isoformat(),
                "metadata": metadata
            }
            
            self.extract_logger.info(f"✅ Successfully extracted table {table_name}")
            self.extract_logger.info(f"  Batch ID: {batch_id}")
            self.extract_logger.info(f"  Rows: {file_info.row_count:,}")
            self.extract_logger.info(f"  Size: {file_info.size_bytes:,} bytes")
            
            return batch_id, results
            
        except Exception as e:
            self.extract_logger.error(f"❌ Failed to extract table {table_name}: {e}")
            
            # Mark batch as failed if it was created
            if 'batch_id' in locals():
                try:
                    self.archive_manager.manifest_manager.update_batch_status(
                        batch_id=batch_id,
                        status="failed",
                        error_message=str(e),
                        completed_at=datetime.now()
                    )
                except:
                    pass
            
            raise
    
    def extract_tables(
        self,
        table_names: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract multiple tables to parquet archive.
        
        Args:
            table_names: Specific tables to extract (None = all enabled)
            custom_metadata: Additional metadata for all extractions
            
        Returns:
            Dictionary of extraction results by table name
        """
        try:
            # Get tables to extract
            if table_names:
                tables_to_extract = {
                    name: config for name, config in self.config.tables.items()
                    if name in table_names and config.enabled
                }
                
                # Check for invalid table names
                invalid_tables = set(table_names) - set(self.config.tables.keys())
                if invalid_tables:
                    raise ValueError(f"Invalid table names: {', '.join(invalid_tables)}")
            else:
                tables_to_extract = {
                    name: config for name, config in self.config.tables.items()
                    if config.enabled
                }
            
            if not tables_to_extract:
                raise ValueError("No tables to extract")
            
            self.extract_logger.info(f"Starting extraction for {len(tables_to_extract)} tables")
            
            results = {}
            failed_tables = []
            
            # Process each table
            for table_name, table_config in tables_to_extract.items():
                try:
                    batch_id, table_result = self.extract_table(
                        table_name=table_name,
                        table_config=table_config,
                        custom_metadata=custom_metadata
                    )
                    results[table_name] = table_result
                    
                except Exception as e:
                    self.extract_logger.error(f"Failed to extract table {table_name}: {e}")
                    failed_tables.append(table_name)
                    results[table_name] = {
                        "status": "failed",
                        "error": str(e),
                        "table_name": table_name
                    }
            
            # Summary
            successful_tables = len([r for r in results.values() if r.get("status") == "completed"])
            
            self.extract_logger.info(f"✅ Extraction completed:")
            self.extract_logger.info(f"  Successful: {successful_tables}")
            self.extract_logger.info(f"  Failed: {len(failed_tables)}")
            
            if failed_tables:
                self.extract_logger.warning(f"  Failed tables: {', '.join(failed_tables)}")
            
            return results
            
        except Exception as e:
            self.extract_logger.error(f"❌ Extraction batch failed: {e}")
            raise
    
    def _create_dlt_source(self, table_config: TableConfig):
        """Create DLT source for table extraction."""
        try:
            # Get source connection
            source_conn = self.config.connections["source"].connection_string
            source_schema = self.config.connections["source"].schema_name
            
            # Create SQL database source
            if table_config.custom_sql:
                # Use custom SQL query
                source = sql_database(
                    credentials=source_conn,
                    schema=source_schema,
                    table_names=[],
                    chunk_size=self.config.pipeline.chunk_size
                ).with_resources(table_config.custom_sql)
            else:
                # Use table name
                source_table = table_config.source_table
                
                # Handle incremental loading
                if table_config.incremental.enabled:
                    # Create incremental source
                    source = sql_database(
                        credentials=source_conn,
                        schema=source_schema,
                        table_names=[source_table],
                        chunk_size=self.config.pipeline.chunk_size
                    )
                    
                    # Apply incremental configuration
                    resource = source.resources[source_table]
                    if table_config.incremental.strategy == "timestamp":
                        resource = resource.add_limit(
                            dlt.sources.incremental(
                                table_config.incremental.watermark_column,
                                initial_value=table_config.incremental.initial_value
                            )
                        )
                    elif table_config.incremental.strategy == "sequence":
                        resource = resource.add_limit(
                            dlt.sources.incremental(
                                table_config.incremental.watermark_column,
                                initial_value=table_config.incremental.initial_value
                            )
                        )
                else:
                    # Full table extraction
                    source = sql_database(
                        credentials=source_conn,
                        schema=source_schema,
                        table_names=[source_table],
                        chunk_size=self.config.pipeline.chunk_size
                    )
            
            # Apply naming convention
            source.schema.naming.naming_convention = self.config.pipeline.naming_convention.value
            
            return source
            
        except Exception as e:
            self.extract_logger.error(f"Failed to create DLT source: {e}")
            raise
    
    def _extract_data_with_dlt(self, source, table_config: TableConfig):
        """Extract data using DLT and return as Arrow Table."""
        try:
            # Create temporary pipeline for extraction
            pipeline_name = f"extract_{table_config.source_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Use filesystem destination for extraction
            pipeline = dlt.pipeline(
                pipeline_name=pipeline_name,
                destination="filesystem",
                dataset_name="extract_temp"
            )
            
            # Run extraction
            load_info = pipeline.run(source)
            
            # Get the extracted data path
            # DLT filesystem destination saves to the pipeline working directory
            extract_path = pipeline.working_dir / "extract_temp"
            
            # Load the parquet data back as Arrow Table
            import pyarrow.parquet as pq
            
            # Find the parquet files
            parquet_files = list(extract_path.rglob("*.parquet"))
            if not parquet_files:
                raise ValueError("No parquet files found after extraction")
            
            # Read the data
            if len(parquet_files) == 1:
                data = pq.read_table(str(parquet_files[0]))
            else:
                # Multiple files, read as dataset
                data = pq.read_table(str(extract_path))
            
            # Cleanup temporary files
            import shutil
            shutil.rmtree(str(extract_path), ignore_errors=True)
            
            return data
            
        except Exception as e:
            self.extract_logger.error(f"Failed to extract data with DLT: {e}")
            raise
    
    def _build_source_query(self, table_config: TableConfig) -> str:
        """Build the source query for the table."""
        if table_config.custom_sql:
            return table_config.custom_sql
        
        source_table = table_config.source_table
        
        if table_config.where_clause:
            return f"SELECT * FROM {source_table} WHERE {table_config.where_clause}"
        else:
            return f"SELECT * FROM {source_table}"
    
    def _get_watermark_value(self, table_config: TableConfig) -> Optional[Any]:
        """Get the current watermark value for incremental loading."""
        if not table_config.incremental.enabled:
            return None
        
        # For now, return the initial value
        # In a more advanced implementation, this would check the last loaded value
        return table_config.incremental.initial_value
    
    def _get_partition_columns(self, table_config: TableConfig) -> Optional[List[str]]:
        """Determine partition columns for the table."""
        # Check if partitioning is configured in archive settings
        if self.config.archive.partitioning and self.config.archive.partitioning.get("enabled", False):
            partition_col = self.config.archive.partitioning.get("column")
            if partition_col:
                return [partition_col]
        
        # Default: no partitioning
        return None
    
    def _get_source_table_stats(self, table_config: TableConfig) -> Dict[str, Any]:
        """Get statistics about the source table."""
        try:
            if self.schema_analyzer:
                # Use schema analyzer to get table stats
                source_table = table_config.source_table
                schema_info = self.schema_analyzer.analyze_table_schema(source_table)
                
                return {
                    "estimated_row_count": schema_info.get("estimated_row_count", 0),
                    "column_count": len(schema_info.get("columns", [])),
                    "table_size_bytes": schema_info.get("table_size_bytes", 0)
                }
            else:
                return {}
                
        except Exception as e:
            self.extract_logger.warning(f"Failed to get source table stats: {e}")
            return {}
    
    def _get_table_schema_info(self, table_config: TableConfig) -> Dict[str, Any]:
        """Get schema information about the table."""
        try:
            if self.schema_analyzer:
                source_table = table_config.source_table
                schema_info = self.schema_analyzer.analyze_table_schema(source_table)
                
                return {
                    "columns": schema_info.get("columns", []),
                    "primary_key": schema_info.get("primary_key", []),
                    "indexes": schema_info.get("indexes", [])
                }
            else:
                return {}
                
        except Exception as e:
            self.extract_logger.warning(f"Failed to get table schema info: {e}")
            return {}