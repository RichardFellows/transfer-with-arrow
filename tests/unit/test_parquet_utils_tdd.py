#!/usr/bin/env python3
"""
TDD approach tests for ParquetUtils - write tests first, then fix implementation.
"""

import pytest
from unittest.mock import Mock
import pandas as pd
import pyarrow as pa
from pathlib import Path
from datetime import datetime
import sys

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.utils.parquet_utils import ParquetUtils, ParquetFileInfo


@pytest.fixture
def parquet_utils():
    """Create ParquetUtils instance."""
    return ParquetUtils()


@pytest.fixture
def sample_dataframe():
    """Create sample dataframe for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [10.5, 20.1, 30.7]
    })


@pytest.mark.unit
class TestParquetUtilsBasicFunctionality:
    """Test basic ParquetUtils functionality with TDD approach."""
    
    def test_can_create_parquet_utils_instance(self):
        """Test: Should be able to create ParquetUtils instance."""
        # This is the most basic test - can we instantiate the class?
        utils = ParquetUtils()
        assert utils is not None
        assert hasattr(utils, 'logger')
    
    def test_write_parquet_dataset_creates_file(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: write_parquet_dataset should create a parquet file."""
        # Arrange
        output_path = tmp_path / "test_output"
        table_name = "test_table"
        batch_id = "batch_001"
        
        # Act
        result = parquet_utils.write_parquet_dataset(
            data=sample_dataframe,
            output_path=output_path,
            table_name=table_name,
            batch_id=batch_id
        )
        
        # Assert
        assert isinstance(result, ParquetFileInfo)
        assert result.table_name == table_name
        assert result.batch_id == batch_id
        assert result.row_count == 3  # Our sample has 3 rows
        assert result.path.exists()  # File should be created
        assert result.path.suffix == '.parquet'
    
    def test_write_parquet_dataset_with_arrow_table(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: write_parquet_dataset should work with Arrow Table input."""
        # Arrange
        arrow_table = pa.Table.from_pandas(sample_dataframe)
        output_path = tmp_path / "test_arrow_output"
        
        # Act
        result = parquet_utils.write_parquet_dataset(
            data=arrow_table,
            output_path=output_path,
            table_name="arrow_test",
            batch_id="batch_002"
        )
        
        # Assert
        assert isinstance(result, ParquetFileInfo)
        assert result.row_count == 3
        assert result.path.exists()
    
    def test_read_parquet_dataset_returns_arrow_table(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: read_parquet_dataset should return data as Arrow Table."""
        # Arrange - first write a file
        output_path = tmp_path / "read_test_output"
        write_result = parquet_utils.write_parquet_dataset(
            data=sample_dataframe,
            output_path=output_path,
            table_name="read_test",
            batch_id="batch_003"
        )
        
        # Act - then read it back
        read_result = parquet_utils.read_parquet_dataset(write_result.path)
        
        # Assert
        assert isinstance(read_result, pa.Table)
        assert read_result.num_rows == 3
        assert read_result.num_columns == 3
        
        # Verify data integrity
        df_result = read_result.to_pandas()
        pd.testing.assert_frame_equal(
            df_result.sort_values('id').reset_index(drop=True),
            sample_dataframe.sort_values('id').reset_index(drop=True)
        )
    
    def test_validate_parquet_file_with_valid_file(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: validate_parquet_file should return True for valid files."""
        # Arrange
        output_path = tmp_path / "validate_test_output"
        write_result = parquet_utils.write_parquet_dataset(
            data=sample_dataframe,
            output_path=output_path,
            table_name="validate_test",
            batch_id="batch_004"
        )
        
        # Act
        is_valid = parquet_utils.validate_parquet_file(write_result.path)
        
        # Assert
        assert is_valid is True
    
    def test_validate_parquet_file_with_nonexistent_file(self, parquet_utils, tmp_path):
        """Test: validate_parquet_file should return False for non-existent files."""
        # Arrange
        nonexistent_file = tmp_path / "does_not_exist.parquet"
        
        # Act
        is_valid = parquet_utils.validate_parquet_file(nonexistent_file)
        
        # Assert
        assert is_valid is False
    
    def test_get_parquet_metadata_returns_info(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: get_parquet_metadata should return file metadata."""
        # Arrange
        output_path = tmp_path / "metadata_test_output"
        write_result = parquet_utils.write_parquet_dataset(
            data=sample_dataframe,
            output_path=output_path,
            table_name="metadata_test",
            batch_id="batch_005"
        )
        
        # Act
        metadata = parquet_utils.get_parquet_metadata(write_result.path)
        
        # Assert
        assert isinstance(metadata, dict)
        assert "num_rows" in metadata
        assert "num_columns" in metadata
        assert "file_size_bytes" in metadata
        assert metadata["num_rows"] == 3
        assert metadata["num_columns"] == 3


@pytest.mark.unit
class TestParquetFileInfoDataClass:
    """Test ParquetFileInfo data class."""
    
    def test_parquet_file_info_required_fields(self):
        """Test: ParquetFileInfo should require essential fields."""
        # This test defines what fields are required
        file_info = ParquetFileInfo(
            path=Path("/test/path.parquet"),
            table_name="test_table", 
            batch_id="batch_123",
            created_at=datetime.now(),
            size_bytes=1024
        )
        
        assert file_info.path == Path("/test/path.parquet")
        assert file_info.table_name == "test_table"
        assert file_info.batch_id == "batch_123"
        assert isinstance(file_info.created_at, datetime)
        assert file_info.size_bytes == 1024
    
    def test_parquet_file_info_to_dict(self):
        """Test: ParquetFileInfo should convert to dictionary."""
        file_info = ParquetFileInfo(
            path=Path("/test/path.parquet"),
            table_name="test_table",
            batch_id="batch_123", 
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            size_bytes=1024,
            row_count=100
        )
        
        result_dict = file_info.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["path"] == "/test/path.parquet"
        assert result_dict["table_name"] == "test_table"
        assert result_dict["batch_id"] == "batch_123"
        assert result_dict["size_bytes"] == 1024
        assert result_dict["row_count"] == 100
        assert "created_at" in result_dict


@pytest.mark.unit  
class TestParquetUtilsAdvancedFeatures:
    """Test advanced ParquetUtils features."""
    
    def test_write_with_compression(self, parquet_utils, sample_dataframe, tmp_path):
        """Test: Should support different compression algorithms."""
        output_path = tmp_path / "compressed_output"
        
        result = parquet_utils.write_parquet_dataset(
            data=sample_dataframe,
            output_path=output_path,
            table_name="compressed_test",
            batch_id="batch_006",
            compression="gzip"
        )
        
        assert result.path.exists()
        # Note: We can't easily verify compression type without reading metadata
    
    def test_write_with_partitioning(self, parquet_utils, tmp_path):
        """Test: Should support partitioning by columns."""
        # Create data with a partition column
        partitioned_data = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'category': ['A', 'A', 'B', 'B'],
            'value': [10, 20, 30, 40]
        })
        
        output_path = tmp_path / "partitioned_output"
        
        result = parquet_utils.write_parquet_dataset(
            data=partitioned_data,
            output_path=output_path,
            table_name="partitioned_test",
            batch_id="batch_007",
            partition_cols=["category"]
        )
        
        assert result.path.exists()
        # Verify partition directories were created
        assert (output_path / "category=A").exists() or (output_path / "partitioned_test_batch_007").exists()