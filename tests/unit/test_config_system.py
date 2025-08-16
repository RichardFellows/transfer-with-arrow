#!/usr/bin/env python3

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

# Add the dlt_scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts/src'))

from src.pipeline.config_models import (
    ConfigurationModel, TableConfig, IncrementalConfig, 
    ConnectionConfig, VerificationConfig, LoggingConfig,
    PipelineConfig, WriteDisposition, IncrementalStrategy
)
from src.pipeline.config_loader import load_config, ConfigurationError
from src.pipeline.pipeline_runner import PipelineRunner


class TestConfigModels:
    """Unit tests for Pydantic configuration models."""

    @pytest.mark.unit
    def test_table_config_defaults(self):
        """Test TableConfig with default values."""
        config = TableConfig(source_table="dbo.Users")
        
        assert config.source_table == "dbo.Users"
        assert config.destination_table == "users"  # Auto-generated from source
        assert config.disposition == WriteDisposition.REPLACE
        assert config.enabled is True
        assert config.incremental.enabled is False
        assert config.primary_key is None
        assert config.where_clause is None

    @pytest.mark.unit
    def test_table_config_custom_destination(self):
        """Test TableConfig with custom destination table name."""
        config = TableConfig(
            source_table="dbo.Users",
            destination_table="custom_users"
        )
        
        assert config.destination_table == "custom_users"

    @pytest.mark.unit
    def test_incremental_config_timestamp_strategy(self):
        """Test IncrementalConfig with timestamp strategy."""
        config = IncrementalConfig(
            enabled=True,
            strategy=IncrementalStrategy.TIMESTAMP,
            watermark_column="UpdatedDate",
            initial_value="2020-01-01T00:00:00"
        )
        
        assert config.enabled is True
        assert config.strategy == IncrementalStrategy.TIMESTAMP
        assert config.watermark_column == "UpdatedDate"
        assert config.initial_value == "2020-01-01T00:00:00"

    @pytest.mark.unit
    def test_pipeline_config_validation(self):
        """Test PipelineConfig validation."""
        config = PipelineConfig(
            name="test_pipeline",
            dataset_name="test_data"
        )
        
        assert config.name == "test_pipeline"
        assert config.dataset_name == "test_data"
        assert config.chunk_size == 10000
        assert config.backend == "pyarrow"
        assert config.loader_file_format == "parquet"

    @pytest.mark.unit
    def test_configuration_model_full(self):
        """Test complete ConfigurationModel."""
        config_dict = {
            "pipeline": {
                "name": "test_migration",
                "dataset_name": "test_data"
            },
            "connections": {
                "source": ConnectionConfig(
                    connection_string="source_conn",
                    schema_name="dbo"
                ),
                "destination": ConnectionConfig(
                    connection_string="dest_conn",
                    schema_name="target"
                )
            },
            "tables": {
                "Users": {
                    "source_table": "dbo.Users",
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
        
        config = ConfigurationModel(**config_dict)
        
        assert config.pipeline.name == "test_migration"
        assert config.connections["source"].connection_string == "source_conn"
        assert "Users" in config.tables
        assert config.tables["Users"].source_table == "dbo.Users"
        assert config.verification.enabled is True
        assert config.logging.level == "INFO"


class TestConfigLoader:
    """Unit tests for configuration loading."""

    def create_temp_config_file(self, config_content):
        """Helper to create temporary config file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_content, temp_file)
        temp_file.close()
        return temp_file.name

    @pytest.mark.unit
    def test_load_basic_config(self):
        """Test loading basic configuration."""
        config_content = {
            "pipeline": {
                "name": "test_pipeline",
                "dataset_name": "test_data"
            },
            "connections": {
                "source": {
                    "connection_string": "source_conn"
                },
                "destination": {
                    "connection_string": "dest_conn"
                }
            },
            "tables": {
                "Users": {
                    "source_table": "dbo.Users"
                }
            }
        }
        
        config_file = self.create_temp_config_file(config_content)
        
        try:
            config = load_config(config_file)
            assert config.pipeline.name == "test_pipeline"
            assert config.tables["Users"].source_table == "dbo.Users"
        finally:
            os.unlink(config_file)

    @pytest.mark.unit
    def test_load_config_with_environment_substitution(self, monkeypatch):
        """Test configuration loading with environment variable substitution."""
        monkeypatch.setenv("SOURCE_CONN", "test_source_connection")
        monkeypatch.setenv("DEST_CONN", "test_dest_connection")
        
        config_content = {
            "pipeline": {
                "name": "test_pipeline",
                "dataset_name": "test_data"
            },
            "connections": {
                "source": {
                    "connection_string": "${SOURCE_CONN}"
                },
                "destination": {
                    "connection_string": "${DEST_CONN}"
                }
            },
            "tables": {
                "Users": {
                    "source_table": "dbo.Users"
                }
            }
        }
        
        config_file = self.create_temp_config_file(config_content)
        
        try:
            config = load_config(config_file)
            assert config.connections["source"].connection_string == "test_source_connection"
            assert config.connections["destination"].connection_string == "test_dest_connection"
        finally:
            os.unlink(config_file)

    @pytest.mark.unit
    def test_load_config_with_environment_override(self):
        """Test configuration loading with environment-specific overrides."""
        base_config = {
            "pipeline": {
                "name": "base_pipeline",
                "dataset_name": "base_data",
                "chunk_size": 10000
            },
            "connections": {
                "source": {"connection_string": "base_source"},
                "destination": {"connection_string": "base_dest"}
            },
            "tables": {
                "Users": {"source_table": "dbo.Users"}
            }
        }
        
        env_config = {
            "pipeline": {
                "name": "dev_pipeline",
                "chunk_size": 1000
            },
            "tables": {
                "Users": {
                    "where_clause": "IsActive = 1"
                }
            }
        }
        
        base_file = self.create_temp_config_file(base_config)
        
        # Create temporary environment config
        temp_dir = tempfile.mkdtemp()
        env_dir = Path(temp_dir) / "environments"
        env_dir.mkdir()
        env_file = env_dir / "dev.yaml"
        
        with open(env_file, 'w') as f:
            yaml.dump(env_config, f)
        
        try:
            config = load_config(base_file, environment="dev", config_dir=Path(temp_dir))
            
            # Base values should be preserved
            assert config.pipeline.dataset_name == "base_data"
            assert config.connections["source"].connection_string == "base_source"
            
            # Environment overrides should be applied
            assert config.pipeline.name == "dev_pipeline"
            assert config.pipeline.chunk_size == 1000
            assert config.tables["Users"].where_clause == "IsActive = 1"
            
        finally:
            os.unlink(base_file)
            import shutil
            shutil.rmtree(temp_dir)

    @pytest.mark.unit
    def test_load_config_validation_error(self):
        """Test configuration validation errors."""
        invalid_config = {
            "pipeline": {
                "name": "test_pipeline"
                # Missing required dataset_name
            },
            "connections": {
                "source": {"connection_string": "source_conn"}
                # Missing destination connection
            }
        }
        
        config_file = self.create_temp_config_file(invalid_config)
        
        try:
            with pytest.raises(ConfigurationError):
                load_config(config_file)
        finally:
            os.unlink(config_file)


class TestPipelineRunner:
    """Unit tests for PipelineRunner."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        return ConfigurationModel(
            pipeline=PipelineConfig(
                name="test_pipeline",
                dataset_name="test_data"
            ),
            connections={
                "source": ConnectionConfig(connection_string="sqlite:///source.db"),
                "destination": ConnectionConfig(connection_string="sqlite:///dest.db")
            },
            tables={
                "Users": TableConfig(source_table="dbo.Users"),
                "Posts": TableConfig(
                    source_table="dbo.Posts",
                    incremental=IncrementalConfig(
                        enabled=True,
                        strategy=IncrementalStrategy.TIMESTAMP,
                        watermark_column="CreationDate",
                        initial_value="2020-01-01T00:00:00"
                    )
                )
            },
            verification=VerificationConfig(enabled=True),
            logging=LoggingConfig(level="INFO")
        )

    @pytest.mark.unit
    def test_pipeline_runner_initialization(self, sample_config):
        """Test PipelineRunner initialization."""
        with patch('src.pipeline.pipeline_runner.setup_logging'), \
             patch('src.pipeline.table_processor.TableProcessor'), \
             patch('src.pipeline.verification.DataVerifier'):
            
            runner = PipelineRunner(sample_config)
            
            assert runner.config == sample_config
            assert runner.results == {
                'status': 'pending',
                'start_time': None,
                'end_time': None,
                'duration_seconds': 0,
                'tables_processed': [],
                'table_results': {},
                'verification_results': {},
                'error': None
            }

    @pytest.mark.unit
    def test_get_enabled_tables(self, sample_config):
        """Test getting enabled tables from configuration."""
        with patch('src.pipeline.pipeline_runner.setup_logging'), \
             patch('src.pipeline.table_processor.TableProcessor'), \
             patch('src.pipeline.verification.DataVerifier'):
            
            runner = PipelineRunner(sample_config)
            
            # All tables enabled by default
            enabled_tables = runner._get_enabled_tables()
            assert "Users" in enabled_tables
            assert "Posts" in enabled_tables
            
            # Filter specific tables
            specific_tables = runner._get_enabled_tables(["Users"])
            assert "Users" in specific_tables
            assert "Posts" not in specific_tables

    @pytest.mark.unit
    def test_run_with_mocked_dependencies(self, sample_config):
        """Test pipeline run with mocked dependencies."""
        with patch('src.pipeline.pipeline_runner.setup_logging'), \
             patch('src.pipeline.table_processor.TableProcessor') as mock_processor_class, \
             patch('src.pipeline.verification.DataVerifier') as mock_verification_class:
            
            # Setup mocks
            mock_processor = Mock()
            mock_processor.process_table.return_value = {
                'status': 'success',
                'duration_seconds': 1.5,
                'rows_processed': 100
            }
            mock_processor_class.return_value = mock_processor
            
            mock_verification = Mock()
            mock_verification.verify_all_tables.return_value = {
                'verification_enabled': True,
                'total_checks': 2,
                'passed_checks': 2,
                'failed_checks': []
            }
            mock_verification_class.return_value = mock_verification
            
            runner = PipelineRunner(sample_config)
            results = runner.run()
            
            # Verify results structure
            assert results['status'] == 'success'
            assert len(results['tables_processed']) == 2
            assert 'Users' in results['tables_processed']
            assert 'Posts' in results['tables_processed']
            assert results['verification_results']['verification_enabled'] is True

    @pytest.mark.unit
    def test_run_with_table_processing_error(self, sample_config):
        """Test pipeline run when table processing fails."""
        with patch('src.pipeline.pipeline_runner.setup_logging'), \
             patch('src.pipeline.table_processor.TableProcessor') as mock_processor_class, \
             patch('src.pipeline.verification.DataVerifier'):
            
            # Setup mock to fail on second table
            mock_processor = Mock()
            mock_processor.process_table.side_effect = [
                {
                    'status': 'success',
                    'duration_seconds': 1.0,
                    'rows_processed': 50
                },
                Exception("Database connection failed")
            ]
            mock_processor_class.return_value = mock_processor
            
            runner = PipelineRunner(sample_config)
            results = runner.run()
            
            # Should fail after first table succeeds
            assert results['status'] == 'error'
            assert len(results['tables_processed']) == 1  # Only first table processed
            assert 'Database connection failed' in results['error']