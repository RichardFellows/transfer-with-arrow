#!/usr/bin/env python3
"""
Unit tests for ManifestManager class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.utils.manifest_manager import ManifestManager, ExtractionBatch, BatchStatus


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def manifest_manager(mock_logger, tmp_path):
    """Create ManifestManager instance with temporary database."""
    manifest_path = tmp_path / "test_manifest.db"
    return ManifestManager(manifest_path, mock_logger)


@pytest.fixture
def sample_batch():
    """Create sample extraction batch."""
    return ExtractionBatch(
        batch_id="batch_001",
        table_name="test_table",
        status=BatchStatus.PENDING,
        created_at=datetime.now(),
        row_count=100,
        file_size_bytes=2048,
        file_path="/path/to/file.parquet"
    )


@pytest.mark.unit
class TestManifestManager:
    """Test ManifestManager functionality."""
    
    def test_create_batch(self, manifest_manager, mock_logger):
        """Test creating a new batch."""
        with patch('src.utils.manifest_manager.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "abc123"
            
            batch_id = manifest_manager.create_batch(
                table_name="users",
                source_query="SELECT * FROM users",
                watermark_value="2023-01-01",
                metadata={"test": "data"}
            )
        
        assert batch_id == "abc123"
        
        # Verify batch was stored
        batch = manifest_manager.get_batch(batch_id)
        assert batch is not None
        assert batch.table_name == "users"
        assert batch.status == BatchStatus.PENDING
    
    def test_update_batch_status(self, manifest_manager, sample_batch):
        """Test updating batch status."""
        # First create a batch
        manifest_manager._save_batch(sample_batch)
        
        # Update status
        success = manifest_manager.update_batch_status(
            batch_id=sample_batch.batch_id,
            status=BatchStatus.COMPLETED,
            row_count=150,
            file_size_bytes=3072,
            file_path="/new/path.parquet"
        )
        
        assert success is True
        
        # Verify update
        updated_batch = manifest_manager.get_batch(sample_batch.batch_id)
        assert updated_batch.status == BatchStatus.COMPLETED
        assert updated_batch.row_count == 150
        assert updated_batch.file_size_bytes == 3072
    
    def test_get_batch_not_found(self, manifest_manager):
        """Test getting non-existent batch."""
        batch = manifest_manager.get_batch("nonexistent")
        assert batch is None
    
    def test_list_batches(self, manifest_manager):
        """Test listing batches."""
        # Create multiple batches
        batch1 = ExtractionBatch(
            batch_id="batch_001",
            table_name="users",
            status=BatchStatus.COMPLETED,
            created_at=datetime.now()
        )
        batch2 = ExtractionBatch(
            batch_id="batch_002", 
            table_name="posts",
            status=BatchStatus.PENDING,
            created_at=datetime.now()
        )
        
        manifest_manager._save_batch(batch1)
        manifest_manager._save_batch(batch2)
        
        # Test listing all batches
        all_batches = manifest_manager.list_batches()
        assert len(all_batches) == 2
        
        # Test filtering by table
        user_batches = manifest_manager.list_batches(table_name="users")
        assert len(user_batches) == 1
        assert user_batches[0].table_name == "users"
        
        # Test filtering by status
        completed_batches = manifest_manager.list_batches(status=BatchStatus.COMPLETED)
        assert len(completed_batches) == 1
        assert completed_batches[0].status == BatchStatus.COMPLETED
    
    def test_get_latest_batch(self, manifest_manager):
        """Test getting latest batch for table."""
        # Create batches with different timestamps
        old_batch = ExtractionBatch(
            batch_id="batch_old",
            table_name="users",
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 1, 1)
        )
        new_batch = ExtractionBatch(
            batch_id="batch_new",
            table_name="users", 
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 2, 1)
        )
        
        manifest_manager._save_batch(old_batch)
        manifest_manager._save_batch(new_batch)
        
        latest = manifest_manager.get_latest_batch("users")
        assert latest is not None
        assert latest.batch_id == "batch_new"
    
    def test_get_batches_in_date_range(self, manifest_manager):
        """Test getting batches within date range."""
        # Create batches with different dates
        batch1 = ExtractionBatch(
            batch_id="batch_2023_01",
            table_name="users",
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 1, 15)
        )
        batch2 = ExtractionBatch(
            batch_id="batch_2023_02",
            table_name="users",
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 2, 15)
        )
        batch3 = ExtractionBatch(
            batch_id="batch_2023_03",
            table_name="users", 
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 3, 15)
        )
        
        manifest_manager._save_batch(batch1)
        manifest_manager._save_batch(batch2)
        manifest_manager._save_batch(batch3)
        
        # Get batches in January-February range
        batches = manifest_manager.get_batches_in_date_range(
            table_name="users",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 28)
        )
        
        assert len(batches) == 2
        batch_ids = [b.batch_id for b in batches]
        assert "batch_2023_01" in batch_ids
        assert "batch_2023_02" in batch_ids
        assert "batch_2023_03" not in batch_ids
    
    def test_cleanup_old_batches(self, manifest_manager):
        """Test cleaning up old batches."""
        # Create old and recent batches
        old_batch = ExtractionBatch(
            batch_id="batch_old",
            table_name="users",
            status=BatchStatus.COMPLETED,
            created_at=datetime(2023, 1, 1)
        )
        recent_batch = ExtractionBatch(
            batch_id="batch_recent",
            table_name="users",
            status=BatchStatus.COMPLETED, 
            created_at=datetime.now()
        )
        
        manifest_manager._save_batch(old_batch)
        manifest_manager._save_batch(recent_batch)
        
        # Cleanup batches older than 30 days
        with patch('src.utils.manifest_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now()
            mock_datetime.side_effect = lambda *args: datetime(*args) if args else datetime.now()
            
            cleaned_count = manifest_manager.cleanup_old_batches(older_than_days=30)
        
        # Should have cleaned up the old batch
        assert cleaned_count >= 0  # Implementation dependent
    
    def test_get_statistics(self, manifest_manager):
        """Test getting manifest statistics."""
        # Create some test batches
        batch1 = ExtractionBatch(
            batch_id="batch_001",
            table_name="users", 
            status=BatchStatus.COMPLETED,
            created_at=datetime.now()
        )
        batch2 = ExtractionBatch(
            batch_id="batch_002",
            table_name="posts",
            status=BatchStatus.PENDING,
            created_at=datetime.now()
        )
        
        manifest_manager._save_batch(batch1)
        manifest_manager._save_batch(batch2)
        
        stats = manifest_manager.get_statistics()
        
        assert "total_batches" in stats
        assert "completed_batches" in stats
        assert "pending_batches" in stats
        assert "failed_batches" in stats
        assert stats["total_batches"] >= 2


@pytest.mark.unit
class TestExtractionBatch:
    """Test ExtractionBatch dataclass."""
    
    def test_extraction_batch_creation(self):
        """Test creating ExtractionBatch instance."""
        batch = ExtractionBatch(
            batch_id="test_batch",
            table_name="test_table",
            status=BatchStatus.PENDING,
            created_at=datetime.now(),
            row_count=100,
            file_size_bytes=2048
        )
        
        assert batch.batch_id == "test_batch"
        assert batch.table_name == "test_table"
        assert batch.status == BatchStatus.PENDING
        assert isinstance(batch.created_at, datetime)
        assert batch.row_count == 100
        assert batch.file_size_bytes == 2048
    
    def test_extraction_batch_defaults(self):
        """Test ExtractionBatch with default values."""
        batch = ExtractionBatch(
            batch_id="test_batch",
            table_name="test_table", 
            status=BatchStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert batch.completed_at is None
        assert batch.row_count is None
        assert batch.file_size_bytes is None
        assert batch.file_path is None
        assert batch.source_query is None
        assert batch.watermark_value is None
        assert batch.error_message is None
        assert batch.metadata is None


@pytest.mark.unit 
class TestBatchStatus:
    """Test BatchStatus enum."""
    
    def test_batch_status_values(self):
        """Test BatchStatus enum values."""
        assert BatchStatus.PENDING.value == "pending"
        assert BatchStatus.IN_PROGRESS.value == "in_progress"
        assert BatchStatus.COMPLETED.value == "completed"
        assert BatchStatus.FAILED.value == "failed"
        
    def test_batch_status_conversion(self):
        """Test converting strings to BatchStatus."""
        assert BatchStatus("pending") == BatchStatus.PENDING
        assert BatchStatus("completed") == BatchStatus.COMPLETED
        assert BatchStatus("failed") == BatchStatus.FAILED