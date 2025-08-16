#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path
from typing import Optional

from ..pipeline.config_loader import ConfigLoader, ConfigurationError
from ..pipeline.config_models import ConfigurationModel


def validate_config_command(args: argparse.Namespace) -> int:
    """
    Validate configuration file command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_dir = Path(args.config_dir) if args.config_dir else None
        loader = ConfigLoader(config_dir)
        
        print(f"Validating configuration file: {args.config_file}")
        
        if args.environment:
            print(f"Using environment: {args.environment}")
        
        # Validate configuration
        config = loader.load_configuration(args.config_file, args.environment)
        
        print("✅ Configuration is valid!")
        
        # Print summary
        print(f"\nConfiguration Summary:")
        print(f"  Pipeline Name: {config.pipeline.name}")
        print(f"  Dataset Name: {config.pipeline.dataset_name}")
        print(f"  Backend: {config.pipeline.backend}")
        print(f"  Chunk Size: {config.pipeline.chunk_size:,}")
        
        enabled_tables = [name for name, table in config.tables.items() if table.enabled]
        print(f"  Enabled Tables ({len(enabled_tables)}): {', '.join(enabled_tables)}")
        
        incremental_tables = [
            name for name, table in config.tables.items() 
            if table.enabled and table.incremental.enabled
        ]
        if incremental_tables:
            print(f"  Incremental Tables ({len(incremental_tables)}): {', '.join(incremental_tables)}")
        
        print(f"  Verification Enabled: {config.verification.enabled}")
        print(f"  Logging Level: {config.logging.level}")
        
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration validation failed:")
        print(f"  {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error during validation:")
        print(f"  {e}")
        return 1


def list_environments_command(args: argparse.Namespace) -> int:
    """
    List available environment configurations.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_dir = Path(args.config_dir) if args.config_dir else None
        loader = ConfigLoader(config_dir)
        
        environments = loader.list_environments()
        
        if environments:
            print("Available environments:")
            for env in environments:
                print(f"  - {env}")
        else:
            print("No environment configurations found.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error listing environments:")
        print(f"  {e}")
        return 1


def show_config_command(args: argparse.Namespace) -> int:
    """
    Show resolved configuration (with environment variables substituted).
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config_dir = Path(args.config_dir) if args.config_dir else None
        loader = ConfigLoader(config_dir)
        
        print(f"Loading configuration: {args.config_file}")
        if args.environment:
            print(f"Environment: {args.environment}")
        
        config = loader.load_configuration(args.config_file, args.environment)
        
        # Show resolved configuration
        import yaml
        config_dict = config.dict()
        
        # Hide sensitive information
        if 'connections' in config_dict:
            for conn_name, conn_config in config_dict['connections'].items():
                if 'connection_string' in conn_config:
                    # Mask password in connection string
                    conn_str = conn_config['connection_string']
                    if '@' in conn_str and ':' in conn_str:
                        parts = conn_str.split('@')
                        if len(parts) == 2:
                            user_pass = parts[0].split(':')
                            if len(user_pass) >= 3:  # protocol://user:pass
                                user_pass[-1] = '***'
                                parts[0] = ':'.join(user_pass)
                                conn_config['connection_string'] = '@'.join(parts)
        
        print("\nResolved Configuration:")
        print(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))
        
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration error:")
        print(f"  {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error:")
        print(f"  {e}")
        return 1


def create_sample_config_command(args: argparse.Namespace) -> int:
    """
    Create a sample configuration file.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        output_path = Path(args.output)
        
        if output_path.exists() and not args.force:
            print(f"❌ File already exists: {output_path}")
            print("Use --force to overwrite")
            return 1
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        sample_config = """# Sample Pipeline Configuration
pipeline:
  name: "my_data_migration"
  dataset_name: "migrated_data"
  chunk_size: 10000
  backend: "pyarrow"

connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema: "dbo"
  destination:
    connection_string: "${DEST_CONNECTION_STRING}"
    schema: "target_schema"

tables:
  my_table:
    source_table: "dbo.MyTable"
    destination_table: "my_table"
    disposition: "replace"
    incremental:
      enabled: false
    enabled: true

verification:
  enabled: true
  tolerance: 0

logging:
  level: "INFO"
"""
        
        with open(output_path, 'w') as f:
            f.write(sample_config)
        
        print(f"✅ Sample configuration created: {output_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Error creating sample configuration:")
        print(f"  {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Configuration utilities for DLT Pipeline Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config-dir',
        help='Configuration directory path (default: config/)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.add_argument(
        'config_file',
        nargs='?',
        default='pipeline_config.yaml',
        help='Configuration file to validate (default: pipeline_config.yaml)'
    )
    validate_parser.add_argument(
        '--environment', '-e',
        help='Environment configuration to use'
    )
    
    # List environments command
    list_parser = subparsers.add_parser('list-envs', help='List available environments')
    
    # Show config command
    show_parser = subparsers.add_parser('show', help='Show resolved configuration')
    show_parser.add_argument(
        'config_file',
        nargs='?',
        default='pipeline_config.yaml',
        help='Configuration file to show (default: pipeline_config.yaml)'
    )
    show_parser.add_argument(
        '--environment', '-e',
        help='Environment configuration to use'
    )
    
    # Create sample command
    sample_parser = subparsers.add_parser('create-sample', help='Create sample configuration file')
    sample_parser.add_argument(
        'output',
        help='Output file path'
    )
    sample_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite existing file'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'validate':
        return validate_config_command(args)
    elif args.command == 'list-envs':
        return list_environments_command(args)
    elif args.command == 'show':
        return show_config_command(args)
    elif args.command == 'create-sample':
        return create_sample_config_command(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())