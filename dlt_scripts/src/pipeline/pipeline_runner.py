#!/usr/bin/env python3

import dlt
from typing import Dict, Any, Optional
from datetime import datetime
import time

from .config_models import ConfigurationModel, TableConfig, get_enabled_tables
from ..utils.logging_setup import (
    setup_logging, get_logger, log_configuration_summary, log_pipeline_start,
    log_pipeline_complete, log_pipeline_error
)
from .table_processor import TableProcessor
from .verification import DataVerifier


class PipelineRunner:
    """Main pipeline runner that orchestrates the data migration process."""
    
    def __init__(self, config: ConfigurationModel):
        """
        Initialize the pipeline runner.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        
        # Setup logging
        self.logger = setup_logging(config.logging, "pipeline")
        
        # Initialize components
        self.table_processor = TableProcessor(config, self.logger)
        self.verifier = DataVerifier(config, self.logger)
        
        # Pipeline state
        self.start_time: Optional[datetime] = None
        self.processed_tables: Dict[str, Dict[str, Any]] = {}
    
    def run(self, tables_to_process: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Run the complete data migration pipeline.
        
        Args:
            tables_to_process: Specific tables to process (None = all enabled tables)
            
        Returns:
            Pipeline execution results
        """
        self.start_time = datetime.now()
        
        try:
            log_pipeline_start(self.logger)
            log_configuration_summary(self.logger, self.config)
            
            # Get tables to process
            enabled_tables = get_enabled_tables(self.config)
            
            if tables_to_process:
                # Filter to only requested tables
                tables_to_run = {
                    name: config for name, config in enabled_tables.items()
                    if name in tables_to_process
                }
                
                # Check for invalid table names
                invalid_tables = set(tables_to_process) - set(enabled_tables.keys())
                if invalid_tables:
                    raise ValueError(f"Invalid table names: {', '.join(invalid_tables)}")
            else:
                tables_to_run = enabled_tables
            
            if not tables_to_run:
                raise ValueError("No tables to process")
            
            self.logger.info(f"Processing {len(tables_to_run)} tables: {', '.join(tables_to_run.keys())}")
            
            # Process each table
            for table_name, table_config in tables_to_run.items():
                table_result = self._process_table(table_name, table_config)
                self.processed_tables[table_name] = table_result
            
            # Run verification if enabled
            verification_results = {}
            if self.config.verification.enabled:
                verification_results = self.verifier.verify_all_tables(
                    list(tables_to_run.keys())
                )
            
            # Calculate total duration
            end_time = datetime.now()
            total_duration = (end_time - self.start_time).total_seconds()
            
            log_pipeline_complete(self.logger, total_duration, len(tables_to_run))
            
            return {
                "status": "success",
                "start_time": self.start_time,
                "end_time": end_time,
                "duration_seconds": total_duration,
                "tables_processed": list(tables_to_run.keys()),
                "table_results": self.processed_tables,
                "verification_results": verification_results
            }
            
        except Exception as e:
            log_pipeline_error(self.logger, e)
            
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
            
            return {
                "status": "failed",
                "start_time": self.start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "error": str(e),
                "error_type": type(e).__name__,
                "tables_processed": list(self.processed_tables.keys()),
                "table_results": self.processed_tables
            }
    
    def _process_table(self, table_name: str, table_config: TableConfig) -> Dict[str, Any]:
        """
        Process a single table.
        
        Args:
            table_name: Name of the table to process
            table_config: Table configuration
            
        Returns:
            Table processing results
        """
        start_time = time.time()
        
        try:
            # Process the table using table processor
            load_info = self.table_processor.process_table(table_name, table_config)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract basic statistics from load_info
            row_count = None
            load_id = None
            state = None
            
            if load_info and load_info.load_packages:
                package = load_info.load_packages[0]
                load_id = package.load_id
                state = package.state
                
                # Try to extract row count if available
                try:
                    if hasattr(package, 'jobs') and package.jobs:
                        jobs_list = list(package.jobs) if hasattr(package.jobs, '__iter__') else []
                        # This is a simplified approach - in practice, you might need
                        # to sum up row counts from multiple jobs for the same table
                        for job in jobs_list:
                            if hasattr(job, 'table_name') and job.table_name == table_config.destination_table:
                                # Row count extraction would depend on DLT version and job type
                                break
                except (TypeError, AttributeError):
                    pass
            
            result = {
                "status": "success",
                "duration_seconds": duration,
                "load_id": load_id,
                "state": state,
                "disposition": table_config.disposition,
                "incremental_enabled": table_config.incremental.enabled
            }
            
            if row_count is not None:
                result["row_count"] = row_count
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            log_pipeline_error(self.logger, e, table_name)
            
            return {
                "status": "failed",
                "duration_seconds": duration,
                "error": str(e),
                "error_type": type(e).__name__,
                "disposition": table_config.disposition,
                "incremental_enabled": table_config.incremental.enabled
            }
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline statistics.
        
        Returns:
            Pipeline statistics dictionary
        """
        if not self.processed_tables:
            return {"message": "No tables have been processed yet"}
        
        total_tables = len(self.processed_tables)
        successful_tables = sum(1 for result in self.processed_tables.values() if result["status"] == "success")
        failed_tables = total_tables - successful_tables
        
        total_duration = sum(result["duration_seconds"] for result in self.processed_tables.values())
        
        stats = {
            "total_tables": total_tables,
            "successful_tables": successful_tables,
            "failed_tables": failed_tables,
            "total_duration_seconds": total_duration,
            "average_duration_per_table": total_duration / total_tables if total_tables > 0 else 0,
            "success_rate": (successful_tables / total_tables * 100) if total_tables > 0 else 0
        }
        
        # Add per-table breakdown
        stats["table_breakdown"] = {
            name: {
                "status": result["status"],
                "duration": result["duration_seconds"],
                "disposition": result["disposition"]
            }
            for name, result in self.processed_tables.items()
        }
        
        return stats
    
    def retry_failed_tables(self) -> Dict[str, Any]:
        """
        Retry processing of failed tables.
        
        Returns:
            Retry results
        """
        failed_tables = [
            name for name, result in self.processed_tables.items()
            if result["status"] == "failed"
        ]
        
        if not failed_tables:
            self.logger.info("No failed tables to retry")
            return {"message": "No failed tables to retry"}
        
        self.logger.info(f"Retrying {len(failed_tables)} failed tables: {', '.join(failed_tables)}")
        
        # Run pipeline again with only failed tables
        return self.run(failed_tables)