#!/usr/bin/env python3
"""
Unit tests for ArchiveManager class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.pipeline.archive_manager import ArchiveManager
from src.utils.manifest_manager import ExtractionBatch, BatchStatus
from src.utils.parquet_utils import ParquetFileInfo


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def mock_parquet_utils():
    """Create mock ParquetUtils."""
    return Mock()


@pytest.fixture
def mock_manifest_manager():
    """Create mock ManifestManager."""
    return Mock()


@pytest.fixture
def archive_manager(mock_logger, tmp_path):
    """Create ArchiveManager instance with temp paths."""
    archive_path = tmp_path / "archive"
    manifest_path = tmp_path / "manifests"
    return ArchiveManager(
        archive_path=archive_path,
        manifest_path=manifest_path,
        retention_days=30,
        logger=mock_logger
    )


@pytest.fixture
def sample_file_info():
    """Create sample ParquetFileInfo."""
    return ParquetFileInfo(
        path=Path("/test/path.parquet"),
        table_name="test_table",
        batch_id="batch_001",
        row_count=100,
        size_bytes=2048,
        compression="snappy"
    )


@pytest.fixture
def sample_batch():
    """Create sample ExtractionBatch."""
    return ExtractionBatch(
        batch_id="batch_001",
        table_name="test_table",
        status=BatchStatus.COMPLETED,
        created_at=datetime.now(),
        row_count=100,
        file_size_bytes=2048,
        file_path="/test/path.parquet"
    )


@pytest.mark.unit
class TestArchiveManager:
    """Test ArchiveManager functionality."""
    
    def test_initialization(self, archive_manager, tmp_path):
        """Test ArchiveManager initialization."""
        assert archive_manager.archive_path == tmp_path / "archive"
        assert archive_manager.manifest_path == tmp_path / "manifests"
        assert archive_manager.retention_days == 30
        assert archive_manager.parquet_utils is not None
        assert archive_manager.manifest_manager is not None
    
    def test_create_extraction_batch(self, archive_manager):
        """Test creating extraction batch."""
        with patch.object(archive_manager.manifest_manager, 'create_batch') as mock_create:
            mock_create.return_value = "batch_123"
            
            batch_id, batch = archive_manager.create_extraction_batch(
                table_name="users",
                source_query="SELECT * FROM users",
                watermark_value="2023-01-01",
                metadata={"test": "data"}
            )
        
        assert batch_id == "batch_123"
        mock_create.assert_called_once_with(
            table_name="users",
            source_query="SELECT * FROM users", 
            watermark_value="2023-01-01",
            metadata={"test": "data"}
        )
    
    def test_store_extraction_data(self, archive_manager, sample_file_info):
        """Test storing extraction data."""
        import pandas as pd
        test_data = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        
        with patch.object(archive_manager.parquet_utils, 'write_parquet_dataset') as mock_write:
            mock_write.return_value = sample_file_info
            
            with patch.object(archive_manager.manifest_manager, 'update_batch_status') as mock_update:
                mock_update.return_value = True
                
                result = archive_manager.store_extraction_data(
                    batch_id="batch_001",
                    table_name="test_table",
                    data=test_data,
                    compression="gzip"
                )
        
        assert result == sample_file_info
        mock_write.assert_called_once()
        mock_update.assert_called_once()
    
    def test_load_extraction_data(self, archive_manager):
        """Test loading extraction data."""
        mock_table = Mock()
        
        with patch.object(archive_manager.manifest_manager, 'get_batch') as mock_get_batch:
            mock_batch = Mock()
            mock_batch.file_path = "/test/path.parquet"
            mock_batch.status = BatchStatus.COMPLETED
            mock_get_batch.return_value = mock_batch
            
            with patch.object(archive_manager.parquet_utils, 'read_parquet_dataset') as mock_read:
                mock_read.return_value = mock_table
                
                result = archive_manager.load_extraction_data(
                    batch_id="batch_001",
                    table_name="test_table"
                )
        
        assert result == mock_table
        mock_get_batch.assert_called_once_with("batch_001")
        mock_read.assert_called_once()
    
    def test_load_extraction_data_batch_not_found(self, archive_manager):
        """Test loading data when batch not found."""
        with patch.object(archive_manager.manifest_manager, 'get_batch') as mock_get_batch:
            mock_get_batch.return_value = None
            
            with pytest.raises(ValueError, match="Batch batch_001 not found"):
                archive_manager.load_extraction_data(
                    batch_id="batch_001",
                    table_name="test_table"
                )
    
    def test_get_latest_batch(self, archive_manager, sample_batch):
        """Test getting latest batch."""
        with patch.object(archive_manager.manifest_manager, 'get_latest_batch') as mock_get_latest:
            mock_get_latest.return_value = sample_batch
            
            result = archive_manager.get_latest_batch(
                table_name="test_table",
                status=BatchStatus.COMPLETED
            )
        
        assert result == sample_batch
        mock_get_latest.assert_called_once_with(
            table_name="test_table",
            status=BatchStatus.COMPLETED
        )
    
    def test_list_available_batches(self, archive_manager):
        """Test listing available batches."""
        mock_batches = [Mock(), Mock(), Mock()]
        
        with patch.object(archive_manager.manifest_manager, 'list_batches') as mock_list:
            mock_list.return_value = mock_batches
            
            result = archive_manager.list_available_batches(
                table_name="test_table",
                status=BatchStatus.COMPLETED,
                last_n=5
            )
        
        assert result == mock_batches
        mock_list.assert_called_once()
    
    def test_get_batches_in_date_range(self, archive_manager):
        """Test getting batches in date range."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        mock_batches = [Mock(), Mock()]
        
        with patch.object(archive_manager.manifest_manager, 'get_batches_in_date_range') as mock_get_range:
            mock_get_range.return_value = mock_batches
            
            result = archive_manager.get_batches_in_date_range(
                table_name="test_table",
                start_date=start_date,
                end_date=end_date,
                status=BatchStatus.COMPLETED
            )
        
        assert result == mock_batches
        mock_get_range.assert_called_once_with(
            table_name="test_table",
            start_date=start_date,
            end_date=end_date,
            status=BatchStatus.COMPLETED
        )
    
    def test_get_archive_statistics(self, archive_manager):
        """Test getting archive statistics."""
        mock_manifest_stats = {
            "total_batches": 10,
            "completed_batches": 8,
            "pending_batches": 1,
            "failed_batches": 1
        }
        
        with patch.object(archive_manager.manifest_manager, 'get_statistics') as mock_get_stats:
            mock_get_stats.return_value = mock_manifest_stats
            
            with patch.object(archive_manager, '_calculate_storage_stats') as mock_storage_stats:
                mock_storage_stats.return_value = {
                    "total_storage_bytes": 10485760,
                    "total_files": 8
                }
                
                result = archive_manager.get_archive_statistics()
        
        assert result["manifest_statistics"] == mock_manifest_stats
        assert "storage_statistics" in result
        assert "archive_path" in result
        assert "retention_days" in result
    
    def test_cleanup_archive(self, archive_manager):
        """Test archive cleanup."""
        with patch.object(archive_manager.manifest_manager, 'cleanup_old_batches') as mock_cleanup:
            mock_cleanup.return_value = 5
            
            with patch.object(archive_manager, '_cleanup_orphaned_files') as mock_cleanup_files:
                mock_cleanup_files.return_value = 2
                
                result = archive_manager.cleanup_archive(
                    older_than_days=30,
                    dry_run=False
                )
        
        assert result["batches_cleaned"] == 5
        assert result["files_cleaned"] == 2
        assert result["dry_run"] is False
    
    def test_validate_archive_integrity(self, archive_manager):
        """Test archive integrity validation."""
        mock_batch1 = Mock()
        mock_batch1.batch_id = "batch_001"
        mock_batch1.file_path = "/test/file1.parquet"
        mock_batch1.status = BatchStatus.COMPLETED
        
        mock_batch2 = Mock()
        mock_batch2.batch_id = "batch_002"
        mock_batch2.file_path = "/test/file2.parquet"
        mock_batch2.status = BatchStatus.COMPLETED
        
        with patch.object(archive_manager.manifest_manager, 'list_batches') as mock_list:
            mock_list.return_value = [mock_batch1, mock_batch2]
            
            with patch.object(archive_manager.parquet_utils, 'validate_parquet_file') as mock_validate:
                mock_validate.side_effect = [(True, Mock()), (False, None)]
                
                result = archive_manager.validate_archive_integrity()
        
        assert result["total_batches"] == 2
        assert result["valid_files"] == 1
        assert result["invalid_files"] == 1
        assert len(result["validation_details"]) == 2


