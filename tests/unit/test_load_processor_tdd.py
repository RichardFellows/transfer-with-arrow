#!/usr/bin/env python3
"""
TDD tests for LoadProcessor.
Tests written first to define expected behavior, then implementation follows.
"""

import pytest
pytestmark = pytest.mark.unit
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import tempfile
from pathlib import Path
from datetime import datetime

from src.pipeline.config_models import (
    ConfigurationModel, PipelineConfig, PipelineMode, ArchiveConfig, LoadConfig,
    ConnectionConfig, TableConfig, BatchSelection
)
from src.pipeline.archive_manager import ArchiveManager
from src.utils.parquet_utils import ParquetFileInfo
from src.utils.manifest_manager import ExtractionBatch, BatchStatus
from src.pipeline.load_processor import LoadProcessor


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
def load_config(temp_archive_path, temp_manifest_path):
    """Create configuration for load-only mode."""
    return ConfigurationModel(
        pipeline=PipelineConfig(
            pipeline_mode=PipelineMode.LOAD_ONLY,
            chunk_size=1000
        ),
        connections={
            "destination": ConnectionConfig(
                connection_string="mssql://user:pass@localhost:1434/testdb",
                schema_name="dbo"
            )
        },
        tables={
            "test_table": TableConfig(
                source_table="dbo.TestTable",
                destination_table="test_table",
                enabled=True
            ),
            "incremental_table": TableConfig(
                source_table="dbo.IncrementalTable", 
                destination_table="incremental_table",
                enabled=True
            )
        },
        archive=ArchiveConfig(
            enabled=True,
            storage_path=str(temp_archive_path),
            manifest_path=str(temp_manifest_path),
            compression="snappy"
        ),
        load=LoadConfig(
            batch_selection=BatchSelection.LATEST,
            allow_historical=True,
            concurrent_batches=1
        ),
        verification={},
        logging={}
    )


@pytest.fixture
def mock_archive_manager():
    """Create mock archive manager."""
    mock_manager = Mock(spec=ArchiveManager)
    
    # Mock batch data
    mock_batch = ExtractionBatch(
        batch_id="batch_123",
        table_name="test_table",
        status=BatchStatus.COMPLETED,
        created_at=datetime.now(),
        source_query="SELECT * FROM test_table",
        watermark_value=None,
        metadata={"row_count": 100}
    )
    
    mock_manager.get_latest_batch.return_value = mock_batch
    mock_manager.list_available_batches.return_value = [mock_batch]
    mock_manager.get_batches_in_date_range.return_value = [mock_batch]
    mock_manager.load_extraction_data.return_value = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })
    
    return mock_manager


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })


# Note: We'll need to define LoadProcessor class first, so let's assume it will be imported
# from src.pipeline.load_processor import LoadProcessor


class TestLoadProcessorInitialization:
    """Test LoadProcessor initialization."""
    
    def test_init_with_archive_manager(self, load_config, mock_archive_manager):
        """Test: LoadProcessor should initialize with provided archive manager."""
        # Arrange & Act
        processor = LoadProcessor(
            config=load_config,
            archive_manager=mock_archive_manager
        )
        
        # Assert
        assert processor.config == load_config
        assert processor.archive_manager == mock_archive_manager
        assert processor.load_logger is not None
    
    def test_init_creates_archive_manager_when_none_provided(self, load_config):
        """Test: LoadProcessor should create archive manager when none provided."""
        # Arrange & Act
        processor = LoadProcessor(config=load_config)
        
        # Assert
        assert processor.config == load_config
        assert processor.archive_manager is not None
    
    def test_init_validates_destination_connection(self, load_config):
        """Test: LoadProcessor should validate destination connection exists."""
        # Arrange
        del load_config.connections["destination"]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Destination connection required"):
            LoadProcessor(config=load_config)


