#!/usr/bin/env python3
"""
TDD tests for ExtractProcessor.
Tests written first to define expected behavior, then implementation follows.
"""

import pytest
pytestmark = pytest.mark.unit
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import tempfile
from pathlib import Path
from datetime import datetime

from src.pipeline.extract_processor import ExtractProcessor
from src.pipeline.config_models import (
    ConfigurationModel, PipelineConfig, PipelineMode, ArchiveConfig, ExtractConfig,
    ConnectionConfig, TableConfig, IncrementalConfig, IncrementalStrategy
)
from src.pipeline.archive_manager import ArchiveManager
from src.utils.parquet_utils import ParquetFileInfo


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
def extract_config(temp_archive_path, temp_manifest_path):
    """Create configuration for extract-only mode."""
    return ConfigurationModel(
        pipeline=PipelineConfig(
            pipeline_mode=PipelineMode.EXTRACT_ONLY,
            chunk_size=1000
        ),
        connections={
            "source": ConnectionConfig(
                connection_string="mssql://user:pass@localhost:1433/testdb",
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
                enabled=True,
                incremental=IncrementalConfig(
                    enabled=True,
                    strategy=IncrementalStrategy.TIMESTAMP,
                    watermark_column="updated_at",
                    initial_value="2023-01-01T00:00:00"
                )
            )
        },
        archive=ArchiveConfig(
            enabled=True,
            storage_path=str(temp_archive_path),
            manifest_path=str(temp_manifest_path),
            compression="snappy"
        ),
        extract=ExtractConfig(),
        verification={},
        logging={}
    )


@pytest.fixture
def mock_archive_manager():
    """Create mock archive manager."""
    mock_manager = Mock(spec=ArchiveManager)
    mock_manager.create_extraction_batch.return_value = ("batch_123", Mock())
    mock_manager.store_extraction_data.return_value = ParquetFileInfo(
        path=Path("/test/path.parquet"),
        table_name="test_table",
        batch_id="batch_123",
        created_at=datetime.now(),
        size_bytes=1024,
        row_count=100
    )
    mock_manager.get_latest_batch.return_value = None
    mock_manager.get_archive_statistics.return_value = {"total_batches": 1}
    return mock_manager


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })


class TestExtractProcessorInitialization:
    """Test ExtractProcessor initialization."""
    
    def test_init_with_archive_manager(self, extract_config, mock_archive_manager):
        """Test: ExtractProcessor should initialize with provided archive manager."""
        # Act
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Assert
        assert processor.config == extract_config
        assert processor.archive_manager == mock_archive_manager
        assert processor.extract_logger is not None
    
    def test_init_creates_archive_manager_when_none_provided(self, extract_config):
        """Test: ExtractProcessor should create archive manager when none provided."""
        # Act
        processor = ExtractProcessor(config=extract_config)
        
        # Assert
        assert processor.archive_manager is not None
        assert processor.config == extract_config
    
    def test_init_creates_table_processor_when_source_available(self, extract_config):
        """Test: ExtractProcessor should create table processor when source connection available."""
        # Act
        with patch('src.pipeline.extract_processor.TableProcessor') as mock_tp:
            processor = ExtractProcessor(config=extract_config)
            
            # Assert
            mock_tp.assert_called_once()
            assert processor.table_processor is not None


