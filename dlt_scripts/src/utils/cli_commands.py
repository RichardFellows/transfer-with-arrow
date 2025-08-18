#!/usr/bin/env python3
"""
CLI command implementations for two-stage pipeline operations.
"""

import argparse
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from .cli_validators import validate_batch_selection, validate_date_range, validate_table_names
from .cli_formatters import format_extraction_results, format_load_results, format_archive_status
from ..pipeline.config_loader import load_config, get_environment_from_env_var
from ..pipeline.two_stage_runner import TwoStagePipelineRunner
from ..pipeline.config_models import BatchSelection, PipelineMode


def extract_command(args: argparse.Namespace) -> int:
    """
    Execute extract-only operation.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        print(f"🚀 Starting extraction operation")
        if environment:
            print(f"Environment: {environment}")
        
        config = load_config(args.config, environment, config_dir)
        
        # Validate table names if provided
        if args.tables:
            validate_table_names(args.tables, config)
        
        # Initialize two-stage runner
        runner = TwoStagePipelineRunner(config)
        
        # Prepare custom metadata
        custom_metadata = {
            "extraction_mode": "cli_extract",
            "requested_tables": args.tables,
            "cli_user": "pipeline_operator"
        }
        
        # Execute extraction
        print(f"📦 Extracting tables to archive...")
        if args.tables:
            print(f"Specific tables: {', '.join(args.tables)}")
        else:
            print("All enabled tables")
        
        if args.tables:
            # For specific tables, we need to call extract_table for each one
            results = {"phase": "extract", "status": "completed", "tables": {}, "timestamp": datetime.now().isoformat()}
            for table_name in args.tables:
                try:
                    table_result = runner.extract_processor.extract_table(table_name, custom_metadata)
                    results["tables"][table_name] = table_result
                except Exception as e:
                    results["tables"][table_name] = {"status": "failed", "error": str(e)}
                    results["status"] = "failed"
        else:
            # For all tables, use extract_all_tables
            results = runner.extract_processor.extract_all_tables(custom_metadata)
            results = {
                "phase": "extract",
                "status": "completed",
                "tables": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # Format and display results
        format_extraction_results(results)
        
        # Save results to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Results saved to: {output_path}")
        
        # Check if all extractions were successful
        successful_tables = [
            table_name for table_name, result in results["tables"].items()
            if result.get("status") == "completed"
        ]
        
        if len(successful_tables) == len(results["tables"]):
            print(f"\n✅ All extractions completed successfully")
            return 0
        else:
            failed_count = len(results["tables"]) - len(successful_tables)
            print(f"\n⚠️  {failed_count} extraction(s) failed")
            return 1
        
    except Exception as e:
        print(f"❌ Extract operation failed: {e}")
        return 1


def load_command(args: argparse.Namespace) -> int:
    """
    Execute load-only operation.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        print(f"🚀 Starting load operation")
        if environment:
            print(f"Environment: {environment}")
        
        config = load_config(args.config, environment, config_dir)
        
        # Validate arguments
        if args.tables:
            validate_table_names(args.tables, config)
        
        batch_selection, specific_batch, start_date, end_date = validate_batch_selection(args)
        
        # Initialize two-stage runner
        runner = TwoStagePipelineRunner(config)
        
        # Prepare custom metadata
        custom_metadata = {
            "load_mode": "cli_load",
            "batch_selection": batch_selection.value if batch_selection else None,
            "specific_batch": specific_batch,
            "date_range": f"{start_date}_{end_date}" if start_date and end_date else None,
            "cli_user": "pipeline_operator"
        }
        
        # Execute load
        print(f"🚚 Loading data from archive...")
        if args.tables:
            print(f"Specific tables: {', '.join(args.tables)}")
        else:
            print("All tables with available batches")
        
        if batch_selection:
            print(f"Batch selection: {batch_selection.value}")
            if specific_batch:
                print(f"Specific batch: {specific_batch}")
            elif start_date and end_date:
                print(f"Date range: {start_date} to {end_date}")
        
        results = runner.load_tables(
            tables_to_process=args.tables,
            batch_selection=batch_selection,
            specific_batch=specific_batch,
            start_date=start_date,
            end_date=end_date,
            custom_metadata=custom_metadata
        )
        
        # Format and display results
        format_load_results(results)
        
        # Save results to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Results saved to: {output_path}")
        
        # Check if all loads were successful
        successful_tables = [
            table_name for table_name, result in results["tables"].items()
            if result.get("status") == "completed"
        ]
        
        if len(successful_tables) == len(results["tables"]):
            print(f"\n✅ All loads completed successfully")
            return 0
        else:
            failed_count = len(results["tables"]) - len(successful_tables)
            print(f"\n⚠️  {failed_count} load(s) failed")
            return 1
        
    except Exception as e:
        print(f"❌ Load operation failed: {e}")
        return 1


def archive_list_command(args: argparse.Namespace) -> int:
    """
    List available batches in archive.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        config = load_config(args.config, environment, config_dir)
        runner = TwoStagePipelineRunner(config)
        
        if not runner.archive_manager:
            print("❌ Archive not available for this pipeline mode")
            return 1
        
        print(f"📋 Available Batches")
        print(f"{'='*60}")
        
        # Get available batches
        if args.table:
            validate_table_names([args.table], config)
            batches = runner.archive_manager.list_available_batches(
                table_name=args.table,
                last_n=args.last or 20
            )
            print(f"Table: {args.table}")
        else:
            batches = runner.archive_manager.list_available_batches(
                last_n=args.last or 20
            )
            print("All tables")
        
        if not batches:
            print("No batches found")
            return 0
        
        # Display batches
        for batch in batches:
            status_icon = "✅" if batch.status.value == "completed" else "⚠️"
            print(f"{status_icon} {batch.batch_id}")
            print(f"    Table: {batch.table_name}")
            print(f"    Created: {batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Status: {batch.status.value}")
            print(f"    Rows: {batch.row_count:,}")
            if batch.file_size_mb:
                print(f"    Size: {batch.file_size_mb:.2f} MB")
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Archive list failed: {e}")
        return 1


def archive_stats_command(args: argparse.Namespace) -> int:
    """
    Show archive statistics.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        config = load_config(args.config, environment, config_dir)
        runner = TwoStagePipelineRunner(config)
        
        # Get archive status
        status = runner.get_archive_status()
        
        # Format and display status
        format_archive_status(status)
        
        return 0 if status.get("status") != "error" else 1
        
    except Exception as e:
        print(f"❌ Archive stats failed: {e}")
        return 1


def archive_info_command(args: argparse.Namespace) -> int:
    """
    Show detailed information about a specific batch.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        config = load_config(args.config, environment, config_dir)
        runner = TwoStagePipelineRunner(config)
        
        if not runner.archive_manager:
            print("❌ Archive not available for this pipeline mode")
            return 1
        
        # Get batch information
        batch = runner.archive_manager.get_batch_info(args.batch)
        
        if not batch:
            print(f"❌ Batch not found: {args.batch}")
            return 1
        
        print(f"📦 Batch Information: {args.batch}")
        print(f"{'='*60}")
        print(f"Table: {batch.table_name}")
        print(f"Batch ID: {batch.batch_id}")
        print(f"Created: {batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Status: {batch.status.value}")
        print(f"Row Count: {batch.row_count:,}")
        
        if batch.file_size_mb:
            print(f"File Size: {batch.file_size_mb:.2f} MB")
        
        if batch.compression:
            print(f"Compression: {batch.compression}")
        
        if batch.schema_version:
            print(f"Schema Version: {batch.schema_version}")
        
        # Show file paths
        if hasattr(batch, 'file_paths') and batch.file_paths:
            print(f"\nFiles ({len(batch.file_paths)}):")
            for file_path in batch.file_paths:
                print(f"  📄 {file_path}")
        
        # Show metadata if available
        if batch.metadata:
            print(f"\nMetadata:")
            for key, value in batch.metadata.items():
                print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Archive info failed: {e}")
        return 1


def archive_cleanup_command(args: argparse.Namespace) -> int:
    """
    Clean up old archive batches.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        config = load_config(args.config, environment, config_dir)
        runner = TwoStagePipelineRunner(config)
        
        # Parse older_than argument
        older_than_days = None
        if args.older_than:
            if args.older_than.endswith('d'):
                older_than_days = int(args.older_than[:-1])
            else:
                older_than_days = int(args.older_than)
        
        dry_run = not args.confirm
        
        print(f"🧹 Archive Cleanup")
        print(f"{'='*60}")
        if older_than_days:
            print(f"Cleaning batches older than {older_than_days} days")
        else:
            print("Using default retention policy")
        
        if dry_run:
            print("DRY RUN MODE - No files will be deleted")
        else:
            print("⚠️  LIVE MODE - Files will be permanently deleted")
        
        # Execute cleanup
        results = runner.cleanup_archive(
            older_than_days=older_than_days,
            dry_run=dry_run
        )
        
        if results.get("status") == "archive_disabled":
            print("❌ Archive not available for this pipeline mode")
            return 1
        
        cleanup_results = results.get("cleanup_results", {})
        
        print(f"\nCleanup Results:")
        print(f"  Batches to delete: {cleanup_results.get('batches_to_delete', 0)}")
        print(f"  Space to free: {cleanup_results.get('total_size_to_free_mb', 0):.2f} MB")
        
        if cleanup_results.get('deleted_batches'):
            print(f"\nDeleted Batches:")
            for batch_id in cleanup_results['deleted_batches']:
                print(f"  🗑️  {batch_id}")
        
        if dry_run and cleanup_results.get('batches_to_delete', 0) > 0:
            print(f"\n💡 To actually delete these batches, run with --confirm")
        
        return 0 if results.get("status") == "completed" else 1
        
    except Exception as e:
        print(f"❌ Archive cleanup failed: {e}")
        return 1


