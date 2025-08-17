#!/usr/bin/env python3
"""
Two-stage pipeline runner that orchestrates extract and load operations.
Supports all pipeline modes: direct, extract-only, load-only, and two-stage.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .config_models import ConfigurationModel, PipelineMode, BatchSelection
from .extract_processor import ExtractProcessor
from .load_processor import LoadProcessor
from .pipeline_runner import PipelineRunner  # For direct mode
from .archive_manager import ArchiveManager
from ..utils.logging_setup import setup_logging, get_logger, log_pipeline_start, log_pipeline_complete


class TwoStagePipelineRunner:
    """
    Orchestrates extract and load operations for the two-stage pipeline architecture.
    Supports all pipeline modes and provides unified interface for all operations.
    """
    
    def __init__(self, config: ConfigurationModel):
        """
        Initialize two-stage pipeline runner.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        
        # Setup logging
        self.logger = setup_logging(config.logging, "two_stage_pipeline")
        self.runner_logger = get_logger("two_stage_runner")
        
        # Initialize processors based on pipeline mode
        self.pipeline_mode = config.pipeline.pipeline_mode
        
        # Initialize archive manager for non-direct modes
        if self.pipeline_mode != PipelineMode.DIRECT:
            self.archive_manager = ArchiveManager(
                archive_path=config.archive.storage_path,
                manifest_path=config.archive.manifest_path,
                retention_days=config.archive.retention_days,
                logger=self.runner_logger
            )
        else:
            self.archive_manager = None
        
        # Initialize processors
        self.extract_processor = None
        self.load_processor = None
        self.direct_runner = None
        
        if self.pipeline_mode in [PipelineMode.EXTRACT_ONLY, PipelineMode.TWO_STAGE]:
            self.extract_processor = ExtractProcessor(config, self.logger)
        
        if self.pipeline_mode in [PipelineMode.LOAD_ONLY, PipelineMode.TWO_STAGE]:
            self.load_processor = LoadProcessor(config, self.logger)
        
        if self.pipeline_mode == PipelineMode.DIRECT:
            self.direct_runner = PipelineRunner(config)
        
        # Pipeline state
        self.start_time: Optional[datetime] = None
    
    def run(
        self,
        tables_to_process: Optional[List[str]] = None,
        batch_selection: Optional[BatchSelection] = None,
        specific_batch: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the pipeline based on the configured mode.
        
        Args:
            tables_to_process: Specific tables to process (None = all enabled)
            batch_selection: Batch selection strategy for load operations
            specific_batch: Specific batch ID for SPECIFIC selection
            start_date: Start date for DATE_RANGE selection
            end_date: End date for DATE_RANGE selection
            custom_metadata: Additional metadata
            
        Returns:
            Pipeline execution results
        """
        self.start_time = datetime.now()
        
        try:
            log_pipeline_start(self.logger)
            self.runner_logger.info(f"🚀 Starting {self.pipeline_mode.value} pipeline")
            
            if self.pipeline_mode == PipelineMode.DIRECT:
                return self._run_direct_mode(tables_to_process)
            elif self.pipeline_mode == PipelineMode.EXTRACT_ONLY:
                return self._run_extract_only(tables_to_process, custom_metadata)
            elif self.pipeline_mode == PipelineMode.LOAD_ONLY:
                return self._run_load_only(
                    tables_to_process, batch_selection, specific_batch, 
                    start_date, end_date, custom_metadata
                )
            elif self.pipeline_mode == PipelineMode.TWO_STAGE:
                return self._run_two_stage(
                    tables_to_process, batch_selection, custom_metadata
                )
            else:
                raise ValueError(f"Unsupported pipeline mode: {self.pipeline_mode}")
                
        except Exception as e:
            self.runner_logger.error(f"❌ Pipeline failed: {e}")
            return {
                "status": "failed",
                "mode": self.pipeline_mode.value,
                "error": str(e),
                "duration": (datetime.now() - self.start_time).total_seconds(),
                "started_at": self.start_time.isoformat()
            }
        
        finally:
            if self.start_time:
                duration = datetime.now() - self.start_time
                log_pipeline_complete(self.logger, duration.total_seconds())
    
    def extract_tables(
        self,
        tables_to_process: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract tables to parquet archive.
        
        Args:
            tables_to_process: Specific tables to extract
            custom_metadata: Additional metadata
            
        Returns:
            Extraction results
        """
        if not self.extract_processor:
            raise ValueError("Extract processor not available for this pipeline mode")
        
        self.runner_logger.info("📦 Starting extraction phase")
        
        try:
            results = self.extract_processor.extract_tables(
                table_names=tables_to_process,
                custom_metadata=custom_metadata
            )
            
            self.runner_logger.info("✅ Extraction phase completed")
            return {
                "phase": "extract",
                "status": "completed",
                "tables": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.runner_logger.error(f"❌ Extraction phase failed: {e}")
            raise
    
    def load_tables(
        self,
        tables_to_process: Optional[List[str]] = None,
        batch_selection: Optional[BatchSelection] = None,
        specific_batch: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load tables from parquet archive.
        
        Args:
            tables_to_process: Specific tables to load
            batch_selection: Batch selection strategy
            specific_batch: Specific batch ID
            start_date: Start date for date range
            end_date: End date for date range
            custom_metadata: Additional metadata
            
        Returns:
            Load results
        """
        if not self.load_processor:
            raise ValueError("Load processor not available for this pipeline mode")
        
        self.runner_logger.info("🚚 Starting load phase")
        
        try:
            results = self.load_processor.load_tables(
                table_names=tables_to_process,
                batch_selection=batch_selection,
                specific_batch=specific_batch,
                start_date=start_date,
                end_date=end_date,
                custom_metadata=custom_metadata
            )
            
            self.runner_logger.info("✅ Load phase completed")
            return {
                "phase": "load",
                "status": "completed",
                "tables": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.runner_logger.error(f"❌ Load phase failed: {e}")
            raise
    
    def _run_direct_mode(self, tables_to_process: Optional[List[str]]) -> Dict[str, Any]:
        """Run in direct mode (traditional pipeline)."""
        self.runner_logger.info("⚡ Running direct mode pipeline")
        
        if not self.direct_runner:
            raise ValueError("Direct runner not available")
        
        results = self.direct_runner.run(tables_to_process)
        
        return {
            "mode": "direct",
            "status": "completed",
            "results": results,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.now().isoformat()
        }
    
    def _run_extract_only(
        self,
        tables_to_process: Optional[List[str]],
        custom_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run in extract-only mode."""
        self.runner_logger.info("📦 Running extract-only mode")
        
        extract_results = self.extract_tables(tables_to_process, custom_metadata)
        
        return {
            "mode": "extract_only",
            "status": "completed",
            "extract_results": extract_results,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.now().isoformat()
        }
    
    def _run_load_only(
        self,
        tables_to_process: Optional[List[str]],
        batch_selection: Optional[BatchSelection],
        specific_batch: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        custom_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run in load-only mode."""
        self.runner_logger.info("🚚 Running load-only mode")
        
        load_results = self.load_tables(
            tables_to_process, batch_selection, specific_batch,
            start_date, end_date, custom_metadata
        )
        
        return {
            "mode": "load_only",
            "status": "completed",
            "load_results": load_results,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.now().isoformat()
        }
    
    def _run_two_stage(
        self,
        tables_to_process: Optional[List[str]],
        batch_selection: Optional[BatchSelection],
        custom_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run in two-stage mode (extract then load)."""
        self.runner_logger.info("🔄 Running two-stage mode")
        
        # Phase 1: Extract
        extract_results = self.extract_tables(tables_to_process, custom_metadata)
        
        # Check if extraction was successful
        successful_extracts = [
            table_name for table_name, result in extract_results["tables"].items()
            if result.get("status") == "completed"
        ]
        
        if not successful_extracts:
            raise ValueError("No successful extractions to load")
        
        self.runner_logger.info(f"📦➡️🚚 Transitioning from extract to load phase for {len(successful_extracts)} tables")
        
        # Phase 2: Load (use latest batches from extract)
        load_results = self.load_tables(
            tables_to_process=successful_extracts,
            batch_selection=BatchSelection.LATEST,  # Load the batches we just created
            custom_metadata=custom_metadata
        )
        
        return {
            "mode": "two_stage",
            "status": "completed",
            "extract_results": extract_results,
            "load_results": load_results,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "started_at": self.start_time.isoformat(),
            "completed_at": datetime.now().isoformat()
        }
    
    def get_archive_status(self) -> Dict[str, Any]:
        """Get comprehensive archive status and statistics."""
        if not self.archive_manager:
            return {"status": "archive_disabled", "mode": self.pipeline_mode.value}
        
        try:
            # Get archive statistics
            stats = self.archive_manager.get_archive_statistics()
            
            # Get recent activity
            recent_batches = self.archive_manager.list_available_batches(last_n=10)
            
            # Get table summaries
            table_summaries = {}
            for table_name in self.config.tables.keys():
                latest_batch = self.archive_manager.get_latest_batch(table_name)
                if latest_batch:
                    table_summaries[table_name] = {
                        "latest_batch_id": latest_batch.batch_id,
                        "latest_batch_date": latest_batch.created_at.isoformat(),
                        "latest_row_count": latest_batch.row_count,
                        "status": latest_batch.status.value
                    }
                else:
                    table_summaries[table_name] = {
                        "status": "no_batches"
                    }
            
            return {
                "status": "active",
                "mode": self.pipeline_mode.value,
                "archive_statistics": stats,
                "table_summaries": table_summaries,
                "recent_batches": [batch.to_dict() for batch in recent_batches],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "mode": self.pipeline_mode.value,
                "error": str(e)
            }
    
    def cleanup_archive(
        self,
        older_than_days: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Clean up old archives."""
        if not self.archive_manager:
            return {"status": "archive_disabled"}
        
        try:
            results = self.archive_manager.cleanup_archive(
                older_than_days=older_than_days,
                dry_run=dry_run
            )
            
            return {
                "status": "completed",
                "cleanup_results": results,
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def validate_archive(self) -> Dict[str, Any]:
        """Validate archive integrity."""
        if not self.archive_manager:
            return {"status": "archive_disabled"}
        
        try:
            validation_results = self.archive_manager.validate_archive_integrity()
            
            return {
                "status": "completed",
                "validation_results": validation_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_load_recommendations(
        self,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get load recommendations for tables."""
        if not self.load_processor:
            return {"status": "load_processor_disabled"}
        
        try:
            if table_name:
                # Get recommendations for specific table
                recommendations = self.load_processor.get_load_recommendations(table_name)
                return {
                    "status": "completed",
                    "table_recommendations": {table_name: recommendations},
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Get recommendations for all tables
                table_recommendations = {}
                for table_name in self.config.tables.keys():
                    table_recommendations[table_name] = self.load_processor.get_load_recommendations(table_name)
                
                return {
                    "status": "completed",
                    "table_recommendations": table_recommendations,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }