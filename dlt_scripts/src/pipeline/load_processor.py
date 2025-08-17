#!/usr/bin/env python3
"""
Load processor for parquet-based pipeline.
Handles loading of data from parquet archive to destination databases.
"""

import dlt
from typing import Optional, Any, Dict, List, Tuple
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

from .config_models import ConfigurationModel, TableConfig, BatchSelection, PipelineMode
from .archive_manager import ArchiveManager
from .verification import DataVerifier
from ..utils.logging_setup import get_logger
from ..utils.manifest_manager import BatchStatus


class LoadProcessor:
    """Processes data loading from parquet archive to destination."""
    
    def __init__(self, config: ConfigurationModel, logger: Optional[logging.Logger] = None):
        """
        Initialize load processor.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.load_logger = get_logger("load_processor")
        
        # Initialize archive manager
        self.archive_manager = ArchiveManager(
            archive_path=self.config.archive.storage_path,
            manifest_path=self.config.archive.manifest_path,
            retention_days=self.config.archive.retention_days,
            logger=self.load_logger
        )
        
        # Initialize verifier if needed
        if self.config.verification.enabled:
            self.verifier = DataVerifier(config, self.load_logger)
        else:
            self.verifier = None
        
        # Set naming convention environment variable
        os.environ["SCHEMA__NAMING"] = self.config.pipeline.naming_convention.value
        
        # Cache DLT pipeline instance
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Get or create DLT pipeline instance for loading."""
        if self._pipeline is None:
            dest_conn = self.config.connections["destination"].connection_string
            
            self._pipeline = dlt.pipeline(
                pipeline_name=self.config.pipeline.name,
                destination="mssql",
                dataset_name=self.config.pipeline.dataset_name,
                credentials=dest_conn,
                **self.config.pipeline.backend_kwargs
            )
            
            # Configure backend
            if self.config.pipeline.backend.value == "pyarrow":
                self._pipeline = self._pipeline.with_config(
                    loader_file_format=self.config.pipeline.loader_file_format
                )
        
        return self._pipeline
    
    def load_table_from_batch(
        self,
        table_name: str,
        batch_id: str,
        table_config: Optional[TableConfig] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a specific table from a specific batch.
        
        Args:
            table_name: Name of the table
            batch_id: Batch identifier to load
            table_config: Table configuration (optional, will be looked up if not provided)
            custom_metadata: Additional metadata
            
        Returns:
            Load operation results
        """
        try:
            self.load_logger.info(f"Starting load for table {table_name} from batch {batch_id}")
            
            # Get table config if not provided
            if table_config is None:
                if table_name not in self.config.tables:
                    raise ValueError(f"Table {table_name} not found in configuration")
                table_config = self.config.tables[table_name]
            
            # Validate batch exists and is completed
            batch = self.archive_manager.manifest_manager.get_batch(batch_id)
            if not batch:
                raise ValueError(f"Batch {batch_id} not found")
            
            if batch.status != BatchStatus.COMPLETED:
                raise ValueError(f"Batch {batch_id} is not completed (status: {batch.status})")
            
            if batch.table_name != table_name:
                raise ValueError(f"Batch {batch_id} is for table {batch.table_name}, not {table_name}")
            
            # Load data from archive
            data = self.archive_manager.load_extraction_data(
                batch_id=batch_id,
                table_name=table_name
            )
            
            # Convert Arrow Table to DLT resource
            resource = dlt.resource(
                data.to_pylist(),
                name=table_config.destination_table or table_name,
                write_disposition=table_config.disposition.value,
                primary_key=table_config.primary_key
            )
            
            # Apply incremental settings if configured
            if table_config.incremental.enabled:
                resource = resource.add_limit(
                    dlt.sources.incremental(
                        table_config.incremental.watermark_column,
                        initial_value=table_config.incremental.initial_value
                    )
                )
            
            # Load to destination
            load_info = self.pipeline.run(resource)
            
            # Prepare results
            results = {
                "batch_id": batch_id,
                "table_name": table_name,
                "destination_table": table_config.destination_table or table_name,
                "status": "completed",
                "row_count": len(data),
                "load_time": datetime.now().isoformat(),
                "load_info": {
                    "dataset_name": load_info.dataset_name,
                    "destination_name": load_info.destination_name,
                    "pipeline_name": load_info.pipeline_name,
                    "loads_ids": [load.load_id for load in load_info.loads],
                    "started_at": load_info.started_at.isoformat() if load_info.started_at else None,
                    "finished_at": load_info.finished_at.isoformat() if load_info.finished_at else None
                }
            }
            
            # Run verification if enabled
            if self.verifier and self.config.load.verification_mode == "standard":
                try:
                    verification_results = self._verify_loaded_data(table_name, table_config, batch)
                    results["verification"] = verification_results
                except Exception as e:
                    self.load_logger.warning(f"Verification failed for {table_name}: {e}")
                    results["verification"] = {"status": "failed", "error": str(e)}
            
            self.load_logger.info(f"✅ Successfully loaded table {table_name} from batch {batch_id}")
            self.load_logger.info(f"  Rows loaded: {len(data):,}")
            self.load_logger.info(f"  Destination: {table_config.destination_table or table_name}")
            
            return results
            
        except Exception as e:
            self.load_logger.error(f"❌ Failed to load table {table_name} from batch {batch_id}: {e}")
            raise
    
    def load_table_latest(
        self,
        table_name: str,
        table_config: Optional[TableConfig] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a table from the latest available batch.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration (optional)
            custom_metadata: Additional metadata
            
        Returns:
            Load operation results
        """
        try:
            # Get latest batch for table
            latest_batch = self.archive_manager.get_latest_batch(
                table_name=table_name,
                status=BatchStatus.COMPLETED
            )
            
            if not latest_batch:
                raise ValueError(f"No completed batches found for table {table_name}")
            
            self.load_logger.info(f"Loading table {table_name} from latest batch {latest_batch.batch_id}")
            
            return self.load_table_from_batch(
                table_name=table_name,
                batch_id=latest_batch.batch_id,
                table_config=table_config,
                custom_metadata=custom_metadata
            )
            
        except Exception as e:
            self.load_logger.error(f"❌ Failed to load latest batch for table {table_name}: {e}")
            raise
    
    def load_table_date_range(
        self,
        table_name: str,
        start_date: datetime,
        end_date: datetime,
        table_config: Optional[TableConfig] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load a table from batches within a date range.
        
        Args:
            table_name: Name of the table
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            table_config: Table configuration (optional)
            custom_metadata: Additional metadata
            
        Returns:
            Load operation results
        """
        try:
            # Get batches in date range
            batches = self.archive_manager.get_batches_in_date_range(
                table_name=table_name,
                start_date=start_date,
                end_date=end_date,
                status=BatchStatus.COMPLETED
            )
            
            if not batches:
                raise ValueError(f"No completed batches found for table {table_name} in date range {start_date.date()} to {end_date.date()}")
            
            self.load_logger.info(f"Loading table {table_name} from {len(batches)} batches in date range")
            
            # Load each batch (this could be optimized to combine batches)
            results = {
                "table_name": table_name,
                "date_range": f"{start_date.date()} to {end_date.date()}",
                "batches_loaded": len(batches),
                "batch_results": [],
                "total_rows": 0
            }
            
            for batch in batches:
                batch_result = self.load_table_from_batch(
                    table_name=table_name,
                    batch_id=batch.batch_id,
                    table_config=table_config,
                    custom_metadata=custom_metadata
                )
                results["batch_results"].append(batch_result)
                results["total_rows"] += batch_result.get("row_count", 0)
            
            results["status"] = "completed"
            results["load_time"] = datetime.now().isoformat()
            
            self.load_logger.info(f"✅ Successfully loaded {len(batches)} batches for table {table_name}")
            self.load_logger.info(f"  Total rows: {results['total_rows']:,}")
            
            return results
            
        except Exception as e:
            self.load_logger.error(f"❌ Failed to load date range for table {table_name}: {e}")
            raise
    
    def load_tables(
        self,
        table_names: Optional[List[str]] = None,
        batch_selection: Optional[BatchSelection] = None,
        specific_batch: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load multiple tables from archive.
        
        Args:
            table_names: Specific tables to load (None = all enabled)
            batch_selection: How to select batches to load
            specific_batch: Specific batch ID (for SPECIFIC selection)
            start_date: Start date (for DATE_RANGE selection)
            end_date: End date (for DATE_RANGE selection)
            custom_metadata: Additional metadata
            
        Returns:
            Dictionary of load results by table name
        """
        try:
            # Get tables to load
            if table_names:
                tables_to_load = {
                    name: config for name, config in self.config.tables.items()
                    if name in table_names and config.enabled
                }
                
                # Check for invalid table names
                invalid_tables = set(table_names) - set(self.config.tables.keys())
                if invalid_tables:
                    raise ValueError(f"Invalid table names: {', '.join(invalid_tables)}")
            else:
                tables_to_load = {
                    name: config for name, config in self.config.tables.items()
                    if config.enabled
                }
            
            if not tables_to_load:
                raise ValueError("No tables to load")
            
            # Determine batch selection strategy
            if batch_selection is None:
                batch_selection = self.config.load.batch_selection
            
            self.load_logger.info(f"Starting load for {len(tables_to_load)} tables using {batch_selection.value} selection")
            
            results = {}
            failed_tables = []
            
            # Process each table
            for table_name, table_config in tables_to_load.items():
                try:
                    if batch_selection == BatchSelection.LATEST:
                        table_result = self.load_table_latest(
                            table_name=table_name,
                            table_config=table_config,
                            custom_metadata=custom_metadata
                        )
                    elif batch_selection == BatchSelection.SPECIFIC:
                        if not specific_batch:
                            raise ValueError("specific_batch is required for SPECIFIC batch selection")
                        table_result = self.load_table_from_batch(
                            table_name=table_name,
                            batch_id=specific_batch,
                            table_config=table_config,
                            custom_metadata=custom_metadata
                        )
                    elif batch_selection == BatchSelection.DATE_RANGE:
                        if not start_date or not end_date:
                            raise ValueError("start_date and end_date are required for DATE_RANGE batch selection")
                        table_result = self.load_table_date_range(
                            table_name=table_name,
                            start_date=start_date,
                            end_date=end_date,
                            table_config=table_config,
                            custom_metadata=custom_metadata
                        )
                    else:
                        raise ValueError(f"Unsupported batch selection: {batch_selection}")
                    
                    results[table_name] = table_result
                    
                except Exception as e:
                    self.load_logger.error(f"Failed to load table {table_name}: {e}")
                    failed_tables.append(table_name)
                    results[table_name] = {
                        "status": "failed",
                        "error": str(e),
                        "table_name": table_name
                    }
            
            # Summary
            successful_tables = len([r for r in results.values() if r.get("status") == "completed"])
            
            self.load_logger.info(f"✅ Load operation completed:")
            self.load_logger.info(f"  Successful: {successful_tables}")
            self.load_logger.info(f"  Failed: {len(failed_tables)}")
            
            if failed_tables:
                self.load_logger.warning(f"  Failed tables: {', '.join(failed_tables)}")
            
            return results
            
        except Exception as e:
            self.load_logger.error(f"❌ Load batch failed: {e}")
            raise
    
    def _verify_loaded_data(
        self,
        table_name: str,
        table_config: TableConfig,
        batch: Any
    ) -> Dict[str, Any]:
        """Verify loaded data against the source batch."""
        try:
            if not self.verifier:
                return {"status": "skipped", "reason": "verification disabled"}
            
            # Run basic verification
            verification_results = self.verifier.verify_table(table_name, table_config)
            
            # Add batch-specific checks
            verification_results["batch_verification"] = {
                "batch_id": batch.batch_id,
                "expected_rows": batch.row_count,
                "batch_created": batch.created_at.isoformat(),
                "verification_time": datetime.now().isoformat()
            }
            
            return verification_results
            
        except Exception as e:
            self.load_logger.warning(f"Verification failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    def list_available_batches(
        self,
        table_name: Optional[str] = None,
        status: Optional[BatchStatus] = None,
        last_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List available batches for loading.
        
        Args:
            table_name: Filter by table name
            status: Filter by status (defaults to COMPLETED)
            last_n: Return only the last N batches
            
        Returns:
            List of available batches with metadata
        """
        if status is None:
            status = BatchStatus.COMPLETED
        
        batches = self.archive_manager.list_available_batches(
            table_name=table_name,
            status=status,
            last_n=last_n
        )
        
        # Convert to dictionaries with additional info
        batch_list = []
        for batch in batches:
            batch_dict = batch.to_dict()
            
            # Add file system info
            if batch.file_path:
                file_path = Path(batch.file_path)
                batch_dict["file_exists"] = file_path.exists()
                if file_path.exists():
                    batch_dict["file_size_mb"] = round(file_path.stat().st_size / 1024 / 1024, 2)
            
            batch_list.append(batch_dict)
        
        return batch_list
    
    def get_load_recommendations(
        self,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Get recommendations for loading a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with load recommendations
        """
        try:
            # Get latest batch
            latest_batch = self.archive_manager.get_latest_batch(
                table_name=table_name,
                status=BatchStatus.COMPLETED
            )
            
            if not latest_batch:
                return {
                    "table_name": table_name,
                    "recommendation": "no_data",
                    "message": "No completed batches available for this table"
                }
            
            # Check batch age
            batch_age = datetime.now() - latest_batch.created_at
            
            recommendations = {
                "table_name": table_name,
                "latest_batch": {
                    "batch_id": latest_batch.batch_id,
                    "created_at": latest_batch.created_at.isoformat(),
                    "age_hours": round(batch_age.total_seconds() / 3600, 1),
                    "row_count": latest_batch.row_count,
                    "size_mb": round((latest_batch.file_size_bytes or 0) / 1024 / 1024, 2)
                }
            }
            
            # Provide recommendations based on age
            if batch_age < timedelta(hours=1):
                recommendations["recommendation"] = "fresh"
                recommendations["message"] = "Latest batch is very fresh, recommended for loading"
            elif batch_age < timedelta(hours=24):
                recommendations["recommendation"] = "good"
                recommendations["message"] = "Latest batch is recent, good for loading"
            elif batch_age < timedelta(days=7):
                recommendations["recommendation"] = "acceptable"
                recommendations["message"] = "Latest batch is somewhat old but acceptable"
            else:
                recommendations["recommendation"] = "stale"
                recommendations["message"] = "Latest batch is old, consider running a new extraction"
            
            # Check for multiple recent batches
            recent_batches = self.archive_manager.get_batches_in_date_range(
                table_name=table_name,
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                status=BatchStatus.COMPLETED
            )
            
            recommendations["recent_batches_count"] = len(recent_batches)
            
            if len(recent_batches) > 1:
                recommendations["options"] = {
                    "load_latest": "Load the most recent batch only",
                    "load_range": f"Load all {len(recent_batches)} batches from the last 7 days"
                }
            
            return recommendations
            
        except Exception as e:
            return {
                "table_name": table_name,
                "recommendation": "error",
                "error": str(e)
            }