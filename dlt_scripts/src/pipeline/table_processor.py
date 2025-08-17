#!/usr/bin/env python3
"""
Enhanced Table Processor with Dynamic Schema Analysis
Automatically analyzes source schema and applies optimal column hints to prevent precision loss
"""

import dlt
from dlt.sources.sql_database import sql_database
from typing import Optional, Any, Dict
from datetime import datetime
import logging

from .config_models import (
    ConfigurationModel, TableConfig, IncrementalStrategy, WriteDisposition
)
from ..utils.logging_setup import (
    log_table_processing_start, log_table_processing_complete, get_logger
)
from ..utils.schema_analyzer import SchemaAnalyzer


class TableProcessor:
    """Enhanced table processor with automatic schema analysis and optimization"""
    
    def __init__(self, config: ConfigurationModel, logger: logging.Logger, auto_optimize: bool = True):
        """
        Initialize the enhanced table processor.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
            auto_optimize: Whether to automatically apply schema optimizations
        """
        self.config = config
        self.logger = logger
        self.table_logger = get_logger("table_processor")
        self.auto_optimize = auto_optimize
        
        # Initialize schema analyzer
        source_conn = self.config.connections["source"].connection_string
        self.schema_analyzer = SchemaAnalyzer(source_conn, self.table_logger)
        
        # Cache DLT pipeline instance
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Get or create DLT pipeline instance."""
        if self._pipeline is None:
            dest_conn = self.config.connections["destination"].connection_string
            
            # Set naming convention via environment variable if not default
            if self.config.pipeline.naming_convention != "snake_case":
                import os
                os.environ["SCHEMA__NAMING"] = self.config.pipeline.naming_convention.value
                self.table_logger.info(f"🏷️ Set environment SCHEMA__NAMING={self.config.pipeline.naming_convention.value}")
            
            # Configure naming convention if not using default
            pipeline_kwargs = {
                "pipeline_name": self.config.pipeline.name,
                "destination": dlt.destinations.sqlalchemy(dest_conn),
                "dataset_name": self.config.pipeline.dataset_name
            }
            
            self._pipeline = dlt.pipeline(**pipeline_kwargs)
            
            # Also try to apply naming convention to the pipeline schema
            if self.config.pipeline.naming_convention != "snake_case":
                self.table_logger.info(f"🏷️ Applying naming convention: {self.config.pipeline.naming_convention}")
                try:
                    # Set the naming convention on the pipeline schema
                    self._pipeline.default_schema.naming.naming_convention = self.config.pipeline.naming_convention.value
                    self.table_logger.info(f"✅ Successfully set pipeline naming convention to: {self.config.pipeline.naming_convention.value}")
                except Exception as e:
                    self.table_logger.warning(f"⚠️ Failed to set pipeline naming convention: {e}")
                    self.table_logger.info("📋 Continuing with environment variable approach...")
        
        return self._pipeline
    
    def process_table(self, table_name: str, table_config: TableConfig) -> Any:
        """
        Process a single table with automatic schema optimization
        
        Args:
            table_name: Name of the table in configuration
            table_config: Table configuration
            
        Returns:
            Processing result from DLT pipeline
        """
        start_time = datetime.now()
        log_table_processing_start(self.table_logger, table_name, table_config)
        
        try:
            # Step 1: Analyze source schema if auto-optimization is enabled
            if self.auto_optimize:
                self.table_logger.info(f"🔍 Analyzing source schema for optimization...")
                schema_hints = self._analyze_and_optimize_schema(table_name, table_config)
            else:
                schema_hints = {}
            
            # Step 2: Create optimized table source
            source = self._create_optimized_table_source(table_name, table_config, schema_hints)
            
            # Step 3: Run the pipeline
            load_info = self.pipeline.run(source)
            
            # Step 4: Log completion
            duration = (datetime.now() - start_time).total_seconds()
            log_table_processing_complete(self.table_logger, table_name, duration)
            
            return load_info
            
        except Exception as e:
            self.table_logger.error(f"Failed to process table {table_name}: {e}")
            raise
    
    def _analyze_and_optimize_schema(self, table_name: str, table_config: TableConfig) -> Dict[str, Dict[str, Any]]:
        """
        Analyze source schema and generate optimization hints
        
        Args:
            table_name: Table name
            table_config: Table configuration
            
        Returns:
            Dictionary of column hints for optimization
        """
        try:
            # Extract schema and table name from source_table
            if "." in table_config.source_table:
                schema_name, source_table_name = table_config.source_table.split(".", 1)
            else:
                schema_name = "dbo"
                source_table_name = table_config.source_table
            
            # Analyze schema
            column_hints = self.schema_analyzer.analyze_table_schema(source_table_name, schema_name)
            
            # Add column name preservation hints if enabled (fallback method)
            if self.config.pipeline.preserve_column_names and self.config.pipeline.naming_convention == "snake_case":
                self.table_logger.info("🔄 Using fallback column name preservation method...")
                column_hints = self._add_column_name_preservation_hints(source_table_name, schema_name, column_hints)
            
            if column_hints:
                self.table_logger.info(f"🎯 Generated {len(column_hints)} optimization hints for {table_name}")
                
                # Log specific optimizations
                for col_name, hints in column_hints.items():
                    if hints.get("name") and hints.get("name") != col_name:
                        self.table_logger.info(f"  📛 {col_name} → {hints.get('name')} (name preserved)")
                    elif hints.get("data_type") == "decimal":
                        precision = hints.get("precision", "?")
                        scale = hints.get("scale", "?")
                        self.table_logger.info(f"  📊 {col_name} → DECIMAL({precision},{scale})")
                    elif hints.get("data_type") == "text":
                        self.table_logger.info(f"  📝 {col_name} → TEXT (large text)")
                    elif hints.get("data_type") in ["bool", "double", "timestamp"]:
                        self.table_logger.info(f"  🔧 {col_name} → {hints.get('data_type').upper()}")
            else:
                self.table_logger.info(f"ℹ️ No schema optimizations needed for {table_name}")
            
            return column_hints
            
        except Exception as e:
            self.table_logger.warning(f"⚠️ Schema analysis failed for {table_name}: {e}")
            self.table_logger.info("📋 Continuing without schema optimization...")
            return {}
    
    def _add_column_name_preservation_hints(self, source_table_name: str, schema_name: str, existing_hints: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Add column name preservation hints to prevent DLT's automatic snake_case transformation
        
        Args:
            source_table_name: Name of the source table
            schema_name: Database schema name
            existing_hints: Existing column hints from schema analysis
            
        Returns:
            Updated column hints with name preservation
        """
        try:
            import sqlalchemy as sa
            
            source_conn = self.config.connections["source"].connection_string
            engine = sa.create_engine(source_conn)
            
            # Get original column names from source table
            with engine.connect() as conn:
                # Query to get actual column names (preserving case)
                query = sa.text("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = :schema_name 
                    AND TABLE_NAME = :table_name
                    ORDER BY ORDINAL_POSITION
                """)
                
                result = conn.execute(query, {
                    "schema_name": schema_name,
                    "table_name": source_table_name
                })
                
                original_columns = [row[0] for row in result.fetchall()]
            
            # Create or update hints to preserve original column names
            column_hints = existing_hints.copy() if existing_hints else {}
            
            for original_col_name in original_columns:
                # DLT would normally convert PascalCase to snake_case
                # We force it to keep the original name by setting explicit name hint
                if original_col_name not in column_hints:
                    column_hints[original_col_name] = {}
                
                # Set the name hint to preserve the original column name
                column_hints[original_col_name]["name"] = original_col_name
            
            self.table_logger.info(f"🔒 Added name preservation hints for {len(original_columns)} columns")
            return column_hints
            
        except Exception as e:
            self.table_logger.warning(f"⚠️ Failed to add column name preservation hints: {e}")
            return existing_hints
    
    def _create_optimized_table_source(self, table_name: str, table_config: TableConfig, schema_hints: Dict[str, Dict[str, Any]]) -> Any:
        """
        Create an optimized DLT source with schema hints applied
        
        Args:
            table_name: Table name
            table_config: Table configuration
            schema_hints: Generated schema optimization hints
            
        Returns:
            Optimized DLT source
        """
        source_conn = self.config.connections["source"].connection_string
        
        # Determine what to select from source
        if table_config.custom_sql:
            table_name_or_query = table_config.custom_sql
            self.table_logger.info(f"Using custom SQL for {table_name}")
        else:
            table_name_or_query = table_config.source_table
            if table_config.where_clause:
                table_name_or_query = f"SELECT * FROM {table_config.source_table} WHERE {table_config.where_clause}"
                self.table_logger.info(f"Applied WHERE clause for {table_name}: {table_config.where_clause}")
        
        # Create base source configuration
        source = sql_database(
            source_conn,
            backend=self.config.pipeline.backend.value,
            backend_kwargs=self.config.pipeline.backend_kwargs,
            reflection_level=self.config.pipeline.reflection_level,
            chunk_size=self.config.pipeline.chunk_size
        )
        
        # Apply naming convention to the source schema if not default
        if self.config.pipeline.naming_convention != "snake_case":
            try:
                self.table_logger.info(f"🏷️ Setting source naming convention to: {self.config.pipeline.naming_convention}")
                source.schema.naming.naming_convention = self.config.pipeline.naming_convention.value
                self.table_logger.info(f"✅ Source naming convention successfully set to: {self.config.pipeline.naming_convention.value}")
            except Exception as e:
                self.table_logger.warning(f"⚠️ Failed to set source naming convention: {e}")
                self.table_logger.info("📋 Continuing with default snake_case naming...")
        
        # Configure resource for this specific table
        if table_config.custom_sql:
            resource = source.with_resources(table_config.destination_table)
            resource_obj = resource.resources[table_config.destination_table]
        else:
            # Extract just the table name for resource configuration
            source_table_name = table_config.source_table.split(".")[-1]
            resource = source.with_resources(source_table_name)
            resource_obj = resource.resources[source_table_name]
        
        # Apply schema optimization hints
        if schema_hints:
            self.table_logger.info(f"🔧 Applying {len(schema_hints)} schema optimizations...")
            resource_obj = resource_obj.apply_hints(columns=schema_hints)
        
        # Apply table-level configuration
        disposition_value = table_config.disposition.value if hasattr(table_config.disposition, 'value') else table_config.disposition
        resource_obj = resource_obj.apply_hints(
            table_name=table_config.destination_table,
            write_disposition=disposition_value
        )
        
        # Apply incremental loading configuration if enabled
        if table_config.incremental and table_config.incremental.enabled:
            resource_obj = self._apply_incremental_loading(table_name, table_config, resource_obj)
        
        # Apply primary key if specified
        if hasattr(table_config, 'primary_key') and table_config.primary_key:
            resource_obj = resource_obj.apply_hints(primary_key=table_config.primary_key)
        
        return resource_obj
    
    def _apply_incremental_loading(self, table_name: str, table_config: TableConfig, resource: Any) -> Any:
        """Apply incremental loading configuration to resource"""
        incremental_config = table_config.incremental
        
        if incremental_config.strategy == IncrementalStrategy.TIMESTAMP:
            if incremental_config.watermark_column and incremental_config.initial_value:
                initial_value = self._convert_initial_value(incremental_config.initial_value)
                
                resource = resource.apply_hints(
                    incremental=dlt.sources.incremental(
                        incremental_config.watermark_column,
                        initial_value=initial_value
                    )
                )
                
                self.table_logger.info(f"Applied incremental loading: {incremental_config.watermark_column} >= {initial_value}")
            else:
                self.table_logger.warning(f"Incremental loading enabled but missing watermark_column or initial_value")
        
        return resource
    
    def _convert_initial_value(self, initial_value: str) -> Any:
        """Convert string initial value to appropriate type"""
        if isinstance(initial_value, str):
            try:
                return datetime.fromisoformat(initial_value.replace('Z', '+00:00'))
            except ValueError:
                return initial_value
        return initial_value
    
    def get_table_schema_info(self, table_name: str, table_config: TableConfig) -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        try:
            if "." in table_config.source_table:
                schema_name, source_table_name = table_config.source_table.split(".", 1)
            else:
                schema_name = "dbo"
                source_table_name = table_config.source_table
            
            return self.schema_analyzer.get_schema_summary(source_table_name, schema_name)
        except Exception as e:
            self.table_logger.error(f"Failed to get schema info for {table_name}: {e}")
            return {}
    
    def generate_optimized_config(self, table_name: str, schema: str = "dbo") -> Dict[str, Any]:
        """
        Generate an optimized configuration for a table
        
        Args:
            table_name: Table name to analyze
            schema: Database schema
            
        Returns:
            Complete optimized table configuration
        """
        return self.schema_analyzer.generate_config_section(table_name, schema)

    def estimate_table_size(self, table_name: str, table_config: TableConfig) -> Optional[int]:
        """
        Estimate the number of rows in a table.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            
        Returns:
            Estimated row count or None if estimation fails
        """
        try:
            import sqlalchemy as sa
            
            source_conn = self.config.connections["source"].connection_string
            engine = sa.create_engine(source_conn)
            
            # Build count query
            if table_config.where_clause:
                count_query = f"SELECT COUNT(*) FROM {table_config.source_table} WHERE {table_config.where_clause}"
            else:
                count_query = f"SELECT COUNT(*) FROM {table_config.source_table}"
            
            with engine.connect() as conn:
                result = conn.execute(sa.text(count_query))
                row_count = result.scalar()
            
            self.table_logger.info(f"Estimated row count for {table_name}: {row_count:,}")
            return row_count
            
        except Exception as e:
            self.table_logger.warning(f"Failed to estimate size for {table_name}: {e}")
            return None


# Convenience function for direct usage  
def create_table_processor(config: ConfigurationModel, logger: logging.Logger, auto_optimize: bool = True) -> TableProcessor:
    """
    Create a table processor with schema optimization
    
    Args:
        config: Pipeline configuration
        logger: Logger instance
        auto_optimize: Whether to enable automatic schema optimization
        
    Returns:
        Table processor instance
    """
    return TableProcessor(config, logger, auto_optimize)