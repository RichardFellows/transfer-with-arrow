#!/usr/bin/env python3
"""
TDD tests for TwoStagePipelineRunner.
Tests written first to define expected behavior for all pipeline modes and orchestration logic.
"""

import pytest
pytestmark = pytest.mark.unit
from unittest.mock import Mock, MagicMock, patch
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

from src.pipeline.two_stage_runner import TwoStagePipelineRunner
from src.pipeline.config_models import (
    ConfigurationModel, PipelineConfig, PipelineMode, ArchiveConfig, ExtractConfig,
    LoadConfig, ConnectionConfig, TableConfig, IncrementalConfig, IncrementalStrategy,
    BatchSelection, LoggingConfig
)


@pytest.fixture
def temp_archive_path(tmp_path):
    """Create temporary archive path."""
    archive_path = tmp_path / "test_archive"
    archive_path.mkdir()
    return archive_path


@pytest.fixture
def temp_manifest_path(tmp_path):
    """Create temporary manifest path."""
    manifest_path = tmp_path / "test_manifests"
    manifest_path.mkdir()
    return manifest_path


@pytest.fixture
def base_config_dict(temp_archive_path, temp_manifest_path):
    """Base configuration dictionary for testing."""
    return {
        "pipeline": {
            "pipeline_mode": "direct",
            "chunk_size": 1000
        },
        "connections": {
            "source": {
                "connection_string": "mssql://user:pass@localhost:1433/testdb",
                "schema_name": "dbo"
            },
            "destination": {
                "connection_string": "mssql://user:pass@localhost:1434/targetdb",
                "schema_name": "dbo"
            }
        },
        "archive": {
            "enabled": True,
            "storage_path": str(temp_archive_path),
            "manifest_path": str(temp_manifest_path),
            "retention_days": 30,
            "compression": "snappy"
        },
        "extract": {
            "enabled": True,
            "batch_size": 1000
        },
        "load": {
            "enabled": True,
            "verification_enabled": True
        },
        "tables": {
            "test_table": {
                "source_table": "dbo.TestTable",
                "destination_table": "test_table",
                "enabled": True,
                "incremental": {
                    "enabled": True,
                    "strategy": "timestamp",
                    "watermark_column": "updated_at",
                    "initial_value": "2023-01-01T00:00:00"
                }
            }
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


@pytest.fixture
def direct_config(base_config_dict):
    """Configuration for direct mode."""
    config_dict = base_config_dict.copy()
    config_dict["pipeline"]["pipeline_mode"] = "direct"
    return ConfigurationModel.model_validate(config_dict)


@pytest.fixture
def extract_only_config(base_config_dict):
    """Configuration for extract-only mode."""
    config_dict = base_config_dict.copy()
    config_dict["pipeline"]["pipeline_mode"] = "extract_only"
    return ConfigurationModel.model_validate(config_dict)


@pytest.fixture
def load_only_config(base_config_dict):
    """Configuration for load-only mode."""
    config_dict = base_config_dict.copy()
    config_dict["pipeline"]["pipeline_mode"] = "load_only"
    return ConfigurationModel.model_validate(config_dict)


@pytest.fixture
def two_stage_config(base_config_dict):
    """Configuration for two-stage mode."""
    config_dict = base_config_dict.copy()
    config_dict["pipeline"]["pipeline_mode"] = "two_stage"
    return ConfigurationModel.model_validate(config_dict)


class TestTwoStageRunnerInitialization:
    """Test TwoStagePipelineRunner initialization with different configurations."""
    
    def test_init_with_direct_mode(self, direct_config):
        """Test initialization with direct mode configuration."""
        with patch('src.pipeline.two_stage_runner.setup_logging') as mock_setup, \
             patch('src.pipeline.two_stage_runner.get_logger') as mock_get_logger, \
             patch('src.pipeline.two_stage_runner.PipelineRunner') as mock_runner:
            
            mock_logger = Mock()
            mock_setup.return_value = mock_logger
            mock_get_logger.return_value = mock_logger
            
            runner = TwoStagePipelineRunner(direct_config)
            
            # Verify configuration
            assert runner.config == direct_config
            assert runner.pipeline_mode == PipelineMode.DIRECT
            
            # Verify processors initialization
            assert runner.archive_manager is None  # No archive for direct mode
            assert runner.extract_processor is None
            assert runner.load_processor is None
            assert runner.direct_runner is not None
            
            # Verify logging setup
            mock_setup.assert_called_once_with(direct_config.logging, "two_stage_pipeline")
            mock_get_logger.assert_called_once_with("two_stage_runner")
    
    def test_init_with_extract_only_mode(self, extract_only_config):
        """Test initialization with extract-only mode configuration."""
        with patch('src.pipeline.two_stage_runner.setup_logging') as mock_setup, \
             patch('src.pipeline.two_stage_runner.get_logger') as mock_get_logger, \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract:
            
            mock_logger = Mock()
            mock_setup.return_value = mock_logger
            mock_get_logger.return_value = mock_logger
            
            runner = TwoStagePipelineRunner(extract_only_config)
            
            # Verify configuration
            assert runner.config == extract_only_config
            assert runner.pipeline_mode == PipelineMode.EXTRACT_ONLY
            
            # Verify processors initialization
            assert runner.archive_manager is not None
            assert runner.extract_processor is not None
            assert runner.load_processor is None
            assert runner.direct_runner is None
            
            # Verify archive manager initialization
            mock_archive.assert_called_once_with(
                archive_path=extract_only_config.archive.storage_path,
                manifest_path=extract_only_config.archive.manifest_path,
                retention_days=extract_only_config.archive.retention_days,
                logger=mock_logger
            )
            
            # Verify extract processor initialization
            mock_extract.assert_called_once_with(extract_only_config, mock_logger)
    
    def test_init_with_load_only_mode(self, load_only_config):
        """Test initialization with load-only mode configuration."""
        with patch('src.pipeline.two_stage_runner.setup_logging') as mock_setup, \
             patch('src.pipeline.two_stage_runner.get_logger') as mock_get_logger, \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive, \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load:
            
            mock_logger = Mock()
            mock_setup.return_value = mock_logger
            mock_get_logger.return_value = mock_logger
            
            runner = TwoStagePipelineRunner(load_only_config)
            
            # Verify configuration
            assert runner.config == load_only_config
            assert runner.pipeline_mode == PipelineMode.LOAD_ONLY
            
            # Verify processors initialization
            assert runner.archive_manager is not None
            assert runner.extract_processor is None
            assert runner.load_processor is not None
            assert runner.direct_runner is None
            
            # Verify load processor initialization
            mock_load.assert_called_once_with(load_only_config, mock_logger)
    
    def test_init_with_two_stage_mode(self, two_stage_config):
        """Test initialization with two-stage mode configuration."""
        with patch('src.pipeline.two_stage_runner.setup_logging') as mock_setup, \
             patch('src.pipeline.two_stage_runner.get_logger') as mock_get_logger, \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract, \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load:
            
            mock_logger = Mock()
            mock_setup.return_value = mock_logger
            mock_get_logger.return_value = mock_logger
            
            runner = TwoStagePipelineRunner(two_stage_config)
            
            # Verify configuration
            assert runner.config == two_stage_config
            assert runner.pipeline_mode == PipelineMode.TWO_STAGE
            
            # Verify processors initialization
            assert runner.archive_manager is not None
            assert runner.extract_processor is not None
            assert runner.load_processor is not None
            assert runner.direct_runner is None
            
            # Verify both processors initialized
            mock_extract.assert_called_once_with(two_stage_config, mock_logger)
            mock_load.assert_called_once_with(two_stage_config, mock_logger)


class TestPipelineModeExecution:
    """Test pipeline execution for different modes."""
    
    def test_run_direct_mode(self, direct_config):
        """Test running pipeline in direct mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner') as mock_runner_class, \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            # Setup mock direct runner
            mock_runner = Mock()
            mock_runner.run.return_value = {"table1": {"status": "completed", "rows": 100}}
            mock_runner_class.return_value = mock_runner
            
            runner = TwoStagePipelineRunner(direct_config)
            result = runner.run(tables_to_process=["table1"])
            
            # Verify direct runner called
            mock_runner.run.assert_called_once_with(["table1"])
            
            # Verify result structure
            assert result["mode"] == "direct"
            assert result["status"] == "completed"
            assert result["results"] == {"table1": {"status": "completed", "rows": 100}}
            assert "duration" in result
            assert "started_at" in result
            assert "completed_at" in result
    
    def test_run_extract_only_mode(self, extract_only_config):
        """Test running pipeline in extract-only mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class, \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            # Setup mock extract processor
            mock_extract = Mock()
            mock_extract.extract_tables.return_value = {
                "table1": {"status": "completed", "batch_id": "20250817_120000", "rows": 100}
            }
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(extract_only_config)
            result = runner.run(tables_to_process=["table1"], custom_metadata={"test": "value"})
            
            # Verify extract processor called
            mock_extract.extract_tables.assert_called_once_with(
                table_names=["table1"],
                custom_metadata={"test": "value"}
            )
            
            # Verify result structure
            assert result["mode"] == "extract_only"
            assert result["status"] == "completed"
            assert "extract_results" in result
            assert result["extract_results"]["phase"] == "extract"
            assert "duration" in result
    
    def test_run_load_only_mode(self, load_only_config):
        """Test running pipeline in load-only mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class, \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            # Setup mock load processor
            mock_load = Mock()
            mock_load.load_tables.return_value = {
                "table1": {"status": "completed", "loaded_rows": 100}
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.run(
                tables_to_process=["table1"],
                batch_selection=BatchSelection.LATEST,
                custom_metadata={"test": "value"}
            )
            
            # Verify load processor called
            mock_load.load_tables.assert_called_once_with(
                table_names=["table1"],
                batch_selection=BatchSelection.LATEST,
                specific_batch=None,
                start_date=None,
                end_date=None,
                custom_metadata={"test": "value"}
            )
            
            # Verify result structure
            assert result["mode"] == "load_only"
            assert result["status"] == "completed"
            assert "load_results" in result
            assert result["load_results"]["phase"] == "load"
    
    def test_run_two_stage_mode(self, two_stage_config):
        """Test running pipeline in two-stage mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class, \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class, \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            # Setup mock processors
            mock_extract = Mock()
            mock_extract.extract_tables.return_value = {
                "table1": {"status": "completed", "batch_id": "20250817_120000"},
                "table2": {"status": "completed", "batch_id": "20250817_120001"}
            }
            mock_extract_class.return_value = mock_extract
            
            mock_load = Mock()
            mock_load.load_tables.return_value = {
                "table1": {"status": "completed", "loaded_rows": 100},
                "table2": {"status": "completed", "loaded_rows": 200}
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.run(tables_to_process=["table1", "table2"])
            
            # Verify extract called first
            mock_extract.extract_tables.assert_called_once_with(
                table_names=["table1", "table2"],
                custom_metadata=None
            )
            
            # Verify load called with successful extracts
            mock_load.load_tables.assert_called_once_with(
                table_names=["table1", "table2"],
                batch_selection=BatchSelection.LATEST,
                specific_batch=None,
                start_date=None,
                end_date=None,
                custom_metadata=None
            )
            
            # Verify result structure
            assert result["mode"] == "two_stage"
            assert result["status"] == "completed"
            assert "extract_results" in result
            assert "load_results" in result
    
    def test_run_unsupported_mode(self, direct_config):
        """Test running with unsupported pipeline mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            runner = TwoStagePipelineRunner(direct_config)
            # Create a mock enum-like object that will fail in the run method
            class InvalidMode:
                value = "invalid_mode"
            
            runner.pipeline_mode = InvalidMode()
            
            result = runner.run()
            
            assert result["status"] == "failed"
            assert "Unsupported pipeline mode" in result["error"]


class TestExtractOperations:
    """Test extract operations and error handling."""
    
    def test_extract_tables_with_specific_tables(self, extract_only_config):
        """Test extracting specific tables."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class:
            
            mock_extract = Mock()
            mock_extract.extract_tables.return_value = {
                "table1": {"status": "completed", "batch_id": "20250817_120000", "rows": 100}
            }
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(extract_only_config)
            result = runner.extract_tables(
                tables_to_process=["table1"],
                custom_metadata={"source": "test"}
            )
            
            # Verify extract processor called correctly
            mock_extract.extract_tables.assert_called_once_with(
                table_names=["table1"],
                custom_metadata={"source": "test"}
            )
            
            # Verify result structure
            assert result["phase"] == "extract"
            assert result["status"] == "completed"
            assert "tables" in result
            assert "timestamp" in result
    
    def test_extract_tables_all_enabled(self, extract_only_config):
        """Test extracting all enabled tables."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class:
            
            mock_extract = Mock()
            mock_extract.extract_tables.return_value = {
                "table1": {"status": "completed", "batch_id": "20250817_120000"},
                "table2": {"status": "completed", "batch_id": "20250817_120001"}
            }
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(extract_only_config)
            result = runner.extract_tables()
            
            # Verify extract processor called with None (all tables)
            mock_extract.extract_tables.assert_called_once_with(
                table_names=None,
                custom_metadata=None
            )
            
            assert result["status"] == "completed"
    
    def test_extract_tables_error_handling(self, extract_only_config):
        """Test extract operation error handling."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class:
            
            mock_extract = Mock()
            mock_extract.extract_tables.side_effect = ValueError("Database connection failed")
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(extract_only_config)
            
            with pytest.raises(ValueError, match="Database connection failed"):
                runner.extract_tables()
    
    def test_extract_not_available_for_mode(self, direct_config):
        """Test extract operation when not available for pipeline mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner'):
            
            runner = TwoStagePipelineRunner(direct_config)
            
            with pytest.raises(ValueError, match="Extract processor not available"):
                runner.extract_tables()


class TestLoadOperations:
    """Test load operations with different batch selection strategies."""
    
    def test_load_tables_latest_batches(self, load_only_config):
        """Test loading latest batches for tables."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class:
            
            mock_load = Mock()
            mock_load.load_tables.return_value = {
                "table1": {"status": "completed", "loaded_rows": 100}
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.load_tables(
                tables_to_process=["table1"],
                batch_selection=BatchSelection.LATEST
            )
            
            # Verify load processor called correctly
            mock_load.load_tables.assert_called_once_with(
                table_names=["table1"],
                batch_selection=BatchSelection.LATEST,
                specific_batch=None,
                start_date=None,
                end_date=None,
                custom_metadata=None
            )
            
            # Verify result structure
            assert result["phase"] == "load"
            assert result["status"] == "completed"
            assert "tables" in result
    
    def test_load_tables_specific_batches(self, load_only_config):
        """Test loading specific batch."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class:
            
            mock_load = Mock()
            mock_load.load_tables.return_value = {
                "table1": {"status": "completed", "loaded_rows": 100}
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.load_tables(
                batch_selection=BatchSelection.SPECIFIC,
                specific_batch="20250817_120000"
            )
            
            # Verify specific batch loading
            mock_load.load_tables.assert_called_once_with(
                table_names=None,
                batch_selection=BatchSelection.SPECIFIC,
                specific_batch="20250817_120000",
                start_date=None,
                end_date=None,
                custom_metadata=None
            )
            
            assert result["status"] == "completed"
    
    def test_load_tables_date_range(self, load_only_config):
        """Test loading batches from date range."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class:
            
            mock_load = Mock()
            mock_load.load_tables.return_value = {
                "table1": {"status": "completed", "loaded_rows": 150}
            }
            mock_load_class.return_value = mock_load
            
            start_date = datetime(2025, 8, 15)
            end_date = datetime(2025, 8, 17)
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.load_tables(
                batch_selection=BatchSelection.DATE_RANGE,
                start_date=start_date,
                end_date=end_date
            )
            
            # Verify date range loading
            mock_load.load_tables.assert_called_once_with(
                table_names=None,
                batch_selection=BatchSelection.DATE_RANGE,
                specific_batch=None,
                start_date=start_date,
                end_date=end_date,
                custom_metadata=None
            )
            
            assert result["status"] == "completed"
    
    def test_load_not_available_for_mode(self, direct_config):
        """Test load operation when not available for pipeline mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner'):
            
            runner = TwoStagePipelineRunner(direct_config)
            
            with pytest.raises(ValueError, match="Load processor not available"):
                runner.load_tables()


class TestArchiveManagement:
    """Test archive management operations."""
    
    def test_get_archive_status_active(self, two_stage_config):
        """Test getting archive status when active."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive_class, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor'):
            
            # Setup mock archive manager
            mock_archive = Mock()
            mock_archive.get_archive_statistics.return_value = {
                "total_batches": 10,
                "total_size_mb": 500.5
            }
            mock_archive.list_available_batches.return_value = []
            mock_archive.get_latest_batch.return_value = None
            mock_archive_class.return_value = mock_archive
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.get_archive_status()
            
            # Verify archive operations called
            mock_archive.get_archive_statistics.assert_called_once()
            mock_archive.list_available_batches.assert_called_once_with(last_n=10)
            
            # Verify result structure
            assert result["status"] == "active"
            assert result["mode"] == "two_stage"
            assert "archive_statistics" in result
            assert "table_summaries" in result
            assert "recent_batches" in result
    
    def test_get_archive_status_disabled(self, direct_config):
        """Test getting archive status when disabled."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner'):
            
            runner = TwoStagePipelineRunner(direct_config)
            result = runner.get_archive_status()
            
            assert result["status"] == "archive_disabled"
            assert result["mode"] == "direct"
    
    def test_cleanup_archive_dry_run(self, two_stage_config):
        """Test archive cleanup in dry-run mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive_class, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor'):
            
            mock_archive = Mock()
            mock_archive.cleanup_archive.return_value = {
                "batches_to_delete": 5,
                "total_size_to_free_mb": 100.0
            }
            mock_archive_class.return_value = mock_archive
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.cleanup_archive(older_than_days=30, dry_run=True)
            
            # Verify cleanup called correctly
            mock_archive.cleanup_archive.assert_called_once_with(
                older_than_days=30,
                dry_run=True
            )
            
            # Verify result structure
            assert result["status"] == "completed"
            assert result["dry_run"] is True
            assert "cleanup_results" in result
    
    def test_cleanup_archive_disabled(self, direct_config):
        """Test archive cleanup when disabled."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner'):
            
            runner = TwoStagePipelineRunner(direct_config)
            result = runner.cleanup_archive()
            
            assert result["status"] == "archive_disabled"
    
    def test_validate_archive_integrity(self, two_stage_config):
        """Test archive integrity validation."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive_class, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor'):
            
            mock_archive = Mock()
            mock_archive.validate_archive_integrity.return_value = {
                "valid_batches": 8,
                "corrupted_batches": 0,
                "overall_status": "healthy"
            }
            mock_archive_class.return_value = mock_archive
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.validate_archive()
            
            # Verify validation called
            mock_archive.validate_archive_integrity.assert_called_once()
            
            # Verify result structure
            assert result["status"] == "completed"
            assert "validation_results" in result


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""
    
    def test_extract_failure_handling(self, two_stage_config):
        """Test handling extract failures in two-stage mode."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class, \
             patch('src.pipeline.two_stage_runner.LoadProcessor'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            mock_extract = Mock()
            mock_extract.extract_tables.side_effect = RuntimeError("Database timeout")
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.run()
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "Database timeout" in result["error"]
            assert "duration" in result
    
    def test_load_failure_handling(self, load_only_config):
        """Test handling load failures."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class, \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            mock_load = Mock()
            mock_load.load_tables.side_effect = RuntimeError("Destination unavailable")
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.run()
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "Destination unavailable" in result["error"]
    
    def test_two_stage_no_successful_extracts(self, two_stage_config):
        """Test two-stage mode when no extractions succeed."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.ExtractProcessor') as mock_extract_class, \
             patch('src.pipeline.two_stage_runner.LoadProcessor'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_start'), \
             patch('src.pipeline.two_stage_runner.log_pipeline_complete'):
            
            # Setup extract to return no successful results
            mock_extract = Mock()
            mock_extract.extract_tables.return_value = {
                "table1": {"status": "failed", "error": "No data found"}
            }
            mock_extract_class.return_value = mock_extract
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.run()
            
            # Verify error handling
            assert result["status"] == "failed"
            assert "No successful extractions to load" in result["error"]
    
    def test_archive_operation_errors(self, two_stage_config):
        """Test archive operation error handling."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager') as mock_archive_class, \
             patch('src.pipeline.two_stage_runner.ExtractProcessor'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor'):
            
            mock_archive = Mock()
            mock_archive.get_archive_statistics.side_effect = RuntimeError("Archive corrupted")
            mock_archive_class.return_value = mock_archive
            
            runner = TwoStagePipelineRunner(two_stage_config)
            result = runner.get_archive_status()
            
            # Verify error handling
            assert result["status"] == "error"
            assert "Archive corrupted" in result["error"]


class TestLoadRecommendations:
    """Test load recommendation functionality."""
    
    def test_get_load_recommendations_single_table(self, load_only_config):
        """Test getting load recommendations for a single table."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class:
            
            mock_load = Mock()
            mock_load.get_load_recommendations.return_value = {
                "recommended_batch": "20250817_120000",
                "available_batches": 5,
                "last_load_date": "2025-08-16T10:00:00"
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.get_load_recommendations("test_table")
            
            # Verify recommendation called
            mock_load.get_load_recommendations.assert_called_once_with("test_table")
            
            # Verify result structure
            assert result["status"] == "completed"
            assert "table_recommendations" in result
            assert "test_table" in result["table_recommendations"]
    
    def test_get_load_recommendations_all_tables(self, load_only_config):
        """Test getting load recommendations for all tables."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.ArchiveManager'), \
             patch('src.pipeline.two_stage_runner.LoadProcessor') as mock_load_class:
            
            mock_load = Mock()
            mock_load.get_load_recommendations.return_value = {
                "recommended_batch": "20250817_120000"
            }
            mock_load_class.return_value = mock_load
            
            runner = TwoStagePipelineRunner(load_only_config)
            result = runner.get_load_recommendations()
            
            # Verify recommendation called for configured table
            mock_load.get_load_recommendations.assert_called_with("test_table")
            
            # Verify result structure
            assert result["status"] == "completed"
            assert "table_recommendations" in result
    
    def test_get_load_recommendations_disabled(self, direct_config):
        """Test getting load recommendations when load processor disabled."""
        with patch('src.pipeline.two_stage_runner.setup_logging'), \
             patch('src.pipeline.two_stage_runner.get_logger'), \
             patch('src.pipeline.two_stage_runner.PipelineRunner'):
            
            runner = TwoStagePipelineRunner(direct_config)
            result = runner.get_load_recommendations()
            
            assert result["status"] == "load_processor_disabled"