def run_two_stage_command(args: argparse.Namespace) -> int:
    """
    Execute pipeline with two-stage mode support.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        print(f"🚀 Starting pipeline execution")
        if args.mode:
            print(f"Mode: {args.mode}")
        if environment:
            print(f"Environment: {environment}")
        
        config = load_config(args.config, environment, config_dir)
        
        # Override pipeline mode if specified
        if args.mode:
            if args.mode == "direct":
                config.pipeline.pipeline_mode = PipelineMode.DIRECT
            elif args.mode == "extract-only":
                config.pipeline.pipeline_mode = PipelineMode.EXTRACT_ONLY
            elif args.mode == "load-only":
                config.pipeline.pipeline_mode = PipelineMode.LOAD_ONLY
            elif args.mode == "two-stage":
                config.pipeline.pipeline_mode = PipelineMode.TWO_STAGE
            else:
                print(f"❌ Invalid mode: {args.mode}")
                return 1
        
        # Validate table names if provided
        if args.tables:
            validate_table_names(args.tables, config)
        
        # Parse batch selection for load operations
        batch_selection = None
        specific_batch = None
        start_date = None
        end_date = None
        
        if hasattr(args, 'batch') and args.batch:
            if args.batch == "latest":
                batch_selection = BatchSelection.LATEST
            else:
                batch_selection = BatchSelection.SPECIFIC
                specific_batch = args.batch
        
        if hasattr(args, 'date_range') and args.date_range:
            start_date, end_date = validate_date_range(args.date_range)
            batch_selection = BatchSelection.DATE_RANGE
        
        # Initialize runner
        runner = TwoStagePipelineRunner(config)
        
        # Prepare custom metadata
        custom_metadata = {
            "execution_mode": "cli_run",
            "requested_mode": args.mode,
            "requested_tables": args.tables,
            "cli_user": "pipeline_operator"
        }
        
        # Execute pipeline
        print(f"▶️  Executing {config.pipeline.pipeline_mode.value} pipeline...")
        if args.tables:
            print(f"Specific tables: {', '.join(args.tables)}")
        
        results = runner.run(
            tables_to_process=args.tables,
            batch_selection=batch_selection,
            specific_batch=specific_batch,
            start_date=start_date,
            end_date=end_date,
            custom_metadata=custom_metadata
        )
        
        # Format and display results
        print(f"\n{'='*60}")
        print("PIPELINE EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Mode: {results['mode'].upper()}")
        print(f"Status: {results['status'].upper()}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"Started: {results['started_at']}")
        print(f"Completed: {results['completed_at']}")
        
        # Show phase-specific results
        if results.get("extract_results"):
            print(f"\n📦 Extract Phase:")
            extract_tables = results["extract_results"].get("tables", {})
            for table_name, result in extract_tables.items():
                status = "✅" if result.get("status") == "completed" else "❌"
                print(f"  {status} {table_name}")
        
        if results.get("load_results"):
            print(f"\n🚚 Load Phase:")
            load_tables = results["load_results"].get("tables", {})
            for table_name, result in load_tables.items():
                status = "✅" if result.get("status") == "completed" else "❌"
                print(f"  {status} {table_name}")
        
        if results.get("results"):  # Direct mode results
            print(f"\n📊 Direct Mode Results:")
            for table_name, result in results["results"].items():
                status = "✅" if result.get("status") == "completed" else "❌"
                print(f"  {status} {table_name}")
        
        # Save results to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Results saved to: {output_path}")
        
        return 0 if results["status"] == "completed" else 1
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        return 1