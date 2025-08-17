#!/usr/bin/env python3
"""
TDD approach tests for ManifestManager - write tests first, then fix implementation.
Tests database-backed batch tracking and manifest management.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.utils.manifest_manager import ManifestManager, ExtractionBatch, BatchStatus


@pytest.fixture
def temp_manifest_dir():
    """Create temporary directory for manifest testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def manifest_manager(temp_manifest_dir):
    """Create ManifestManager instance with temporary directory."""
    return ManifestManager(temp_manifest_dir)


@pytest.fixture
def sample_batch_data():
    """Sample data for creating extraction batches."""
    return {
        "batch_id": "test_batch_001",
        "table_name": "test_table",
        "source_query": "SELECT * FROM test_table",
        "watermark_value": "2023-01-01T00:00:00",
        "metadata": {"extraction_type": "full", "test": True}
    }


@pytest.mark.unit
class TestManifestManagerBasicFunctionality:
    """Test basic ManifestManager functionality with TDD approach."""
    
    def test_can_create_manifest_manager_instance(self, temp_manifest_dir):
        """Test: Should be able to create ManifestManager instance."""
        # This is the most basic test - can we instantiate the class?
        manager = ManifestManager(temp_manifest_dir)
        assert manager is not None
        assert hasattr(manager, 'logger')
        assert hasattr(manager, 'manifest_dir')
        assert hasattr(manager, 'db_path')
    
    def test_database_file_is_created(self, manifest_manager, temp_manifest_dir):
        """Test: Database file should be created on initialization."""
        expected_db_path = temp_manifest_dir / "extractions.db"
        assert expected_db_path.exists()
        assert manifest_manager.db_path == expected_db_path
    
    def test_can_create_extraction_batch(self, manifest_manager, sample_batch_data):
        """Test: Should be able to create an extraction batch."""
        # Act
        batch = manifest_manager.create_batch(**sample_batch_data)
        
        # Assert
        assert isinstance(batch, ExtractionBatch)
        assert batch.batch_id == sample_batch_data["batch_id"]
        assert batch.table_name == sample_batch_data["table_name"]
        assert batch.status == BatchStatus.PENDING
        assert isinstance(batch.created_at, datetime)
        assert batch.source_query == sample_batch_data["source_query"]
        assert batch.watermark_value == sample_batch_data["watermark_value"]
        assert batch.metadata == sample_batch_data["metadata"]
    
    def test_can_retrieve_batch_by_id(self, manifest_manager, sample_batch_data):
        """Test: Should be able to retrieve a batch by its ID."""
        # Arrange - create a batch
        created_batch = manifest_manager.create_batch(**sample_batch_data)
        
        # Act - retrieve it
        retrieved_batch = manifest_manager.get_batch(created_batch.batch_id)
        
        # Assert
        assert retrieved_batch is not None
        assert retrieved_batch.batch_id == created_batch.batch_id
        assert retrieved_batch.table_name == created_batch.table_name
        assert retrieved_batch.status == created_batch.status
        assert retrieved_batch.source_query == created_batch.source_query
    
    def test_returns_none_for_nonexistent_batch(self, manifest_manager):
        """Test: Should return None when batch doesn't exist."""
        # Act
        result = manifest_manager.get_batch("nonexistent_batch_id")
        
        # Assert
        assert result is None
    
    def test_can_update_batch_status(self, manifest_manager, sample_batch_data):
        """Test: Should be able to update batch status."""
        # Arrange
        batch = manifest_manager.create_batch(**sample_batch_data)
        completion_time = datetime.now()
        
        # Act
        success = manifest_manager.update_batch_status(
            batch_id=batch.batch_id,
            status=BatchStatus.COMPLETED,
            completed_at=completion_time
        )
        
        # Assert
        assert success is True
        
        # Verify the update
        updated_batch = manifest_manager.get_batch(batch.batch_id)
        assert updated_batch.status == BatchStatus.COMPLETED
        assert updated_batch.completed_at is not None
        # Allow for small time differences due to datetime precision
        assert abs((updated_batch.completed_at - completion_time).total_seconds()) < 1
    
    def test_can_update_batch_results(self, manifest_manager, sample_batch_data):
        """Test: Should be able to update batch extraction results."""
        # Arrange
        batch = manifest_manager.create_batch(**sample_batch_data)
        row_count = 1000
        file_path = "/path/to/test_file.parquet"
        file_size = 1024 * 1024  # 1MB
        
        # Act
        success = manifest_manager.update_batch_results(
            batch_id=batch.batch_id,
            row_count=row_count,
            file_path=file_path,
            file_size_bytes=file_size
        )
        
        # Assert
        assert success is True
        
        # Verify the update
        updated_batch = manifest_manager.get_batch(batch.batch_id)
        assert updated_batch.row_count == row_count
        assert updated_batch.file_path == file_path
        assert updated_batch.file_size_bytes == file_size
    
    def test_can_list_batches_for_table(self, manifest_manager):
        """Test: Should be able to list batches for a specific table."""
        # Arrange - create batches for different tables
        table1_batch1 = manifest_manager.create_batch("batch1", "table1")
        table1_batch2 = manifest_manager.create_batch("batch2", "table1")
        table2_batch1 = manifest_manager.create_batch("batch3", "table2")
        
        # Act
        table1_batches = manifest_manager.list_batches(table_name="table1")
        
        # Assert
        assert len(table1_batches) == 2
        batch_ids = [batch.batch_id for batch in table1_batches]
        assert "batch1" in batch_ids
        assert "batch2" in batch_ids
        assert "batch3" not in batch_ids
    
    def test_can_get_latest_batch_for_table(self, manifest_manager):
        """Test: Should be able to get the latest batch for a table."""
        # Arrange - create multiple batches with different times
        import time
        first_batch = manifest_manager.create_batch("batch1", "test_table")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        second_batch = manifest_manager.create_batch("batch2", "test_table")
        
        # Act
        latest_batch = manifest_manager.get_latest_batch("test_table")
        
        # Assert
        assert latest_batch is not None
        assert latest_batch.batch_id == "batch2"  # Should be the most recent
        assert latest_batch.created_at >= first_batch.created_at
    
    def test_can_filter_batches_by_status(self, manifest_manager, sample_batch_data):
        """Test: Should be able to filter batches by status."""
        # Arrange - create batches with different statuses
        pending_batch = manifest_manager.create_batch("pending_batch", "test_table")
        completed_batch = manifest_manager.create_batch("completed_batch", "test_table")
        
        # Update one to completed status
        manifest_manager.update_batch_status(
            batch_id=completed_batch.batch_id,
            status=BatchStatus.COMPLETED,
            completed_at=datetime.now()
        )
        
        # Act
        pending_batches = manifest_manager.list_batches(status=BatchStatus.PENDING)
        completed_batches = manifest_manager.list_batches(status=BatchStatus.COMPLETED)
        
        # Assert
        assert len(pending_batches) >= 1
        assert len(completed_batches) >= 1
        
        pending_ids = [batch.batch_id for batch in pending_batches]
        completed_ids = [batch.batch_id for batch in completed_batches]
        
        assert "pending_batch" in pending_ids
        assert "completed_batch" in completed_ids
        assert "completed_batch" not in pending_ids
        assert "pending_batch" not in completed_ids