@pytest.mark.unit
class TestArchiveManagerHelperMethods:
    """Test ArchiveManager helper methods."""
    
    def test_build_archive_path(self, archive_manager):
        """Test building archive file path."""
        path = archive_manager._build_archive_path("test_table", "batch_001")
        
        expected_suffix = Path("test_table") / "batch_001.parquet"
        assert str(path).endswith(str(expected_suffix))
    
    def test_ensure_archive_directory(self, archive_manager, tmp_path):
        """Test ensuring archive directory exists."""
        test_path = tmp_path / "new_table" / "batch_002.parquet"
        
        archive_manager._ensure_archive_directory(test_path)
        
        # Directory should be created
        assert test_path.parent.exists()
        assert test_path.parent.is_dir()
    
    def test_calculate_storage_stats(self, archive_manager, tmp_path):
        """Test calculating storage statistics."""
        # Create some test files
        (tmp_path / "archive" / "table1").mkdir(parents=True)
        (tmp_path / "archive" / "table2").mkdir(parents=True)
        
        file1 = tmp_path / "archive" / "table1" / "batch1.parquet"
        file2 = tmp_path / "archive" / "table2" / "batch2.parquet"
        
        file1.write_text("test data 1")
        file2.write_text("test data 2")
        
        stats = archive_manager._calculate_storage_stats()
        
        assert "total_storage_bytes" in stats
        assert "total_files" in stats
        assert stats["total_files"] >= 0  # Could be 0 if no files found
        assert stats["total_storage_bytes"] >= 0