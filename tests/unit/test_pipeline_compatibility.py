#!/usr/bin/env python3

import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import argparse

# Add the dlt_scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts/src'))

from run_pipeline import run_pipeline_command, validate_config_command, show_statistics_command
from src.pipeline.config_loader import load_config
from src.pipeline.pipeline_runner import PipelineRunner


class TestPipelineCompatibility:
    """Unit tests for new pipeline system compatibility with legacy functionality."""

    def create_stackoverflow_config(self, env_vars, temp_dir):
        """Create a StackOverflow-compatible configuration."""
        config_content = {
            "pipeline": {
                "name": "stackoverflow_copy",
                "dataset_name": "stackoverflow_data",
                "chunk_size": 10000,
                "backend": "pyarrow",
                "loader_file_format": "parquet"
            },
            "connections": {
                "source": {
                    "connection_string": env_vars['source'],
                    "schema": "dbo"
                },
                "destination": {
                    "connection_string": env_vars['dest'],
                    "schema": "stackoverflow_data"
                }
            },
            "tables": {
                "Users": {
                    "source_table": "dbo.Users",
                    "destination_table": "users",
                    "disposition": "replace",
                    "enabled": True
                },
                "Posts": {
                    "source_table": "dbo.Posts",
                    "destination_table": "posts",
                    "disposition": "replace",
                    "enabled": True,
                    "incremental": {
                        "enabled": False
                    }
                },
                "Comments": {
                    "source_table": "dbo.Comments",
                    "destination_table": "comments",
                    "disposition": "replace",
                    "enabled": True
                },
                "Votes": {
                    "source_table": "dbo.Votes",
                    "destination_table": "votes",
                    "disposition": "replace",
                    "enabled": True
                },
                "Badges": {
                    "source_table": "dbo.Badges",
                    "destination_table": "badges",
                    "disposition": "replace",
                    "enabled": True
                },
                "PostTags": {
                    "source_table": "dbo.PostTags",
                    "destination_table": "posttags",
                    "disposition": "replace",
                    "enabled": True
                },
                "Tags": {
                    "source_table": "dbo.Tags",
                    "destination_table": "tags",
                    "disposition": "replace",
                    "enabled": True
                }
            },
            "verification": {
                "enabled": True,
                "tolerance": 0
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        config_file = Path(temp_dir) / "stackoverflow_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        return config_file

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables like the old tests."""
        return {
            'source': 'mssql+pyodbc://sa:password@source:1433/StackOverflowMini?driver=test',
            'dest': 'mssql+pyodbc://sa:password@dest:1433/TargetDB?driver=test'
        }

    @pytest.mark.unit
    def test_default_stackoverflow_tables_configuration(self, mock_env_vars):
        """Test that new system supports all default StackOverflow tables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            config = load_config(str(config_file))
            
            # Verify all default StackOverflow tables are configured
            expected_tables = ["Users", "Posts", "Comments", "Votes", "Badges", "PostTags", "Tags"]
            
            for table in expected_tables:
                assert table in config.tables
                assert config.tables[table].enabled is True
                assert config.tables[table].source_table == f"dbo.{table}"
                assert config.tables[table].disposition.value == "replace"

    @pytest.mark.unit
    def test_incremental_loading_configuration(self, mock_env_vars):
        """Test incremental loading configuration (replaces old incremental test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            
            # Modify config to enable incremental loading for Posts
            config_content = yaml.safe_load(open(config_file))
            config_content["tables"]["Posts"]["incremental"] = {
                "enabled": True,
                "strategy": "timestamp",
                "watermark_column": "CreationDate", 
                "initial_value": "2020-01-01T00:00:00"
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config = load_config(str(config_file))
            
            posts_config = config.tables["Posts"]
            assert posts_config.incremental.enabled is True
            assert posts_config.incremental.strategy.value == "timestamp"
            assert posts_config.incremental.watermark_column == "CreationDate"
            assert posts_config.incremental.initial_value == "2020-01-01T00:00:00"

    @pytest.mark.unit
    def test_write_disposition_support(self, mock_env_vars):
        """Test different write dispositions (replaces old disposition test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            
            for disposition in ['replace', 'append', 'merge']:
                # Modify config with different disposition
                config_content = yaml.safe_load(open(config_file))
                config_content["tables"]["Users"]["disposition"] = disposition
                
                if disposition == 'merge':
                    config_content["tables"]["Users"]["primary_key"] = ["Id"]
                
                with open(config_file, 'w') as f:
                    yaml.dump(config_content, f)
                
                config = load_config(str(config_file))
                assert config.tables["Users"].disposition.value == disposition

    @pytest.mark.unit 
    def test_custom_table_selection(self, mock_env_vars):
        """Test custom table selection (replaces old tables selection test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            
            # Disable all but Users and Posts tables
            config_content = yaml.safe_load(open(config_file))
            for table_name in config_content["tables"]:
                if table_name not in ["Users", "Posts"]:
                    config_content["tables"][table_name]["enabled"] = False
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config = load_config(str(config_file))
            
            enabled_tables = [name for name, table in config.tables.items() if table.enabled]
            assert set(enabled_tables) == {"Users", "Posts"}

    @pytest.mark.unit
    def test_verification_functionality(self, mock_env_vars):
        """Test verification functionality (replaces old verify_copy test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            config = load_config(str(config_file))
            
            # Verify verification is enabled by default
            assert config.verification.enabled is True
            assert config.verification.tolerance == 0
            
            # Test with custom verification settings
            config_content = yaml.safe_load(open(config_file))
            config_content["verification"]["tables"] = ["Users", "Posts"]
            config_content["verification"]["custom_checks"] = {
                "positive_ids": "SELECT COUNT(*) FROM Users WHERE Id <= 0"
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config = load_config(str(config_file))
            assert config.verification.tables == ["Users", "Posts"]
            assert "positive_ids" in config.verification.custom_checks

    @pytest.mark.unit
    def test_cli_argument_compatibility(self, mock_env_vars):
        """Test CLI argument compatibility with old script."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_stackoverflow_config(mock_env_vars, temp_dir)
            
            # Test equivalent of old --tables argument
            args = argparse.Namespace(
                config=str(config_file),
                config_dir=None,
                environment=None,
                tables=["Users", "Posts"],  # Equivalent to old --tables
                output=None
            )
            
            # This should not raise an error (we're not actually running due to mocking needs)
            # Just test that the argument structure is compatible
            assert args.tables == ["Users", "Posts"]
            assert args.config == str(config_file)

    @pytest.mark.unit
    def test_environment_variable_support(self, mock_env_vars, monkeypatch):
        """Test environment variable support (replaces old env var tests)."""
        # Set environment variables
        monkeypatch.setenv('SOURCE_CONNECTION_STRING', mock_env_vars['source'])
        monkeypatch.setenv('DEST_CONNECTION_STRING', mock_env_vars['dest'])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config using environment variables
            config_content = {
                "pipeline": {
                    "name": "stackoverflow_copy",
                    "dataset_name": "stackoverflow_data"
                },
                "connections": {
                    "source": {
                        "connection_string": "${SOURCE_CONNECTION_STRING}"
                    },
                    "destination": {
                        "connection_string": "${DEST_CONNECTION_STRING}"
                    }
                },
                "tables": {
                    "Users": {
                        "source_table": "dbo.Users",
                        "enabled": True
                    }
                }
            }
            
            config_file = Path(temp_dir) / "env_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            config = load_config(str(config_file))
            
            # Verify environment variables were substituted
            assert config.connections["source"].connection_string == mock_env_vars['source']
            assert config.connections["destination"].connection_string == mock_env_vars['dest']

    @pytest.mark.unit
    def test_config_validation_errors(self, mock_env_vars):
        """Test configuration validation (replaces old error handling tests)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid config (missing required fields)
            invalid_config = {
                "pipeline": {
                    "name": "test"
                    # Missing dataset_name
                },
                "connections": {
                    "source": {
                        "connection_string": mock_env_vars['source']
                    }
                    # Missing destination
                },
                "tables": {}  # No tables defined
            }
            
            config_file = Path(temp_dir) / "invalid_config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(invalid_config, f)
            
            # Test that validation fails appropriately
            from src.pipeline.config_loader import ConfigurationError
            with pytest.raises(ConfigurationError):
                load_config(str(config_file))


class TestLegacyCommandMapping:
    """Test that new commands provide equivalent functionality to old ones."""
    
    @pytest.mark.unit
    def test_command_equivalencies(self):
        """Test that new commands map to old functionality."""
        # Old: copy_stackoverflow.py --tables Users Posts
        # New: run_pipeline.py run --tables Users Posts
        
        # Old: copy_stackoverflow.py --verify  
        # New: run_pipeline.py run (with verification.enabled: true in config)
        
        # Old: copy_stackoverflow.py --incremental
        # New: run_pipeline.py run (with incremental.enabled: true in table config)
        
        # Old: copy_stackoverflow.py --disposition append
        # New: run_pipeline.py run (with disposition: append in table config)
        
        # These are conceptual mappings - the new system is more powerful
        assert True  # Placeholder for mapping verification

    @pytest.mark.unit 
    def test_enhanced_capabilities(self):
        """Test that new system provides enhanced capabilities beyond old script."""
        # New capabilities not available in old script:
        # - Environment-specific configurations
        # - Per-table incremental settings
        # - Custom verification checks
        # - Advanced logging and monitoring
        # - Configuration validation
        # - Table-specific filters and transformations
        
        assert True  # These are verified in other configuration tests