@pytest.mark.unit
class TestExtractionBatchDataClass:
    """Test ExtractionBatch data class functionality."""
    
    def test_extraction_batch_required_fields(self):
        """Test: ExtractionBatch should require essential fields."""
        batch = ExtractionBatch(
            batch_id="test_batch",
            table_name="test_table", 
            status=BatchStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert batch.batch_id == "test_batch"
        assert batch.table_name == "test_table"
        assert batch.status == BatchStatus.PENDING
        assert isinstance(batch.created_at, datetime)
    
    def test_extraction_batch_to_dict(self):
        """Test: ExtractionBatch should convert to dictionary."""
        created_time = datetime.now()
        completed_time = datetime.now()
        
        batch = ExtractionBatch(
            batch_id="test_batch",
            table_name="test_table",
            status=BatchStatus.COMPLETED,
            created_at=created_time,
            completed_at=completed_time,
            row_count=1000,
            metadata={"test": "value"}
        )
        
        result_dict = batch.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["batch_id"] == "test_batch"
        assert result_dict["table_name"] == "test_table"
        assert result_dict["status"] == "completed"  # Should be string value
        assert result_dict["row_count"] == 1000
        assert result_dict["metadata"] == {"test": "value"}
        assert "created_at" in result_dict
        assert "completed_at" in result_dict
    
    def test_extraction_batch_from_dict(self):
        """Test: ExtractionBatch should create from dictionary."""
        created_time = datetime.now()
        data = {
            "batch_id": "test_batch",
            "table_name": "test_table",
            "status": "pending",
            "created_at": created_time.isoformat(),
            "completed_at": None,
            "source_query": None,
            "row_count": None,
            "file_path": None,
            "file_size_bytes": None,
            "watermark_value": None,
            "error_message": None,
            "metadata": {"test": "value"}
        }
        
        batch = ExtractionBatch.from_dict(data)
        
        assert batch.batch_id == "test_batch"
        assert batch.table_name == "test_table"
        assert batch.status == BatchStatus.PENDING
        assert isinstance(batch.created_at, datetime)
        assert batch.completed_at is None
        assert batch.metadata == {"test": "value"}


@pytest.mark.unit
class TestBatchStatusEnum:
    """Test BatchStatus enum functionality."""
    
    def test_batch_status_values(self):
        """Test: BatchStatus should have expected string values."""
        assert BatchStatus.PENDING.value == "pending"
        assert BatchStatus.EXTRACTING.value == "extracting"
        assert BatchStatus.COMPLETED.value == "completed"
        assert BatchStatus.FAILED.value == "failed"
        assert BatchStatus.LOADING.value == "loading"
        assert BatchStatus.LOADED.value == "loaded"
        assert BatchStatus.ARCHIVED.value == "archived"
    
    def test_batch_status_string_conversion(self):
        """Test: BatchStatus should work with string values."""
        # This tests that we can create BatchStatus from string values
        assert BatchStatus("pending") == BatchStatus.PENDING
        assert BatchStatus("completed") == BatchStatus.COMPLETED
        assert BatchStatus("failed") == BatchStatus.FAILED


@pytest.mark.unit  
class TestManifestManagerAdvancedFeatures:
    """Test advanced ManifestManager features."""
    
    def test_get_batch_statistics_basic(self, manifest_manager):
        """Test: Should provide basic batch statistics."""
        # Arrange - create some batches
        manifest_manager.create_batch("batch1", "table1")
        batch2 = manifest_manager.create_batch("batch2", "table1") 
        batch3 = manifest_manager.create_batch("batch3", "table2")
        
        # Update one batch with results
        manifest_manager.update_batch_results("batch2", 1000, "/path/file.parquet", 1024)
        manifest_manager.update_batch_status("batch2", BatchStatus.COMPLETED)
        
        # Act
        stats = manifest_manager.get_batch_statistics()
        
        # Assert
        assert isinstance(stats, dict)
        assert "total_batches" in stats
        assert stats["total_batches"] >= 3
        assert "status_counts" in stats
        assert "table_counts" in stats
        assert "total_rows_extracted" in stats
        assert "total_size_bytes" in stats
    
    def test_can_limit_batch_listing(self, manifest_manager):
        """Test: Should support limit and offset in batch listing."""
        # Arrange - create multiple batches
        for i in range(5):
            manifest_manager.create_batch(f"batch_{i}", "test_table")
        
        # Act
        limited_batches = manifest_manager.list_batches(limit=3)
        
        # Assert
        assert len(limited_batches) == 3
        # Should be ordered by created_at DESC (most recent first)
        assert limited_batches[0].batch_id == "batch_4"  # Most recent
    
    def test_update_nonexistent_batch_returns_false(self, manifest_manager):
        """Test: Updating nonexistent batch should return False."""
        # Act
        result = manifest_manager.update_batch_status(
            batch_id="nonexistent",
            status=BatchStatus.COMPLETED
        )
        
        # Assert
        assert result is False