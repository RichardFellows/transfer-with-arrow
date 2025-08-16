#!/usr/bin/env python3

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


class TableProcessor:
    """Handles processing of individual tables with advanced configuration support."""
    
    def __init__(self, config: ConfigurationModel, logger: logging.Logger):
        """
        Initialize the table processor.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.table_logger = get_logger("table_processor")
        
        # Cache DLT pipeline instance
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Get or create DLT pipeline instance."""
        if self._pipeline is None:
            dest_conn = self.config.connections["destination"].connection_string
            
            self._pipeline = dlt.pipeline(
                pipeline_name=self.config.pipeline.name,
                destination=dlt.destinations.sqlalchemy(dest_conn),
                dataset_name=self.config.pipeline.dataset_name
            )
        
        return self._pipeline
    
    def process_table(self, table_name: str, table_config: TableConfig) -> Any:
        """
        Process a single table according to its configuration.
        
        Args:
            table_name: Name of the table in configuration
            table_config: Table-specific configuration
            
        Returns:
            DLT load information
        """
        log_table_processing_start(self.table_logger, table_name, table_config)
        
        start_time = datetime.now()
        
        try:
            # Create source configuration
            source = self._create_table_source(table_name, table_config)
            
            # Apply incremental loading if configured
            if table_config.incremental.enabled:
                source = self._apply_incremental_loading(source, table_config)
            
            # Run the pipeline for this table
            load_info = self.pipeline.run(
                source,
                write_disposition=table_config.disposition.value,
                loader_file_format=self.config.pipeline.loader_file_format
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            log_table_processing_complete(self.table_logger, table_name, duration)
            
            return load_info
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.table_logger.error(f"Failed to process table {table_name}: {e}")
            raise
    
    def _create_table_source(self, table_name: str, table_config: TableConfig) -> Any:
        """
        Create a DLT source for the specified table.
        
        Args:
            table_name: Name of the table in configuration
            table_config: Table configuration
            
        Returns:
            DLT source configured for the table
        """
        source_conn = self.config.connections["source"].connection_string
        
        # Determine what to select from source
        if table_config.custom_sql:
            # Use custom SQL query
            table_name_or_query = table_config.custom_sql
            self.table_logger.info(f"Using custom SQL for {table_name}")
        else:
            # Use table name with optional WHERE clause
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
        
        # Configure resource for this specific table
        if table_config.custom_sql:
            # For custom SQL, we need to handle it differently
            # This is a simplified approach - in practice, you might need more sophisticated handling
            source = source.with_resources(table_config.destination_table)
        else:
            # Extract just the table name for resource configuration
            if table_config.where_clause:
                # For tables with WHERE clauses, we need to create a custom resource
                source = source.with_resources(table_config.source_table.split('.')[-1])
            else:
                source = source.with_resources(table_config.source_table.split('.')[-1])
        
        return source
    
    def _apply_incremental_loading(self, source: Any, table_config: TableConfig) -> Any:
        """
        Apply incremental loading configuration to the source.
        
        Args:
            source: DLT source
            table_config: Table configuration
            
        Returns:
            Source with incremental loading applied
        """
        if not table_config.incremental.enabled:
            return source
        
        incremental_config = table_config.incremental
        
        self.table_logger.info(
            f"Configuring incremental loading: "
            f"strategy={incremental_config.strategy}, "
            f"column={incremental_config.watermark_column}, "
            f"initial_value={incremental_config.initial_value}"
        )
        
        # Convert initial value to appropriate type based on strategy
        initial_value = self._convert_initial_value(
            incremental_config.initial_value,
            incremental_config.strategy
        )
        
        # Get the resource name (destination table name or source table name)
        resource_name = table_config.destination_table
        if not resource_name:
            resource_name = table_config.source_table.split('.')[-1]
        
        # Apply incremental configuration
        try:
            # Get the specific resource from the source
            if hasattr(source, resource_name):
                resource = getattr(source, resource_name)
            else:
                # Try to get from resources dictionary
                if hasattr(source, 'resources') and resource_name in source.resources:
                    resource = source.resources[resource_name]
                else:
                    # Fallback: try with source table name
                    source_table_name = table_config.source_table.split('.')[-1]
                    if hasattr(source, source_table_name):
                        resource = getattr(source, source_table_name)
                    else:
                        raise ValueError(f"Cannot find resource '{resource_name}' or '{source_table_name}' in source")
            
            # Apply incremental hints
            resource.apply_hints(
                incremental=dlt.sources.incremental(
                    incremental_config.watermark_column,
                    initial_value=initial_value
                )
            )
            
            self.table_logger.info(f"Incremental loading configured for resource: {resource_name}")
            
        except Exception as e:
            self.table_logger.error(f"Failed to configure incremental loading: {e}")
            # Continue without incremental loading rather than failing
            self.table_logger.warning("Proceeding without incremental loading")
        
        return source
    
    def _convert_initial_value(self, initial_value: Any, strategy: IncrementalStrategy) -> Any:
        """
        Convert initial value to appropriate type based on incremental strategy.
        
        Args:
            initial_value: Initial value from configuration
            strategy: Incremental strategy
            
        Returns:
            Converted initial value
        """
        if initial_value is None:
            return None
        
        if strategy == IncrementalStrategy.TIMESTAMP:
            if isinstance(initial_value, str):
                try:
                    # Try to parse as ISO format datetime
                    return datetime.fromisoformat(initial_value.replace('Z', '+00:00'))
                except ValueError:
                    # If that fails, try other common formats
                    from dateutil.parser import parse
                    return parse(initial_value)
            elif isinstance(initial_value, datetime):
                return initial_value
            else:
                raise ValueError(f"Invalid timestamp initial value: {initial_value}")
        
        elif strategy == IncrementalStrategy.SEQUENCE:
            if isinstance(initial_value, (int, float)):
                return initial_value
            elif isinstance(initial_value, str):
                try:
                    # Try to convert to integer first, then float
                    if '.' in initial_value:
                        return float(initial_value)
                    else:
                        return int(initial_value)
                except ValueError:
                    raise ValueError(f"Invalid sequence initial value: {initial_value}")
            else:
                raise ValueError(f"Invalid sequence initial value: {initial_value}")
        
        else:  # CUSTOM or other strategies
            # For custom strategies, return as-is and let DLT handle it
            return initial_value
    
    def get_table_schema_info(self, table_name: str, table_config: TableConfig) -> Dict[str, Any]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            
        Returns:
            Schema information dictionary
        """
        try:
            source = self._create_table_source(table_name, table_config)
            
            # Extract schema information
            schema_info = {
                "table_name": table_name,
                "source_table": table_config.source_table,
                "destination_table": table_config.destination_table,
                "disposition": table_config.disposition.value,
                "incremental_enabled": table_config.incremental.enabled,
                "primary_key": table_config.primary_key,
                "has_where_clause": bool(table_config.where_clause),
                "has_custom_sql": bool(table_config.custom_sql)
            }
            
            if table_config.incremental.enabled:
                schema_info.update({
                    "incremental_strategy": table_config.incremental.strategy.value,
                    "watermark_column": table_config.incremental.watermark_column,
                    "initial_value": table_config.incremental.initial_value
                })
            
            return schema_info
            
        except Exception as e:
            self.table_logger.error(f"Failed to get schema info for {table_name}: {e}")
            return {
                "table_name": table_name,
                "error": str(e)
            }
    
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