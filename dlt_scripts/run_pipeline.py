#!/usr/bin/env python3

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline.config_loader import load_config, ConfigurationError, get_environment_from_env_var
from src.pipeline.pipeline_runner import PipelineRunner
from src.pipeline.two_stage_runner import TwoStagePipelineRunner
from src.utils.logging_setup import setup_logging
from src.utils.cli_commands import (
    extract_command, load_command, archive_list_command, archive_stats_command,
    archive_info_command, archive_cleanup_command, run_two_stage_command
)
from src.utils.cli_validators import (
    validate_pipeline_mode, validate_archive_action, validate_environment_name,
    validate_output_path, validate_retention_period, validate_positive_integer
)


def run_pipeline_command(args: argparse.Namespace) -> int:
    """
    Run the data migration pipeline.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # If mode is specified, use the two-stage runner command
    if hasattr(args, 'mode') and args.mode:
        return run_two_stage_command(args)
    
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        print(f"Loading configuration: {args.config}")
        if environment:
            print(f"Environment: {environment}")
        
        config = load_config(args.config, environment, config_dir)
        
        # Check if config specifies non-direct mode, use TwoStageRunner
        if config.pipeline.pipeline_mode.value != "direct":
            print(f"Configuration specifies {config.pipeline.pipeline_mode.value} mode, using TwoStageRunner")
            runner = TwoStagePipelineRunner(config)
            
            results = runner.run(tables_to_process=args.tables)
            
            # Format results for two-stage modes
            from src.utils.cli_formatters import format_pipeline_summary
            format_pipeline_summary(results)
            
        else:
            # Use traditional pipeline runner for direct mode
            runner = PipelineRunner(config)
            
            # Run pipeline
            tables_to_process = args.tables if args.tables else None
            if tables_to_process:
                print(f"Processing specific tables: {', '.join(tables_to_process)}")
            
            results = runner.run(tables_to_process)
            
            # Print results summary
            print(f"\n{'='*60}")
            print("PIPELINE EXECUTION SUMMARY")
            print(f"{'='*60}")
            print(f"Status: {results['status'].upper()}")
            print(f"Duration: {results['duration_seconds']:.2f} seconds")
            
            if results['status'] == 'success':
                print(f"Tables processed: {len(results['tables_processed'])}")
                
                # Show per-table results
                for table_name in results['tables_processed']:
                    table_result = results['table_results'][table_name]
                    status = "✅" if table_result['status'] == 'success' else "❌"
                    duration = table_result['duration_seconds']
                    print(f"  {status} {table_name}: {duration:.2f}s")
                
                # Show verification results if available
                if results.get('verification_results') and results['verification_results'].get('verification_enabled'):
                    verification = results['verification_results']
                    print(f"\nVerification: {verification['passed_checks']}/{verification['total_checks']} checks passed")
            else:
                print(f"Error: {results.get('error', 'Unknown error')}")
                if results.get('tables_processed'):
                    print(f"Tables processed before failure: {', '.join(results['tables_processed'])}")
        
        # Save results to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {output_path}")
        
        return 0 if results.get('status') in ['success', 'completed'] else 1
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n❌ Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def validate_config_command(args: argparse.Namespace) -> int:
    """
    Validate configuration without running the pipeline.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        from src.utils.cli_utils import validate_config_command
        return validate_config_command(args)
    except ImportError:
        # Fallback validation
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        config = load_config(args.config, environment, config_dir)
        print("✅ Configuration is valid!")
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return 1


