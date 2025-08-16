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
from src.utils.logging_setup import setup_logging


def run_pipeline_command(args: argparse.Namespace) -> int:
    """
    Run the data migration pipeline.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        environment = args.environment or get_environment_from_env_var()
        config_dir = Path(args.config_dir) if args.config_dir else None
        
        print(f"Loading configuration: {args.config}")
        if environment:
            print(f"Environment: {environment}")
        
        config = load_config(args.config, environment, config_dir)
        
        # Initialize pipeline runner
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
        
        return 0 if results['status'] == 'success' else 1
        
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
        description="Configuration-driven data migration pipeline using DLT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                          # Run with default config
  %(prog)s run -e dev                   # Run with dev environment
  %(prog)s run --tables Users Posts     # Run specific tables only
  %(prog)s validate                     # Validate configuration
  %(prog)s stats                        # Show pipeline statistics
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
        '--tables', '-t',
        nargs='+',
        help='Specific tables to process'
    )
    run_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show pipeline statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to 'run' if no command specified
    if not args.command:
        args.command = 'run'
    
    # Execute command
    try:
        if args.command == 'run':
            return run_pipeline_command(args)
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