#!/usr/bin/env python3
"""
Unit tests for ParquetUtils class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pyarrow as pa
from pathlib import Path
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.utils.parquet_utils import ParquetUtils, ParquetFileInfo


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def parquet_utils(mock_logger):
    """Create ParquetUtils instance with mock logger."""
    return ParquetUtils(mock_logger)


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['A', 'B', 'C', 'D', 'E'],
        'value': [10.5, 20.1, 30.7, 40.2, 50.9],
        'created_at': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
    })


@pytest.fixture
def sample_arrow_table(sample_dataframe):
    """Create sample Arrow table for testing."""
    return pa.Table.from_pandas(sample_dataframe)


@pytest.mark.unit
class TestParquetUtils:
    """Test ParquetUtils functionality."""
    
    def test_write_parquet_dataset_basic(self, parquet_utils, sample_dataframe, tmp_path):
        """Test basic parquet dataset writing."""
        output_path = tmp_path / "test_output.parquet"
        
        with patch('pyarrow.parquet.write_table') as mock_write:
            # Mock the write operation
            mock_write.return_value = None
            
            # Mock path.stat() for file size
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                result = parquet_utils.write_parquet_dataset(
                    data=sample_dataframe,
                    output_path=output_path,
                    table_name="test_table",
                    batch_id="batch_001"
                )
        
        # Verify result
        assert isinstance(result, ParquetFileInfo)
        assert result.path == output_path
        assert result.table_name == "test_table"
        assert result.batch_id == "batch_001"
        assert result.row_count == 5
        assert result.size_bytes == 1024
        
        # Verify write was called
        mock_write.assert_called_once()
    
    def test_write_parquet_dataset_with_partitioning(self, parquet_utils, sample_dataframe, tmp_path):
        """Test parquet dataset writing with partitioning."""
        output_path = tmp_path / "partitioned_output"
        
        with patch('pyarrow.parquet.write_to_dataset') as mock_write_dataset:
            mock_write_dataset.return_value = None
            
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 2048
                
                result = parquet_utils.write_parquet_dataset(
                    data=sample_dataframe,
                    output_path=output_path,
                    table_name="test_table",
                    batch_id="batch_002",
                    partition_cols=["created_at"],
                    compression="gzip"
                )
        
        # Verify partitioned write was called
        mock_write_dataset.assert_called_once()
        assert result.compression == "gzip"
    
    def test_read_parquet_dataset(self, parquet_utils, tmp_path):
        """Test reading parquet dataset."""
        file_path = tmp_path / "test_read.parquet"
        
        # Mock the read operation
        with patch('pyarrow.parquet.read_table') as mock_read:
            mock_table = Mock()
            mock_table.num_rows = 10
            mock_table.schema = Mock()
            mock_read.return_value = mock_table
            
            result = parquet_utils.read_parquet_dataset(file_path)
        
        # Verify read was called and result returned
        mock_read.assert_called_once_with(str(file_path))
        assert result == mock_table
    
    def test_validate_parquet_file(self, parquet_utils, tmp_path):
        """Test parquet file validation."""
        file_path = tmp_path / "test_validate.parquet"
        
        with patch('pyarrow.parquet.read_metadata') as mock_metadata:
            mock_meta = Mock()
            mock_meta.num_rows = 5
            mock_meta.schema = Mock()
            mock_metadata.return_value = mock_meta
            
            is_valid, metadata = parquet_utils.validate_parquet_file(file_path)
        
        assert is_valid is True
        assert metadata == mock_meta
        mock_metadata.assert_called_once()
    
    def test_validate_parquet_file_invalid(self, parquet_utils, tmp_path):
        """Test parquet file validation with invalid file."""
        file_path = tmp_path / "invalid.parquet"
        
        with patch('pyarrow.parquet.read_metadata') as mock_metadata:
            mock_metadata.side_effect = Exception("Invalid file")
            
            is_valid, metadata = parquet_utils.validate_parquet_file(file_path)
        
        assert is_valid is False
        assert metadata is None
    
    def test_get_file_info(self, parquet_utils, tmp_path):
        """Test getting file information."""
        file_path = tmp_path / "test_info.parquet"
        file_path.touch()  # Create empty file
        
        with patch('pyarrow.parquet.read_metadata') as mock_metadata:
            mock_meta = Mock()
            mock_meta.num_rows = 15
            mock_meta.schema.names = ['col1', 'col2', 'col3']
            mock_metadata.return_value = mock_meta
            
            info = parquet_utils.get_file_info(file_path)
        
        assert info["file_path"] == str(file_path)
        assert info["row_count"] == 15
        assert info["column_count"] == 3
        assert "file_size_bytes" in info
    
    def test_cleanup_files(self, parquet_utils, tmp_path):
        """Test file cleanup functionality."""
        # Create test files
        file1 = tmp_path / "file1.parquet"
        file2 = tmp_path / "file2.parquet"
        file1.touch()
        file2.touch()
        
        files_to_clean = [file1, file2]
        
        cleaned_count = parquet_utils.cleanup_files(files_to_clean)
        
        assert cleaned_count == 2
        assert not file1.exists()
        assert not file2.exists()


@pytest.mark.unit 
class TestParquetFileInfo:
    """Test ParquetFileInfo dataclass."""
    
    def test_parquet_file_info_creation(self):
        """Test creating ParquetFileInfo instance."""
        info = ParquetFileInfo(
            path=Path("/test/path.parquet"),
            table_name="test_table",
            batch_id="batch_123",
            row_count=100,
            size_bytes=2048,
            compression="snappy"
        )
        
        assert info.path == Path("/test/path.parquet")
        assert info.table_name == "test_table"
        assert info.batch_id == "batch_123"
        assert info.row_count == 100
        assert info.size_bytes == 2048
        assert info.compression == "snappy"
    
    def test_parquet_file_info_defaults(self):
        """Test ParquetFileInfo with default values."""
        info = ParquetFileInfo(
            path=Path("/test/path.parquet"),
            table_name="test_table",
            batch_id="batch_123"
        )
        
        assert info.row_count is None
        assert info.size_bytes is None
        assert info.compression is None
        assert info.partition_cols is None
        assert info.metadata is None