def show_statistics_command(args: argparse.Namespace) -> int:
    """
    Show pipeline statistics and table information.
    
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
        
        # Initialize pipeline runner (but don't run)
        runner = PipelineRunner(config)
        
        print(f"{'='*60}")
        print("PIPELINE CONFIGURATION OVERVIEW")
        print(f"{'='*60}")
        
        print(f"Pipeline Name: {config.pipeline.name}")
        print(f"Dataset Name: {config.pipeline.dataset_name}")
        print(f"Backend: {config.pipeline.backend}")
        print(f"Chunk Size: {config.pipeline.chunk_size:,}")
        print(f"File Format: {config.pipeline.loader_file_format}")
        
        # Show table configurations
        enabled_tables = {name: table for name, table in config.tables.items() if table.enabled}
        print(f"\nEnabled Tables ({len(enabled_tables)}):")
        
        for table_name, table_config in enabled_tables.items():
            print(f"\n  📋 {table_name}")
            print(f"     Source: {table_config.source_table}")
            print(f"     Destination: {table_config.destination_table}")
            print(f"     Disposition: {table_config.disposition}")
            
            if table_config.incremental.enabled:
                print(f"     Incremental: {table_config.incremental.strategy}")
                print(f"     Watermark: {table_config.incremental.watermark_column}")
                print(f"     Initial Value: {table_config.incremental.initial_value}")
            else:
                print("     Incremental: Disabled")
            
            if table_config.where_clause:
                print(f"     Filter: {table_config.where_clause}")
            
            if table_config.primary_key:
                print(f"     Primary Key: {', '.join(table_config.primary_key)}")
            
            # Try to estimate table size
            try:
                processor = runner.table_processor
                row_count = processor.estimate_table_size(table_name, table_config)
                if row_count is not None:
                    print(f"     Estimated Rows: {row_count:,}")
            except Exception:
                pass  # Skip if estimation fails
        
        # Show disabled tables
        disabled_tables = [name for name, table in config.tables.items() if not table.enabled]
        if disabled_tables:
            print(f"\nDisabled Tables ({len(disabled_tables)}): {', '.join(disabled_tables)}")
        
        # Show verification settings
        print(f"\nVerification Settings:")
        print(f"  Enabled: {config.verification.enabled}")
        if config.verification.enabled:
            print(f"  Tolerance: {config.verification.tolerance}")
            
            verification_tables = config.verification.tables or list(enabled_tables.keys())
            print(f"  Tables to verify: {', '.join(verification_tables)}")
            
            if config.verification.custom_checks:
                print(f"  Custom checks: {len(config.verification.custom_checks)}")
        
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def main():
    """Main entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="Configuration-driven data migration pipeline using DLT with two-stage support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                                    # Run with default config
  %(prog)s run --mode two-stage                   # Run in two-stage mode
  %(prog)s run -e dev --tables Users Posts        # Run specific tables with dev environment
  %(prog)s extract --tables Users                 # Extract specific tables only
  %(prog)s load --batch latest                    # Load latest batches
  %(prog)s load --batch 20250817_143000          # Load specific batch
  %(prog)s load --date-range 20250815-20250817   # Load batches from date range
  %(prog)s archive list --last 10                # List last 10 batches
  %(prog)s archive stats                          # Show archive statistics
  %(prog)s archive cleanup --older-than 30d      # Clean batches older than 30 days
  %(prog)s validate --mode two-stage              # Validate two-stage configuration
  %(prog)s stats                                  # Show pipeline statistics
        """
    )
    
    # Global arguments
    parser.add_argument(
        '--config', '-c',
        default='pipeline_config.yaml',
        help='Configuration file (default: pipeline_config.yaml)'
    )
    parser.add_argument(
        '--config-dir',
        help='Configuration directory (default: config/)'
    )
    parser.add_argument(
        '--environment', '-e',
        help='Environment configuration (dev, staging, prod, etc.)'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the data migration pipeline')
    run_parser.add_argument(
        '--mode',
        choices=['direct', 'extract-only', 'load-only', 'two-stage'],
        help='Pipeline execution mode'
    )
    run_parser.add_argument(
        '--tables', '-t',
        nargs='+',
        help='Specific tables to process'
    )
    run_parser.add_argument(
        '--batch',
        help='Batch selection for load operations (latest or specific batch ID)'
    )
    run_parser.add_argument(
        '--date-range',
        help='Date range for batch selection (YYYYMMDD-YYYYMMDD)'
    )
    run_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract tables to archive')
    extract_parser.add_argument(
        '--tables', '-t',
        nargs='+',
        help='Specific tables to extract (default: all enabled tables)'
    )
    extract_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load tables from archive')
    load_parser.add_argument(
        '--tables', '-t',
        nargs='+',
        help='Specific tables to load (default: all available tables)'
    )
    load_parser.add_argument(
        '--batch',
        default='latest',
        help='Batch selection: latest, specific batch ID (default: latest)'
    )
    load_parser.add_argument(
        '--date-range',
        help='Date range for batch selection (YYYYMMDD-YYYYMMDD)'
    )
    load_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Archive management operations')
    archive_subparsers = archive_parser.add_subparsers(dest='archive_action', help='Archive actions')
    
    # Archive list
    list_parser = archive_subparsers.add_parser('list', help='List available batches')
    list_parser.add_argument(
        '--table',
        help='Filter by specific table'
    )
    list_parser.add_argument(
        '--last',
        type=int,
        help='Show last N batches (default: 20)'
    )
    
    # Archive stats
    stats_archive_parser = archive_subparsers.add_parser('stats', help='Show archive statistics')
    
    # Archive info
    info_parser = archive_subparsers.add_parser('info', help='Show batch information')
    info_parser.add_argument(
        '--batch',
        required=True,
        help='Batch ID to show information for'
    )
    
    # Archive cleanup
    cleanup_parser = archive_subparsers.add_parser('cleanup', help='Clean up old batches')
    cleanup_parser.add_argument(
        '--older-than',
        help='Delete batches older than specified period (e.g., 30d, 90)'
    )
    cleanup_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete files (default is dry-run)'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument(
        '--mode',
        choices=['direct', 'extract-only', 'load-only', 'two-stage'],
        help='Validate for specific pipeline mode'
    )
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show pipeline statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to 'run' if no command specified
    if not args.command:
        args.command = 'run'
    
    # Validate arguments
    try:
        if hasattr(args, 'environment') and args.environment:
            validate_environment_name(args.environment)
        
        if hasattr(args, 'mode') and args.mode:
            validate_pipeline_mode(args.mode)
        
        if hasattr(args, 'output') and args.output:
            validate_output_path(args.output)
        
        if hasattr(args, 'older_than') and args.older_than:
            validate_retention_period(args.older_than)
        
        if hasattr(args, 'last') and args.last:
            validate_positive_integer(str(args.last), "last", 1000)
        
        if args.command == 'archive' and hasattr(args, 'archive_action') and args.archive_action:
            validate_archive_action(args.archive_action)
        
    except ValueError as e:
        print(f"❌ Argument validation error: {e}")
        return 1
    
    # Execute command
    try:
        if args.command == 'run':
            return run_pipeline_command(args)
        elif args.command == 'extract':
            return extract_command(args)
        elif args.command == 'load':
            return load_command(args)
        elif args.command == 'archive':
            if not hasattr(args, 'archive_action') or not args.archive_action:
                archive_parser.print_help()
                return 1
            elif args.archive_action == 'list':
                return archive_list_command(args)
            elif args.archive_action == 'stats':
                return archive_stats_command(args)
            elif args.archive_action == 'info':
                return archive_info_command(args)
            elif args.archive_action == 'cleanup':
                return archive_cleanup_command(args)
            else:
                archive_parser.print_help()
                return 1
        elif args.command == 'validate':
            return validate_config_command(args)
        elif args.command == 'stats':
            return show_statistics_command(args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1


if __name__ == '__main__':
    sys.exit(main())