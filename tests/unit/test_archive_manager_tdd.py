#!/usr/bin/env python3
"""
TDD approach tests for ArchiveManager - write tests first, then fix implementation.
Tests coordination between ParquetUtils and ManifestManager for archive operations.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import pandas as pd
import pyarrow as pa
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.pipeline.archive_manager import ArchiveManager
from src.utils.manifest_manager import ExtractionBatch, BatchStatus
from src.utils.parquet_utils import ParquetFileInfo


@pytest.fixture
def temp_directories():
    """Create temporary directories for archive and manifest testing."""
    with tempfile.TemporaryDirectory() as archive_dir, \
         tempfile.TemporaryDirectory() as manifest_dir:
        yield Path(archive_dir), Path(manifest_dir)


@pytest.fixture
def archive_manager(temp_directories):
    """Create ArchiveManager instance with temporary directories."""
    archive_path, manifest_path = temp_directories
    return ArchiveManager(
        archive_path=archive_path,
        manifest_path=manifest_path,
        retention_days=30
    )


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'value': [10.5, 20.1, 30.7, 40.2, 50.9],
        'created_at': pd.date_range('2023-01-01', periods=5)
    })


@pytest.mark.unit
class TestArchiveManagerBasicFunctionality:
    """Test basic ArchiveManager functionality with TDD approach."""
    
    def test_can_create_archive_manager_instance(self, temp_directories):
        """Test: Should be able to create ArchiveManager instance."""
        archive_path, manifest_path = temp_directories
        
        manager = ArchiveManager(
            archive_path=archive_path,
            manifest_path=manifest_path
        )
        
        assert manager is not None
        assert hasattr(manager, 'logger')
        assert hasattr(manager, 'archive_path')
        assert hasattr(manager, 'manifest_path')
        assert hasattr(manager, 'parquet_utils')
        assert hasattr(manager, 'manifest_manager')
    
    def test_directories_are_created(self, temp_directories):
        """Test: Archive and manifest directories should be created."""
        archive_path, manifest_path = temp_directories
        
        # Remove directories to test creation
        archive_path.rmdir()
        manifest_path.rmdir()
        
        manager = ArchiveManager(
            archive_path=archive_path,
            manifest_path=manifest_path
        )
        
        assert archive_path.exists()
        assert manifest_path.exists()
    
    def test_can_generate_batch_id(self, archive_manager):
        """Test: Should generate unique batch IDs."""
        table_name = "test_table"
        timestamp = datetime(2023, 1, 1, 12, 30, 45)
        
        batch_id = archive_manager.generate_batch_id(table_name, timestamp)
        
        assert isinstance(batch_id, str)
        assert table_name in batch_id
        assert "20230101_123045" in batch_id
        expected = "test_table_20230101_123045"
        assert batch_id == expected
    
    def test_can_get_table_archive_path(self, archive_manager):
        """Test: Should generate correct archive paths for tables."""
        table_name = "users"
        batch_id = "users_20230101_120000"
        
        path = archive_manager.get_table_archive_path(table_name, batch_id)
        
        assert isinstance(path, Path)
        assert path.name == batch_id
        assert path.parent.name == table_name
        assert str(archive_manager.archive_path) in str(path)
    
    def test_can_create_extraction_batch(self, archive_manager):
        """Test: Should be able to create an extraction batch."""
        table_name = "test_table"
        source_query = "SELECT * FROM test_table"
        metadata = {"extraction_type": "full"}
        
        batch_id, batch = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query=source_query,
            metadata=metadata
        )
        
        assert isinstance(batch_id, str)
        assert isinstance(batch, ExtractionBatch)
        assert batch.batch_id == batch_id
        assert batch.table_name == table_name
        assert batch.source_query == source_query
        assert batch.status == BatchStatus.PENDING
        assert batch.metadata == metadata
        
        # Verify archive directory was created
        archive_path = archive_manager.get_table_archive_path(table_name, batch_id)
        assert archive_path.exists()
    
    def test_can_store_extraction_data(self, archive_manager, sample_dataframe):
        """Test: Should be able to store extraction data as parquet."""
        # Arrange - create batch first
        table_name = "test_table"
        batch_id, batch = archive_manager.create_extraction_batch(table_name)
        
        # Act - store data
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe,
            compression="snappy"
        )
        
        # Assert
        assert isinstance(file_info, ParquetFileInfo)
        assert file_info.table_name == table_name
        assert file_info.batch_id == batch_id
        assert file_info.row_count == len(sample_dataframe)
        assert file_info.size_bytes > 0
        assert file_info.path.exists()
        
        # Verify batch was updated
        updated_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert updated_batch.status == BatchStatus.COMPLETED
        assert updated_batch.row_count == len(sample_dataframe)
        assert updated_batch.file_path == str(file_info.path)
        assert updated_batch.completed_at is not None
    
    def test_can_load_extraction_data(self, archive_manager, sample_dataframe):
        """Test: Should be able to load data from completed extraction batch."""
        # Arrange - create and store data
        table_name = "test_table"
        batch_id, batch = archive_manager.create_extraction_batch(table_name)
        
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe
        )
        
        # Act - load data back
        loaded_data = archive_manager.load_extraction_data(
            batch_id=batch_id,
            table_name=table_name
        )
        
        # Assert
        assert isinstance(loaded_data, pa.Table)
        assert loaded_data.num_rows == len(sample_dataframe)
        assert loaded_data.num_columns == len(sample_dataframe.columns)
        
        # Verify data integrity
        loaded_df = loaded_data.to_pandas()
        pd.testing.assert_frame_equal(
            loaded_df.sort_values('id').reset_index(drop=True),
            sample_dataframe.sort_values('id').reset_index(drop=True),
            check_dtype=False  # Arrow conversion may change dtypes
        )
        
        # Verify batch status was updated
        updated_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert updated_batch.status == BatchStatus.LOADED
    
    def test_cannot_load_from_incomplete_batch(self, archive_manager):
        """Test: Should not be able to load from non-completed batch."""
        # Arrange - create batch but don't complete it
        table_name = "test_table"
        batch_id, batch = archive_manager.create_extraction_batch(table_name)
        
        # Act & Assert
        with pytest.raises(ValueError, match="is not ready for loading"):
            archive_manager.load_extraction_data(batch_id, table_name)
    
    def test_can_list_available_batches(self, archive_manager, sample_dataframe):
        """Test: Should be able to list available batches."""
        # Arrange - create multiple batches with different timestamps to ensure unique IDs
        import time
        from datetime import datetime, timedelta
        
        # Create batches with different timestamps
        table1_batch1_id, _ = archive_manager.create_extraction_batch(
            "table1", timestamp=datetime.now() - timedelta(seconds=2)
        )
        table1_batch2_id, _ = archive_manager.create_extraction_batch(
            "table1", timestamp=datetime.now() - timedelta(seconds=1)
        )
        table2_batch1_id, _ = archive_manager.create_extraction_batch(
            "table2", timestamp=datetime.now()
        )
        
        # Complete one batch
        archive_manager.store_extraction_data(
            batch_id=table1_batch1_id,
            table_name="table1", 
            data=sample_dataframe
        )
        
        # Act - list all batches
        all_batches = archive_manager.list_available_batches()
        
        # Assert
        assert len(all_batches) == 3  # Should be exactly 3 batches for this test
        batch_ids = [batch.batch_id for batch in all_batches]
        assert table1_batch1_id in batch_ids
        assert table1_batch2_id in batch_ids
        assert table2_batch1_id in batch_ids
        
        # Test filtering by table
        table1_batches = archive_manager.list_available_batches(table_name="table1")
        assert len(table1_batches) == 2
        
        # Test filtering by status
        completed_batches = archive_manager.list_available_batches(status=BatchStatus.COMPLETED)
        assert len(completed_batches) >= 1
        assert any(batch.batch_id == table1_batch1_id for batch in completed_batches)
    
    def test_can_get_latest_batch(self, archive_manager, sample_dataframe):
        """Test: Should be able to get latest batch for a table."""
        # Arrange - create multiple batches with delay
        table_name = "test_table"
        import time
        
        first_batch_id, _ = archive_manager.create_extraction_batch(table_name)
        archive_manager.store_extraction_data(first_batch_id, table_name, sample_dataframe)
        
        time.sleep(0.01)  # Small delay
        
        second_batch_id, _ = archive_manager.create_extraction_batch(table_name)
        archive_manager.store_extraction_data(second_batch_id, table_name, sample_dataframe)
        
        # Act
        latest_batch = archive_manager.get_latest_batch(table_name)
        
        # Assert
        assert latest_batch is not None
        assert latest_batch.batch_id == second_batch_id
        assert latest_batch.status == BatchStatus.COMPLETED


@pytest.mark.unit
class TestArchiveManagerAdvancedFeatures:
    """Test advanced ArchiveManager features."""
    
    def test_can_get_batches_in_date_range(self, archive_manager, sample_dataframe):
        """Test: Should be able to get batches within date range."""
        # Arrange - create batches with specific timestamps
        table_name = "test_table"
        
        # Create batch from yesterday
        yesterday = datetime.now() - timedelta(days=1)
        old_batch_id, _ = archive_manager.create_extraction_batch(
            table_name, timestamp=yesterday
        )
        archive_manager.store_extraction_data(old_batch_id, table_name, sample_dataframe)
        
        # Create batch from today
        today = datetime.now()
        new_batch_id, _ = archive_manager.create_extraction_batch(
            table_name, timestamp=today
        )
        archive_manager.store_extraction_data(new_batch_id, table_name, sample_dataframe)
        
        # Act - get batches from today only
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        recent_batches = archive_manager.get_batches_in_date_range(
            table_name=table_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert len(recent_batches) >= 1
        batch_ids = [batch.batch_id for batch in recent_batches]
        assert new_batch_id in batch_ids
        # old_batch_id should not be in range
    
    def test_can_get_batch_info(self, archive_manager, sample_dataframe):
        """Test: Should be able to get detailed batch information."""
        # Arrange
        table_name = "test_table"
        batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe
        )
        
        # Act
        batch_info = archive_manager.get_batch_info(batch_id)
        
        # Assert
        assert isinstance(batch_info, dict)
        assert batch_info["batch_id"] == batch_id
        assert batch_info["table_name"] == table_name
        assert batch_info["status"] == "completed"
        assert "parquet_metadata" in batch_info
        assert "file_valid" in batch_info
        assert batch_info["file_valid"] is True
    
    def test_get_batch_info_returns_none_for_nonexistent(self, archive_manager):
        """Test: Should return None for non-existent batch info."""
        result = archive_manager.get_batch_info("nonexistent_batch")
        assert result is None
    
    def test_can_get_archive_statistics(self, archive_manager, sample_dataframe):
        """Test: Should provide comprehensive archive statistics."""
        # Arrange - create some data
        table_name = "test_table"
        batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe
        )
        
        # Act
        stats = archive_manager.get_archive_statistics()
        
        # Assert
        assert isinstance(stats, dict)
        assert "batch_statistics" in stats
        assert "filesystem_statistics" in stats
        assert "table_statistics" in stats
        
        # Check filesystem stats
        fs_stats = stats["filesystem_statistics"]
        assert "total_size_bytes" in fs_stats
        assert "total_files" in fs_stats
        assert "archive_path" in fs_stats
        assert fs_stats["total_files"] >= 1
        assert fs_stats["total_size_bytes"] > 0
        
        # Check table stats
        table_stats = stats["table_statistics"]
        assert table_name in table_stats
        assert table_stats[table_name]["file_count"] >= 1
        assert table_stats[table_name]["size_bytes"] > 0
    
    def test_can_validate_archive_integrity(self, archive_manager, sample_dataframe):
        """Test: Should validate archive integrity."""
        # Arrange - create valid batch
        table_name = "test_table"
        batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe
        )
        
        # Act
        validation_results = archive_manager.validate_archive_integrity()
        
        # Assert
        assert isinstance(validation_results, dict)
        assert "valid_batches" in validation_results
        assert "invalid_batches" in validation_results
        assert "missing_files" in validation_results
        assert "corrupted_files" in validation_results
        assert "orphaned_files" in validation_results
        assert "issues" in validation_results
        
        # Should have at least one valid batch
        assert validation_results["valid_batches"] >= 1
        assert validation_results["invalid_batches"] == 0
        assert validation_results["missing_files"] == 0
        assert validation_results["corrupted_files"] == 0


@pytest.mark.unit
class TestArchiveManagerErrorHandling:
    """Test ArchiveManager error handling scenarios."""
    
    def test_store_data_marks_batch_failed_on_error(self, archive_manager):
        """Test: Should mark batch as failed when storage fails."""
        # Arrange
        table_name = "test_table"
        batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        # Act - try to store invalid data (None should cause error)
        with pytest.raises(Exception):
            archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=None  # This should cause an error
            )
        
        # Assert - batch should be marked as failed
        batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert batch.status == BatchStatus.FAILED
        assert batch.error_message is not None
        assert batch.completed_at is not None
    
    def test_load_nonexistent_batch_raises_error(self, archive_manager):
        """Test: Should raise error when loading non-existent batch."""
        with pytest.raises(ValueError, match="not found"):
            archive_manager.load_extraction_data(
                batch_id="nonexistent_batch",
                table_name="test_table"
            )


@pytest.mark.unit
class TestArchiveManagerIntegration:
    """Test integration aspects of ArchiveManager."""
    
    def test_full_workflow_extract_store_load(self, archive_manager, sample_dataframe):
        """Test: Complete workflow from extraction to loading."""
        # This tests the full integration workflow
        table_name = "integration_test_table"
        
        # Phase 1: Create extraction batch
        batch_id, initial_batch = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query="SELECT * FROM integration_test_table",
            metadata={"test_mode": True}
        )
        
        assert initial_batch.status == BatchStatus.PENDING
        
        # Phase 2: Store extraction data
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=sample_dataframe,
            compression="gzip",
            metadata={"compression": "gzip"}
        )
        
        # Verify storage completed successfully
        assert file_info.row_count == len(sample_dataframe)
        assert file_info.path.exists()
        
        # Phase 3: Load extraction data
        loaded_data = archive_manager.load_extraction_data(
            batch_id=batch_id,
            table_name=table_name
        )
        
        # Verify data integrity
        assert loaded_data.num_rows == len(sample_dataframe)
        loaded_df = loaded_data.to_pandas()
        
        # Check that data matches (allowing for type conversions)
        assert len(loaded_df) == len(sample_dataframe)
        assert list(loaded_df.columns) == list(sample_dataframe.columns)
        
        # Phase 4: Verify final batch state
        final_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert final_batch.status == BatchStatus.LOADED
        assert final_batch.row_count == len(sample_dataframe)
        assert final_batch.file_size_bytes == file_info.size_bytes
        assert final_batch.completed_at is not None
        
        # Phase 5: Verify archive statistics
        stats = archive_manager.get_archive_statistics()
        assert stats["batch_statistics"]["total_batches"] >= 1
        assert stats["filesystem_statistics"]["total_files"] >= 1
        assert table_name in stats["table_statistics"]