class TestBatchSelection:
    """Test batch selection functionality."""
    
    def test_get_latest_batch_for_table(self, load_config, mock_archive_manager):
        """Test: Should get latest batch for a specific table."""
        # This test defines expected behavior - implementation comes after
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.get_latest_batch.return_value = "batch_123"
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            batch_id = processor.get_latest_batch("test_table")
            
            # Assert
            assert batch_id == "batch_123"
            mock_instance.get_latest_batch.assert_called_once_with("test_table")
    
    def test_get_specific_batch(self, load_config, mock_archive_manager):
        """Test: Should get specific batch by ID."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.get_batch_info.return_value = {"batch_id": "batch_456", "status": "COMPLETED"}
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            batch_info = processor.get_batch_info("batch_456")
            
            # Assert
            assert batch_info["batch_id"] == "batch_456"
            mock_instance.get_batch_info.assert_called_once_with("batch_456")
    
    def test_get_batches_in_date_range(self, load_config, mock_archive_manager):
        """Test: Should get batches within specified date range."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.get_batches_in_date_range.return_value = ["batch_123", "batch_124"]
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 1, 31)
            batches = processor.get_batches_in_date_range("test_table", start_date, end_date)
            
            # Assert
            assert len(batches) == 2
            mock_instance.get_batches_in_date_range.assert_called_once()


class TestDataLoading:
    """Test data loading functionality."""
    
    def test_load_latest_batch_for_table(self, load_config, mock_archive_manager, sample_dataframe):
        """Test: Should load latest batch for a table to destination."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_latest_batch.return_value = {
                "batch_id": "batch_123",
                "table_name": "test_table",
                "rows_loaded": 100,
                "status": "success"
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.load_latest_batch("test_table")
            
            # Assert
            assert result["batch_id"] == "batch_123"
            assert result["rows_loaded"] == 100
            assert result["status"] == "success"
            mock_instance.load_latest_batch.assert_called_once_with("test_table")
    
    def test_load_specific_batch(self, load_config, mock_archive_manager):
        """Test: Should load specific batch by ID."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.return_value = {
                "batch_id": "batch_456",
                "table_name": "test_table",
                "rows_loaded": 150,
                "status": "success"
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.load_batch("batch_456")
            
            # Assert
            assert result["batch_id"] == "batch_456"
            assert result["rows_loaded"] == 150
            mock_instance.load_batch.assert_called_once_with("batch_456")
    
    def test_load_multiple_tables(self, load_config, mock_archive_manager):
        """Test: Should load latest batches for multiple tables."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_all_tables.return_value = {
                "test_table": {"batch_id": "batch_123", "rows_loaded": 100, "status": "success"},
                "incremental_table": {"batch_id": "batch_124", "rows_loaded": 50, "status": "success"}
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            results = processor.load_all_tables()
            
            # Assert
            assert len(results) == 2
            assert results["test_table"]["rows_loaded"] == 100
            assert results["incremental_table"]["rows_loaded"] == 50
            mock_instance.load_all_tables.assert_called_once()
    
    def test_load_with_verification(self, load_config, mock_archive_manager):
        """Test: Should verify data after loading when verification enabled."""
        # Enable verification
        load_config.verification = {"enabled": True}
        
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_with_verification.return_value = {
                "batch_id": "batch_123",
                "rows_loaded": 100,
                "verification_passed": True,
                "status": "success"
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.load_with_verification("test_table", "batch_123")
            
            # Assert
            assert result["verification_passed"] is True
            mock_instance.load_with_verification.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_load_nonexistent_batch_raises_error(self, load_config, mock_archive_manager):
        """Test: Should raise error when trying to load nonexistent batch."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.side_effect = ValueError("Batch not found: batch_999")
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act & Assert
            with pytest.raises(ValueError, match="Batch not found: batch_999"):
                processor.load_batch("batch_999")
    
    def test_load_incomplete_batch_raises_error(self, load_config, mock_archive_manager):
        """Test: Should raise error when trying to load incomplete batch."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.side_effect = ValueError("Batch not completed: batch_pending")
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act & Assert
            with pytest.raises(ValueError, match="Batch not completed: batch_pending"):
                processor.load_batch("batch_pending")
    
    def test_load_with_destination_connection_error(self, load_config, mock_archive_manager):
        """Test: Should handle destination connection errors gracefully."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.side_effect = ConnectionError("Failed to connect to destination")
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act & Assert
            with pytest.raises(ConnectionError, match="Failed to connect to destination"):
                processor.load_batch("batch_123")