class TestExtractAllTables:
    """Test extract_all_tables method."""
    
    def test_extract_all_tables_with_no_specific_tables(self, extract_config, mock_archive_manager):
        """Test: extract_all_tables should extract all enabled tables when no specific tables provided."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        with patch.object(processor, '_extract_single_table') as mock_extract:
            mock_extract.return_value = ("batch_123", ParquetFileInfo(
                path=Path("/test.parquet"), table_name="test", batch_id="batch_123",
                created_at=datetime.now(), size_bytes=512, row_count=50
            ))
            
            # Act
            results = processor.extract_all_tables()
            
            # Assert
            assert len(results) == 2  # Two enabled tables
            assert "test_table" in results
            assert "incremental_table" in results
            assert mock_extract.call_count == 2
    
    def test_extract_all_tables_with_specific_tables(self, extract_config, mock_archive_manager):
        """Test: extract_all_tables should extract only specified tables."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        with patch.object(processor, '_extract_single_table') as mock_extract:
            mock_extract.return_value = ("batch_123", ParquetFileInfo(
                path=Path("/test.parquet"), table_name="test", batch_id="batch_123",
                created_at=datetime.now(), size_bytes=512, row_count=50
            ))
            
            # Act
            results = processor.extract_all_tables(tables=["test_table"])
            
            # Assert
            assert len(results) == 1
            assert "test_table" in results
            assert mock_extract.call_count == 1
    
    def test_extract_all_tables_raises_error_for_invalid_tables(self, extract_config, mock_archive_manager):
        """Test: extract_all_tables should raise error for invalid table names."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Requested tables not found or not enabled"):
            processor.extract_all_tables(tables=["invalid_table"])
    
    def test_extract_all_tables_raises_error_when_no_tables_to_extract(self, extract_config, mock_archive_manager):
        """Test: extract_all_tables should raise error when no tables are enabled."""
        # Arrange
        # Disable all tables
        for table_config in extract_config.tables.values():
            table_config.enabled = False
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="No tables to extract"):
            processor.extract_all_tables()


class TestExtractSingleTable:
    """Test _extract_single_table method."""
    
    def test_extract_single_table_creates_batch_and_stores_data(self, extract_config, mock_archive_manager, sample_dataframe):
        """Test: _extract_single_table should create batch and store extracted data."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = extract_config.tables["test_table"]
        
        # Mock the data extraction method to avoid database connections
        with patch.object(processor, '_extract_with_table_processor', return_value=sample_dataframe) as mock_extract:
            
            # Act
            batch_id, file_info = processor._extract_single_table(
                table_name="test_table",
                table_config=table_config
            )
            
            # Assert
            assert batch_id == "batch_123"
            mock_archive_manager.create_extraction_batch.assert_called_once()
            mock_archive_manager.store_extraction_data.assert_called_once()
            mock_extract.assert_called_once_with(table_config)
    
    def test_extract_single_table_includes_incremental_metadata(self, extract_config, mock_archive_manager, sample_dataframe):
        """Test: _extract_single_table should include incremental metadata for incremental tables."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = extract_config.tables["incremental_table"]
        
        with patch.object(processor, '_extract_with_table_processor', return_value=sample_dataframe):
            
            # Act
            processor._extract_single_table(
                table_name="incremental_table",
                table_config=table_config
            )
            
            # Assert
            call_args = mock_archive_manager.create_extraction_batch.call_args
            metadata = call_args.kwargs["metadata"]
            assert metadata["incremental_enabled"] is True
            assert metadata["watermark_column"] == "updated_at"
            assert metadata["incremental_strategy"] == "timestamp"
    
    def test_extract_single_table_handles_custom_batch_metadata(self, extract_config, mock_archive_manager, sample_dataframe):
        """Test: _extract_single_table should include custom batch metadata."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = extract_config.tables["test_table"]
        custom_metadata = {"custom_key": "custom_value"}
        
        with patch.object(processor, '_extract_with_table_processor', return_value=sample_dataframe):
            
            # Act
            processor._extract_single_table(
                table_name="test_table",
                table_config=table_config,
                batch_metadata=custom_metadata
            )
            
            # Assert
            call_args = mock_archive_manager.create_extraction_batch.call_args
            metadata = call_args.kwargs["metadata"]
            assert metadata["custom_key"] == "custom_value"
            assert metadata["extraction_type"] == "scheduled"


class TestDataExtraction:
    """Test data extraction methods."""
    
    def test_extract_with_table_processor_when_available(self, extract_config, mock_archive_manager, sample_dataframe):
        """Test: Should use table processor when available."""
        # Arrange
        mock_table_processor = Mock()
        mock_source = Mock()
        mock_resource = Mock()
        
        # Mock resource iteration
        mock_resource.__iter__ = Mock(return_value=iter([
            {'id': 1, 'name': 'Alice', 'value': 100},
            {'id': 2, 'name': 'Bob', 'value': 200}
        ]))
        mock_source.resources = {'TestTable': mock_resource}
        mock_table_processor._create_optimized_table_source.return_value = mock_source
        mock_table_processor._apply_incremental_loading.return_value = mock_resource
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        processor.table_processor = mock_table_processor
        
        table_config = extract_config.tables["test_table"]
        
        # Act
        result = processor._extract_with_table_processor(table_config)
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_table_processor._create_optimized_table_source.assert_called_once()
    
    def test_extract_with_dlt_direct_when_no_table_processor(self, extract_config, mock_archive_manager):
        """Test: Should use DLT directly when no table processor available."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        processor.table_processor = None
        
        table_config = extract_config.tables["test_table"]
        
        with patch('src.pipeline.extract_processor.sql_database') as mock_sql_db:
            mock_source = Mock()
            mock_resource = Mock()
            mock_resource.__iter__ = Mock(return_value=iter([
                {'id': 1, 'name': 'Test', 'value': 100}
            ]))
            mock_source.resources = {'TestTable': mock_resource}
            mock_sql_db.return_value = mock_source
            
            # Act
            result = processor._extract_with_dlt_direct(table_config)
            
            # Assert
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            mock_sql_db.assert_called_once()
    
    def test_extract_returns_empty_dataframe_when_no_data(self, extract_config, mock_archive_manager):
        """Test: Should return empty DataFrame when no data extracted."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = extract_config.tables["test_table"]
        
        with patch('src.pipeline.extract_processor.sql_database') as mock_sql_db:
            mock_source = Mock()
            mock_resource = Mock()
            mock_resource.__iter__ = Mock(return_value=iter([]))  # No data
            mock_source.resources = {'TestTable': mock_resource}
            mock_sql_db.return_value = mock_source
            
            # Act
            result = processor._extract_with_dlt_direct(table_config)
            
            # Assert
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_build_source_query_with_custom_sql(self, extract_config, mock_archive_manager):
        """Test: _build_source_query should return custom SQL when provided."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = TableConfig(
            source_table="dbo.Test",
            custom_sql="SELECT * FROM dbo.Test WHERE active = 1"
        )
        
        # Act
        query = processor._build_source_query(table_config)
        
        # Assert
        assert query == "SELECT * FROM dbo.Test WHERE active = 1"
    
    def test_build_source_query_with_where_clause(self, extract_config, mock_archive_manager):
        """Test: _build_source_query should include WHERE clause when provided."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = TableConfig(
            source_table="dbo.Test",
            where_clause="active = 1"
        )
        
        # Act
        query = processor._build_source_query(table_config)
        
        # Assert
        assert query == "SELECT * FROM dbo.Test WHERE active = 1"
    
    def test_build_source_query_basic(self, extract_config, mock_archive_manager):
        """Test: _build_source_query should return basic SELECT for simple table."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = TableConfig(source_table="dbo.Test")
        
        # Act
        query = processor._build_source_query(table_config)
        
        # Assert
        assert query == "SELECT * FROM dbo.Test"
    
    def test_get_current_watermark_returns_none_when_not_incremental(self, extract_config, mock_archive_manager):
        """Test: _get_current_watermark should return None for non-incremental tables."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        table_config = extract_config.tables["test_table"]  # Non-incremental
        
        # Act
        watermark = processor._get_current_watermark(table_config)
        
        # Assert
        assert watermark is None
    
    def test_get_current_watermark_returns_initial_value_when_no_previous_batches(self, extract_config, mock_archive_manager):
        """Test: _get_current_watermark should return initial value when no previous batches."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        mock_archive_manager.get_latest_batch.return_value = None
        table_config = extract_config.tables["incremental_table"]  # Incremental
        
        # Act
        watermark = processor._get_current_watermark(table_config)
        
        # Assert
        assert watermark == "2023-01-01T00:00:00"
    
    def test_get_current_watermark_returns_latest_batch_value(self, extract_config, mock_archive_manager):
        """Test: _get_current_watermark should return latest batch watermark value."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        mock_batch = Mock()
        mock_batch.watermark_value = "2023-06-01T12:00:00"
        mock_archive_manager.get_latest_batch.return_value = mock_batch
        
        table_config = extract_config.tables["incremental_table"]
        
        # Act
        watermark = processor._get_current_watermark(table_config)
        
        # Assert
        assert watermark == "2023-06-01T12:00:00"


