#!/usr/bin/env python3

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from ..pipeline.config_models import LoggingConfig


def setup_logging(config: LoggingConfig, logger_name: str = "pipeline") -> logging.Logger:
    """
    Configure logging based on the logging configuration.
    
    Args:
        config: Logging configuration
        logger_name: Name of the logger to create
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, config.level))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler (always present)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if file path is specified)
    if config.file_path:
        file_path = Path(config.file_path)
        
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to manage file size
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent logging from propagating to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"pipeline.{name}")


def log_configuration_summary(logger: logging.Logger, config) -> None:
    """
    Log a summary of the pipeline configuration.
    
    Args:
        logger: Logger instance
        config: Pipeline configuration
    """
    logger.info("=== Pipeline Configuration Summary ===")
    logger.info(f"Pipeline Name: {config.pipeline.name}")
    logger.info(f"Dataset Name: {config.pipeline.dataset_name}")
    logger.info(f"Backend: {config.pipeline.backend}")
    logger.info(f"Chunk Size: {config.pipeline.chunk_size:,}")
    logger.info(f"File Format: {config.pipeline.loader_file_format}")
    
    # Log enabled tables
    enabled_tables = [name for name, table in config.tables.items() if table.enabled]
    logger.info(f"Enabled Tables ({len(enabled_tables)}): {', '.join(enabled_tables)}")
    
    # Log incremental tables
    incremental_tables = [
        name for name, table in config.tables.items() 
        if table.enabled and table.incremental.enabled
    ]
    if incremental_tables:
        logger.info(f"Incremental Tables ({len(incremental_tables)}): {', '.join(incremental_tables)}")
    
    logger.info(f"Verification Enabled: {config.verification.enabled}")
    logger.info("=" * 40)


def log_table_processing_start(logger: logging.Logger, table_name: str, table_config) -> None:
    """
    Log the start of table processing.
    
    Args:
        logger: Logger instance
        table_name: Name of the table being processed
        table_config: Table configuration
    """
    logger.info(f"Starting processing for table: {table_name}")
    logger.info(f"  Source: {table_config.source_table}")
    logger.info(f"  Destination: {table_config.destination_table}")
    logger.info(f"  Disposition: {table_config.disposition}")
    
    if table_config.incremental.enabled:
        logger.info(f"  Incremental: {table_config.incremental.strategy}")
        logger.info(f"  Watermark Column: {table_config.incremental.watermark_column}")
        logger.info(f"  Initial Value: {table_config.incremental.initial_value}")
    else:
        logger.info("  Incremental: Disabled")
    
    if table_config.where_clause:
        logger.info(f"  Filter: {table_config.where_clause}")


def log_table_processing_complete(
    logger: logging.Logger, 
    table_name: str, 
    duration: float, 
    row_count: Optional[int] = None
) -> None:
    """
    Log the completion of table processing.
    
    Args:
        logger: Logger instance
        table_name: Name of the table that was processed
        duration: Processing duration in seconds
        row_count: Number of rows processed (if available)
    """
    logger.info(f"Completed processing for table: {table_name}")
    logger.info(f"  Duration: {duration:.2f} seconds")
    
    if row_count is not None:
        logger.info(f"  Rows processed: {row_count:,}")
        
        if duration > 0:
            rate = row_count / duration
            logger.info(f"  Processing rate: {rate:.0f} rows/second")


def log_pipeline_start(logger: logging.Logger) -> None:
    """
    Log the start of the pipeline.
    
    Args:
        logger: Logger instance
    """
    logger.info("🚀 Starting data migration pipeline")


def log_pipeline_complete(logger: logging.Logger, total_duration: float, table_count: int) -> None:
    """
    Log the completion of the pipeline.
    
    Args:
        logger: Logger instance
        total_duration: Total pipeline duration in seconds
        table_count: Number of tables processed
    """
    logger.info("✅ Data migration pipeline completed successfully")
    logger.info(f"  Total duration: {total_duration:.2f} seconds")
    logger.info(f"  Tables processed: {table_count}")


def log_pipeline_error(logger: logging.Logger, error: Exception, table_name: Optional[str] = None) -> None:
    """
    Log a pipeline error.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        table_name: Name of the table being processed when error occurred (if applicable)
    """
    error_msg = "❌ Pipeline error occurred"
    if table_name:
        error_msg += f" while processing table '{table_name}'"
    
    logger.error(error_msg)
    logger.error(f"  Error type: {type(error).__name__}")
    logger.error(f"  Error message: {str(error)}")
    
    # Log full traceback in debug mode
    logger.debug("Full traceback:", exc_info=True)


def log_verification_start(logger: logging.Logger, tables: list[str]) -> None:
    """
    Log the start of verification process.
    
    Args:
        logger: Logger instance
        tables: List of tables to verify
    """
    logger.info("📊 Starting data verification")
    logger.info(f"  Tables to verify: {', '.join(tables)}")


def log_verification_result(
    logger: logging.Logger, 
    table_name: str, 
    source_count: int, 
    dest_count: int, 
    tolerance: int
) -> None:
    """
    Log verification result for a table.
    
    Args:
        logger: Logger instance
        table_name: Name of the table verified
        source_count: Row count in source
        dest_count: Row count in destination
        tolerance: Allowed difference
    """
    difference = abs(source_count - dest_count)
    status = "✅" if difference <= tolerance else "⚠️"
    
    logger.info(f"{status} {table_name}: Source={source_count:,}, Destination={dest_count:,}")
    
    if difference > 0:
        logger.info(f"  Difference: {difference:,} rows")
        
        if difference > tolerance:
            logger.warning(f"  Difference exceeds tolerance of {tolerance}")


def log_verification_complete(logger: logging.Logger, passed: int, failed: int) -> None:
    """
    Log the completion of verification process.
    
    Args:
        logger: Logger instance
        passed: Number of tables that passed verification
        failed: Number of tables that failed verification
    """
    if failed == 0:
        logger.info("✅ All verification checks passed")
    else:
        logger.warning(f"⚠️ Verification completed: {passed} passed, {failed} failed")
    
    logger.info(f"  Total tables verified: {passed + failed}")