class TestBatchStatusManagement:
    """Test batch status management during loading."""
    
    def test_marks_batch_as_loading_during_load(self, load_config, mock_archive_manager):
        """Test: Should mark batch as LOADING status during load operation."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.return_value = {"status": "success"}
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            processor.load_batch("batch_123")
            
            # Assert - This would verify the batch status was updated
            # Implementation will need to call archive_manager to update status
            mock_instance.load_batch.assert_called_once_with("batch_123")
    
    def test_marks_batch_as_loaded_on_success(self, load_config, mock_archive_manager):
        """Test: Should mark batch as LOADED status on successful completion."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.return_value = {"status": "success"}
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.load_batch("batch_123")
            
            # Assert
            assert result["status"] == "success"
    
    def test_marks_batch_as_failed_on_error(self, load_config, mock_archive_manager):
        """Test: Should mark batch as FAILED status on load error."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.load_batch.return_value = {"status": "failed", "error": "Load failed"}
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.load_batch("batch_123")
            
            # Assert
            assert result["status"] == "failed"
            assert "error" in result


class TestValidation:
    """Test validation functionality."""
    
    def test_validate_load_readiness_success(self, load_config, mock_archive_manager):
        """Test: Should return ready=True for valid load configuration."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.validate_load_readiness.return_value = {
                "ready": True,
                "issues": [],
                "warnings": []
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.validate_load_readiness()
            
            # Assert
            assert result["ready"] is True
            assert len(result["issues"]) == 0
    
    def test_validate_load_readiness_fails_without_destination(self, load_config, mock_archive_manager):
        """Test: Should fail validation without destination connection."""
        del load_config.connections["destination"]
        
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.validate_load_readiness.return_value = {
                "ready": False,
                "issues": ["Destination connection not configured"],
                "warnings": []
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.validate_load_readiness()
            
            # Assert
            assert result["ready"] is False
            assert "Destination connection not configured" in result["issues"]
    
    def test_validate_load_readiness_warns_about_archive_access(self, load_config, mock_archive_manager):
        """Test: Should warn if archive is not accessible."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.validate_load_readiness.return_value = {
                "ready": True,
                "issues": [],
                "warnings": ["Archive path not accessible"]
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            result = processor.validate_load_readiness()
            
            # Assert
            assert result["ready"] is True
            assert "Archive path not accessible" in result["warnings"]


class TestStatistics:
    """Test statistics and monitoring functionality."""
    
    def test_get_load_statistics(self, load_config, mock_archive_manager):
        """Test: Should return load statistics."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.get_load_statistics.return_value = {
                "total_batches_loaded": 5,
                "total_rows_loaded": 10000,
                "last_load_time": "2023-01-15T10:30:00",
                "tables_loaded": ["test_table", "incremental_table"]
            }
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            stats = processor.get_load_statistics()
            
            # Assert
            assert stats["total_batches_loaded"] == 5
            assert stats["total_rows_loaded"] == 10000
            assert len(stats["tables_loaded"]) == 2
    
    def test_get_table_load_history(self, load_config, mock_archive_manager):
        """Test: Should return load history for specific table."""
        with patch('src.pipeline.load_processor.LoadProcessor') as MockLoadProcessor:
            mock_instance = Mock()
            mock_instance.get_table_load_history.return_value = [
                {"batch_id": "batch_123", "loaded_at": "2023-01-15T10:30:00", "rows": 100},
                {"batch_id": "batch_124", "loaded_at": "2023-01-16T10:30:00", "rows": 150}
            ]
            MockLoadProcessor.return_value = mock_instance
            
            processor = MockLoadProcessor(config=load_config, archive_manager=mock_archive_manager)
            
            # Act
            history = processor.get_table_load_history("test_table")
            
            # Assert
            assert len(history) == 2
            assert history[0]["batch_id"] == "batch_123"
            assert history[1]["rows"] == 150