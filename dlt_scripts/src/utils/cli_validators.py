#!/usr/bin/env python3
"""
CLI argument validation utilities.
"""

import argparse
from typing import List, Tuple, Optional
from datetime import datetime

from ..pipeline.config_models import ConfigurationModel, BatchSelection


def validate_table_names(table_names: List[str], config: ConfigurationModel) -> None:
    """
    Validate that requested table names exist in configuration.
    
    Args:
        table_names: List of table names to validate
        config: Pipeline configuration
        
    Raises:
        ValueError: If any table names are invalid
    """
    available_tables = set(config.tables.keys())
    invalid_tables = set(table_names) - available_tables
    
    if invalid_tables:
        raise ValueError(
            f"Invalid table names: {', '.join(invalid_tables)}. "
            f"Available tables: {', '.join(sorted(available_tables))}"
        )
    
    # Check if tables are enabled
    disabled_tables = [
        name for name in table_names 
        if not config.tables[name].enabled
    ]
    
    if disabled_tables:
        print(f"⚠️  Warning: The following tables are disabled: {', '.join(disabled_tables)}")


def validate_batch_selection(args: argparse.Namespace) -> Tuple[Optional[BatchSelection], Optional[str], Optional[datetime], Optional[datetime]]:
    """
    Validate and parse batch selection arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (batch_selection, specific_batch, start_date, end_date)
        
    Raises:
        ValueError: If batch selection arguments are invalid
    """
    batch_selection = None
    specific_batch = None
    start_date = None
    end_date = None
    
    # Check for batch argument
    if hasattr(args, 'batch') and args.batch:
        if args.batch == "latest":
            batch_selection = BatchSelection.LATEST
        else:
            # Validate batch ID format (YYYYMMDD_HHMMSS)
            if not _is_valid_batch_id(args.batch):
                raise ValueError(
                    f"Invalid batch ID format: {args.batch}. "
                    "Expected format: YYYYMMDD_HHMMSS (e.g., 20250817_143000)"
                )
            batch_selection = BatchSelection.SPECIFIC
            specific_batch = args.batch
    
    # Check for date range argument
    if hasattr(args, 'date_range') and args.date_range:
        if batch_selection is not None:
            raise ValueError("Cannot specify both --batch and --date-range")
        
        start_date, end_date = validate_date_range(args.date_range)
        batch_selection = BatchSelection.DATE_RANGE
    
    # Default to latest if no selection specified for load operations
    if (hasattr(args, 'command') and args.command == 'load' and 
        batch_selection is None):
        batch_selection = BatchSelection.LATEST
    
    return batch_selection, specific_batch, start_date, end_date


def validate_date_range(date_range_str: str) -> Tuple[datetime, datetime]:
    """
    Validate and parse date range string.
    
    Args:
        date_range_str: Date range in format "YYYYMMDD-YYYYMMDD"
        
    Returns:
        Tuple of (start_date, end_date)
        
    Raises:
        ValueError: If date range format is invalid
    """
    try:
        if '-' not in date_range_str:
            raise ValueError("Date range must contain '-' separator")
        
        start_str, end_str = date_range_str.split('-', 1)
        
        # Parse dates
        start_date = datetime.strptime(start_str.strip(), "%Y%m%d")
        end_date = datetime.strptime(end_str.strip(), "%Y%m%d")
        
        # Validate date order
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        # Validate date range is not too large (max 365 days)
        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")
        
        return start_date, end_date
        
    except ValueError as e:
        if "time data" in str(e):
            raise ValueError(
                f"Invalid date format in range: {date_range_str}. "
                "Expected format: YYYYMMDD-YYYYMMDD (e.g., 20250815-20250817)"
            )
        else:
            raise


def validate_retention_period(retention_str: str) -> int:
    """
    Validate and parse retention period string.
    
    Args:
        retention_str: Retention period like "30d", "7d", or "90"
        
    Returns:
        Number of days
        
    Raises:
        ValueError: If retention format is invalid
    """
    try:
        if retention_str.endswith('d'):
            days = int(retention_str[:-1])
        else:
            days = int(retention_str)
        
        if days <= 0:
            raise ValueError("Retention period must be positive")
        
        if days > 3650:  # 10 years max
            raise ValueError("Retention period cannot exceed 3650 days (10 years)")
        
        return days
        
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(
                f"Invalid retention format: {retention_str}. "
                "Expected format: number followed by optional 'd' (e.g., 30d, 90)"
            )
        else:
            raise


def validate_environment_name(environment: str) -> None:
    """
    Validate environment name.
    
    Args:
        environment: Environment name to validate
        
    Raises:
        ValueError: If environment name is invalid
    """
    # Allow alphanumeric, underscore, hyphen
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', environment):
        raise ValueError(
            f"Invalid environment name: {environment}. "
            "Environment names must contain only letters, numbers, underscores, and hyphens"
        )
    
    # Check length
    if len(environment) > 50:
        raise ValueError("Environment name cannot exceed 50 characters")


def validate_output_path(output_path: str) -> None:
    """
    Validate output file path.
    
    Args:
        output_path: Output file path to validate
        
    Raises:
        ValueError: If output path is invalid
    """
    from pathlib import Path
    
    try:
        path = Path(output_path)
        
        # Check if parent directory exists or can be created
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create output directory: {e}")
        
        # Check if we can write to the location
        if path.exists() and not path.is_file():
            raise ValueError(f"Output path exists but is not a file: {output_path}")
        
        # Recommend JSON extension
        if not output_path.endswith('.json'):
            print(f"💡 Tip: Consider using .json extension for output file")
        
    except Exception as e:
        raise ValueError(f"Invalid output path: {e}")


def _is_valid_batch_id(batch_id: str) -> bool:
    """
    Check if batch ID follows the expected format.
    
    Args:
        batch_id: Batch ID to validate
        
    Returns:
        True if valid format
    """
    import re
    # Expected format: YYYYMMDD_HHMMSS
    pattern = r'^\d{8}_\d{6}$'
    
    if not re.match(pattern, batch_id):
        return False
    
    # Validate the date and time components
    try:
        datetime.strptime(batch_id, "%Y%m%d_%H%M%S")
        return True
    except ValueError:
        return False


def validate_pipeline_mode(mode: str) -> None:
    """
    Validate pipeline mode.
    
    Args:
        mode: Pipeline mode to validate
        
    Raises:
        ValueError: If mode is invalid
    """
    valid_modes = {"direct", "extract-only", "load-only", "two-stage"}
    
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid pipeline mode: {mode}. "
            f"Valid modes: {', '.join(sorted(valid_modes))}"
        )


def validate_archive_action(action: str) -> None:
    """
    Validate archive action.
    
    Args:
        action: Archive action to validate
        
    Raises:
        ValueError: If action is invalid
    """
    valid_actions = {"list", "stats", "info", "cleanup"}
    
    if action not in valid_actions:
        raise ValueError(
            f"Invalid archive action: {action}. "
            f"Valid actions: {', '.join(sorted(valid_actions))}"
        )


def validate_positive_integer(value: str, name: str, max_value: Optional[int] = None) -> int:
    """
    Validate that a string represents a positive integer.
    
    Args:
        value: String value to validate
        name: Name of the parameter for error messages
        max_value: Maximum allowed value
        
    Returns:
        Validated integer value
        
    Raises:
        ValueError: If value is invalid
    """
    try:
        int_value = int(value)
        
        if int_value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        
        if max_value and int_value > max_value:
            raise ValueError(f"{name} cannot exceed {max_value}")
        
        return int_value
        
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid {name}: must be a positive integer")
        else:
            raise