class TestValidation:
    """Test validation methods."""
    
    def test_validate_extraction_readiness_success(self, extract_config, mock_archive_manager):
        """Test: validate_extraction_readiness should return ready=True for valid configuration."""
        # Arrange
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        result = processor.validate_extraction_readiness()
        
        # Assert
        assert result["ready"] is True
        assert len(result["issues"]) == 0
    
    def test_validate_extraction_readiness_fails_without_source_connection(self, extract_config, mock_archive_manager):
        """Test: validate_extraction_readiness should fail without source connection."""
        # Arrange
        del extract_config.connections["source"]
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        result = processor.validate_extraction_readiness()
        
        # Assert
        assert result["ready"] is False
        assert "Source connection not configured" in result["issues"]
    
    def test_validate_extraction_readiness_fails_without_archive_enabled(self, extract_config, mock_archive_manager):
        """Test: validate_extraction_readiness should fail when archive not enabled."""
        # Arrange
        extract_config.archive.enabled = False
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        result = processor.validate_extraction_readiness()
        
        # Assert
        assert result["ready"] is False
        assert "Archive not enabled" in result["issues"]
    
    def test_validate_extraction_readiness_fails_without_enabled_tables(self, extract_config, mock_archive_manager):
        """Test: validate_extraction_readiness should fail when no tables are enabled."""
        # Arrange
        for table_config in extract_config.tables.values():
            table_config.enabled = False
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        result = processor.validate_extraction_readiness()
        
        # Assert
        assert result["ready"] is False
        assert "No tables enabled for extraction" in result["issues"]


class TestStatistics:
    """Test statistics methods."""
    
    def test_get_extraction_statistics_returns_archive_stats(self, extract_config, mock_archive_manager):
        """Test: get_extraction_statistics should return archive statistics."""
        # Arrange
        expected_stats = {"total_batches": 5, "total_size": 1024000}
        mock_archive_manager.get_archive_statistics.return_value = expected_stats
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        stats = processor.get_extraction_statistics()
        
        # Assert
        assert stats == expected_stats
        mock_archive_manager.get_archive_statistics.assert_called_once()
    
    def test_get_extraction_statistics_handles_errors_gracefully(self, extract_config, mock_archive_manager):
        """Test: get_extraction_statistics should handle errors gracefully."""
        # Arrange
        mock_archive_manager.get_archive_statistics.side_effect = Exception("Database error")
        
        processor = ExtractProcessor(
            config=extract_config,
            archive_manager=mock_archive_manager
        )
        
        # Act
        stats = processor.get_extraction_statistics()
        
        # Assert
        assert stats == {}  # Should return empty dict on error