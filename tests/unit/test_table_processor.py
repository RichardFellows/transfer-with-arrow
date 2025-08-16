#!/usr/bin/env python3
"""
Comprehensive unit tests for TableProcessor to improve coverage.
These tests are designed to fail initially and then be made to pass by implementing the functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.pipeline.table_processor import TableProcessor
from src.pipeline.config_models import (
    ConfigurationModel, TableConfig, IncrementalConfig, ConnectionConfig,
    PipelineConfig, VerificationConfig, LoggingConfig,
    IncrementalStrategy, WriteDisposition, BackendType
)


@pytest.fixture
def basic_config():
    """Create a basic configuration for testing."""
    return ConfigurationModel(
        pipeline=PipelineConfig(
            name="test_pipeline",
            dataset_name="test_data",
            backend=BackendType.PYARROW
        ),
        connections={
            "source": ConnectionConfig(connection_string="sqlite:///source.db"),
            "destination": ConnectionConfig(connection_string="sqlite:///dest.db")
        },
        tables={
            "TestTable": TableConfig(
                source_table="dbo.TestTable",
                destination_table="test_table",
                enabled=True
            )
        },
        verification=VerificationConfig(),
        logging=LoggingConfig()
    )


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.mark.unit
class TestTableProcessorCustomSQL:
    """Test custom SQL functionality - currently uncovered lines 109-110, 131."""
    
    def test_custom_sql_table_processing(self, basic_config, mock_logger):
        """Test processing table with custom SQL - should use custom SQL path."""
        # Create table config with custom SQL
        table_config = TableConfig(
            source_table="dbo.TestTable",
            destination_table="custom_test",
            custom_sql="SELECT id, name FROM dbo.TestTable WHERE active = 1",
            enabled=True
        )
        
        with patch('src.utils.logging_setup.get_logger') as mock_get_logger, \
             patch('src.pipeline.table_processor.sql_database') as mock_sql_db, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt, \
             patch('src.pipeline.table_processor.SchemaAnalyzer') as mock_schema_analyzer:
            
            # Setup logger mock BEFORE creating processor
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            # Setup mocks
            mock_source = Mock()
            mock_sql_db.return_value = mock_source
            mock_source.with_resources.return_value = mock_source
            
            mock_pipeline = Mock()
            mock_dlt.pipeline.return_value = mock_pipeline
            mock_dlt.destinations.sqlalchemy.return_value = "mock_dest"
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Verify the custom SQL is set
            assert table_config.custom_sql is not None
            assert table_config.custom_sql == "SELECT id, name FROM dbo.TestTable WHERE active = 1"
            
            # This should trigger custom SQL path 
            source = processor._create_table_source("TestTable", table_config)
            
            # Verify custom SQL was used
            assert mock_source.with_resources.called
            # Should log custom SQL usage (line 110)
            mock_table_logger.info.assert_called_with("Using custom SQL for TestTable")


@pytest.mark.unit 
class TestTableProcessorIncrementalLoading:
    """Test incremental loading functionality - currently uncovered lines 70, 153-208."""
    
    def test_incremental_loading_timestamp_strategy(self, basic_config, mock_logger):
        """Test timestamp-based incremental loading."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            destination_table="test_table",
            incremental=IncrementalConfig(
                enabled=True,
                strategy=IncrementalStrategy.TIMESTAMP,
                watermark_column="updated_at",
                initial_value="2023-01-01T00:00:00"
            ),
            enabled=True
        )
        
        with patch('src.pipeline.table_processor.sql_database') as mock_sql_db, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt:
            
            mock_source = Mock()
            mock_sql_db.return_value = mock_source
            mock_source.with_resources.return_value = mock_source
            
            # Mock resource with apply_hints method
            mock_resource = Mock()
            mock_source.test_table = mock_resource
            
            mock_pipeline = Mock()
            mock_dlt.pipeline.return_value = mock_pipeline
            mock_dlt.destinations.sqlalchemy.return_value = "mock_dest"
            mock_dlt.sources.incremental.return_value = "mock_incremental"
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # This should trigger incremental loading path (line 70)
            with patch.object(processor, '_apply_incremental_loading') as mock_apply:
                mock_apply.return_value = mock_source
                result = processor.process_table("TestTable", table_config)
                
                # Should apply incremental loading
                mock_apply.assert_called_once_with(mock_source, table_config)
    
    def test_incremental_loading_sequence_strategy(self, basic_config, mock_logger):
        """Test sequence-based incremental loading."""
        table_config = TableConfig(
            source_table="dbo.TestTable", 
            incremental=IncrementalConfig(
                enabled=True,
                strategy=IncrementalStrategy.SEQUENCE,
                watermark_column="id",
                initial_value="0"
            ),
            enabled=True
        )
        
        with patch('src.pipeline.table_processor.sql_database') as mock_sql_db, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt:
            
            mock_source = Mock()
            mock_sql_db.return_value = mock_source
            
            # Mock resource access patterns (lines 179-191)
            mock_resource = Mock()
            mock_source.testtable = mock_resource  # lowercase version
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Should fail initially - incremental loading not fully implemented
            result = processor._apply_incremental_loading(mock_source, table_config)
            
            # Should call apply_hints on resource (line 194-199)
            mock_resource.apply_hints.assert_called()
    
    def test_incremental_loading_resource_not_found(self, basic_config, mock_logger):
        """Test incremental loading when resource is not found - error path lines 186-191."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            incremental=IncrementalConfig(
                enabled=True,
                strategy=IncrementalStrategy.TIMESTAMP,
                watermark_column="updated_at",
                initial_value="2023-01-01T00:00:00"
            ),
            enabled=True
        )
        
        with patch('src.utils.logging_setup.get_logger') as mock_get_logger, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt:
            
            # Setup logger mock BEFORE creating processor
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Create a source mock that will trigger the ValueError path
            mock_source = Mock(spec=[])  # Source with no attributes
            # Manually ensure the hasattr checks will fail
            type(mock_source).TestTable = property(lambda x: None)
            type(mock_source).testtable = property(lambda x: None) 
            type(mock_source).resources = property(lambda x: {})
            
            # Should catch the ValueError and log error (lines 203-206)
            result = processor._apply_incremental_loading(mock_source, table_config)
            
            # Should log error about resource not found
            assert mock_table_logger.error.called
            assert mock_table_logger.warning.called
            assert result == mock_source  # Should return original source
    
    def test_incremental_loading_configuration_error(self, basic_config, mock_logger):
        """Test incremental loading when configuration fails - error handling lines 203-207."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            destination_table="test_table",
            incremental=IncrementalConfig(
                enabled=True,
                strategy=IncrementalStrategy.TIMESTAMP,
                watermark_column="updated_at", 
                initial_value="2023-01-01T00:00:00"
            ),
            enabled=True
        )
        
        with patch('src.utils.logging_setup.get_logger') as mock_get_logger, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt:
            
            # Setup logger mock BEFORE creating processor
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            mock_source = Mock()
            mock_resource = Mock()
            # Set up the source to have the resource attribute using destination table name
            # The table_config.destination_table is "test_table" from basic_config fixture
            mock_source.test_table = mock_resource
            
            # Mock DLT incremental to avoid import issues
            mock_dlt.sources.incremental.return_value = "mock_incremental"
            
            # Make apply_hints raise an exception
            mock_resource.apply_hints.side_effect = Exception("DLT configuration error")
            
            # Should catch exception and log error (lines 203-207)
            result = processor._apply_incremental_loading(mock_source, table_config)
            
            # Should log error and warning
            assert mock_table_logger.error.called
            assert mock_table_logger.warning.called
            assert result == mock_source  # Should return original source


@pytest.mark.unit
class TestTableProcessorInitialValueConversion:
    """Test initial value conversion - currently uncovered lines 221-255."""
    
    def test_convert_timestamp_initial_value_iso_format(self, basic_config, mock_logger):
        """Test converting ISO format timestamp initial value."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should convert ISO string to datetime (lines 227-228)
        result = processor._convert_initial_value(
            "2023-01-01T00:00:00Z", 
            IncrementalStrategy.TIMESTAMP
        )
        assert isinstance(result, datetime)
    
    def test_convert_timestamp_initial_value_other_format(self, basic_config, mock_logger):
        """Test converting non-ISO timestamp with dateutil - lines 231-232."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        with patch('dateutil.parser.parse') as mock_parse:
            mock_parse.return_value = datetime(2023, 1, 1)
            
            # Should fall back to dateutil.parser (lines 231-232)
            result = processor._convert_initial_value(
                "Jan 1, 2023", 
                IncrementalStrategy.TIMESTAMP
            )
            mock_parse.assert_called_once_with("Jan 1, 2023")
    
    def test_convert_timestamp_invalid_value(self, basic_config, mock_logger):
        """Test invalid timestamp value - error line 236."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should raise ValueError for invalid timestamp (line 236)
        with pytest.raises(ValueError, match="Invalid timestamp initial value"):
            processor._convert_initial_value(
                123, 
                IncrementalStrategy.TIMESTAMP
            )
    
    def test_convert_sequence_initial_value_string_int(self, basic_config, mock_logger):
        """Test converting string integer for sequence - lines 246-247."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should convert string to int (lines 246-247)
        result = processor._convert_initial_value(
            "123",
            IncrementalStrategy.SEQUENCE
        )
        assert result == 123
        assert isinstance(result, int)
    
    def test_convert_sequence_initial_value_string_float(self, basic_config, mock_logger):
        """Test converting string float for sequence - lines 244-245."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should convert string to float (lines 244-245)
        result = processor._convert_initial_value(
            "123.45",
            IncrementalStrategy.SEQUENCE
        )
        assert result == 123.45
        assert isinstance(result, float)
    
    def test_convert_sequence_invalid_string(self, basic_config, mock_logger):
        """Test invalid sequence string value - error line 249."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should raise ValueError for invalid sequence string (line 249)
        with pytest.raises(ValueError, match="Invalid sequence initial value"):
            processor._convert_initial_value(
                "not_a_number",
                IncrementalStrategy.SEQUENCE
            )
    
    def test_convert_sequence_invalid_type(self, basic_config, mock_logger):
        """Test invalid sequence value type - error line 251."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should raise ValueError for invalid sequence type (line 251)
        with pytest.raises(ValueError, match="Invalid sequence initial value"):
            processor._convert_initial_value(
                [],
                IncrementalStrategy.SEQUENCE
            )
    
    def test_convert_custom_initial_value(self, basic_config, mock_logger):
        """Test custom strategy initial value - line 255."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should return value as-is for custom strategy (line 255)
        custom_value = {"custom": "data"}
        result = processor._convert_initial_value(
            custom_value,
            IncrementalStrategy.CUSTOM
        )
        assert result == custom_value


@pytest.mark.unit
class TestTableProcessorSchemaInfo:
    """Test schema information retrieval - currently uncovered lines 268-294."""
    
    def test_get_table_schema_info_basic(self, basic_config, mock_logger):
        """Test getting basic schema information."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            destination_table="test_table",
            disposition=WriteDisposition.REPLACE,
            primary_key=["id"],
            enabled=True
        )
        
        with patch.object(TableProcessor, '_create_table_source') as mock_create:
            mock_create.return_value = Mock()
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Should return schema info dict (lines 272-289)
            result = processor.get_table_schema_info("TestTable", table_config)
            
            assert result["table_name"] == "TestTable"
            assert result["source_table"] == "dbo.TestTable"
            assert result["destination_table"] == "test_table"
            assert result["disposition"] == "replace"
            assert result["primary_key"] == ["id"]
            assert result["incremental_enabled"] is False
    
    def test_get_table_schema_info_with_incremental(self, basic_config, mock_logger):
        """Test schema info with incremental config - lines 283-288."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            incremental=IncrementalConfig(
                enabled=True,
                strategy=IncrementalStrategy.TIMESTAMP,
                watermark_column="updated_at",
                initial_value="2023-01-01T00:00:00"
            ),
            enabled=True
        )
        
        with patch.object(TableProcessor, '_create_table_source') as mock_create:
            mock_create.return_value = Mock()
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Should include incremental info (lines 283-288)
            result = processor.get_table_schema_info("TestTable", table_config)
            
            assert result["incremental_enabled"] is True
            assert result["incremental_strategy"] == "timestamp"
            assert result["watermark_column"] == "updated_at"
            assert result["initial_value"] == "2023-01-01T00:00:00"
    
    def test_get_table_schema_info_error_handling(self, basic_config, mock_logger):
        """Test schema info error handling - lines 292-297."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            enabled=True
        )
        
        with patch.object(TableProcessor, '_create_table_source') as mock_create:
            mock_create.side_effect = Exception("Schema error")
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Should handle error and return error dict (lines 292-297)
            result = processor.get_table_schema_info("TestTable", table_config)
            
            assert result["table_name"] == "TestTable"
            assert "error" in result
            assert result["error"] == "Schema error"


@pytest.mark.unit
class TestTableProcessorSizeEstimation:
    """Test table size estimation - currently uncovered lines 318, 329-331."""
    
    def test_estimate_table_size_basic(self, basic_config, mock_logger):
        """Test basic table size estimation."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            enabled=True
        )
        
        mock_sa = Mock()
        mock_engine = Mock()
        mock_sa.create_engine.return_value = mock_engine
        
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_result = Mock()
        mock_result.scalar.return_value = 1000
        mock_conn.execute.return_value = mock_result
        
        # Mock the text function
        mock_text_obj = Mock()
        mock_sa.text.return_value = mock_text_obj
        
        with patch.dict('sys.modules', {'sqlalchemy': mock_sa}), \
             patch('src.utils.logging_setup.get_logger') as mock_get_logger:
            
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Should execute count query and return result (line 318, 323-324)
            result = processor.estimate_table_size("TestTable", table_config)
            
            assert result == 1000
            mock_sa.text.assert_called_with("SELECT COUNT(*) FROM dbo.TestTable")
            mock_conn.execute.assert_called_once()
            mock_table_logger.info.assert_called_with("Estimated row count for TestTable: 1,000")
    
    def test_estimate_table_size_with_where_clause(self, basic_config, mock_logger):
        """Test size estimation with WHERE clause - line 318."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            where_clause="active = 1",
            enabled=True
        )
        
        mock_sa = Mock()
        mock_engine = Mock()
        mock_sa.create_engine.return_value = mock_engine
        
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_result = Mock()
        mock_result.scalar.return_value = 500
        mock_conn.execute.return_value = mock_result
        
        # Mock the text function to return the query string
        mock_text_obj = Mock()
        mock_text_obj.__str__ = Mock(return_value="SELECT COUNT(*) FROM dbo.TestTable WHERE active = 1")
        mock_sa.text.return_value = mock_text_obj
        
        with patch.dict('sys.modules', {'sqlalchemy': mock_sa}), \
             patch('src.utils.logging_setup.get_logger') as mock_get_logger:
            
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Should use WHERE clause in count query (line 318)
            result = processor.estimate_table_size("TestTable", table_config)
            
            # Verify WHERE clause was included in query
            assert result == 500
            mock_sa.text.assert_called_with("SELECT COUNT(*) FROM dbo.TestTable WHERE active = 1")
            mock_conn.execute.assert_called_once()
            mock_table_logger.info.assert_called_with("Estimated row count for TestTable: 500")
    
    def test_estimate_table_size_error_handling(self, basic_config, mock_logger):
        """Test size estimation error handling - lines 329-331."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            enabled=True
        )
        
        mock_sa = Mock()
        mock_sa.create_engine.side_effect = Exception("Database connection failed")
        
        with patch.dict('sys.modules', {'sqlalchemy': mock_sa}), \
             patch('src.utils.logging_setup.get_logger') as mock_get_logger:
            
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Should handle error and return None (lines 329-331)
            result = processor.estimate_table_size("TestTable", table_config)
            
            assert result is None
            mock_table_logger.warning.assert_called_with("Failed to estimate size for TestTable: Database connection failed")


@pytest.mark.unit
class TestTableProcessorEdgeCases:
    """Test additional edge cases and error paths."""
    
    def test_process_table_with_where_clause_logging(self, basic_config, mock_logger):
        """Test WHERE clause logging - line 116."""
        table_config = TableConfig(
            source_table="dbo.TestTable",
            where_clause="status = 'active'",
            enabled=True
        )
        
        with patch('src.utils.logging_setup.get_logger') as mock_get_logger, \
             patch('src.pipeline.table_processor.sql_database') as mock_sql_db, \
             patch('src.pipeline.table_processor.dlt') as mock_dlt, \
             patch('src.pipeline.table_processor.SchemaAnalyzer') as mock_schema_analyzer:
            
            # Setup logger mock BEFORE creating processor
            mock_table_logger = Mock()
            mock_get_logger.return_value = mock_table_logger
            
            mock_source = Mock()
            mock_sql_db.return_value = mock_source
            mock_source.with_resources.return_value = mock_source
            
            mock_pipeline = Mock()
            mock_dlt.pipeline.return_value = mock_pipeline
            mock_dlt.destinations.sqlalchemy.return_value = "mock_dest"
            
            processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
            
            # Replace the table_logger with our mock after processor creation
            processor.table_logger = mock_table_logger
            
            # Should log WHERE clause application (line 116)
            source = processor._create_table_source("TestTable", table_config)
            
            # Verify WHERE clause was logged
            mock_table_logger.info.assert_called_with("Applied WHERE clause for TestTable: status = 'active'")
    
    def test_convert_initial_value_none(self, basic_config, mock_logger):
        """Test None initial value - line 222."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        # Should return None immediately (line 222)
        result = processor._convert_initial_value(None, IncrementalStrategy.TIMESTAMP)
        assert result is None
    
    def test_convert_timestamp_datetime_object(self, basic_config, mock_logger):
        """Test datetime object as initial value - lines 233-234."""
        processor = TableProcessor(basic_config, mock_logger, auto_optimize=False)
        
        dt = datetime(2023, 1, 1, 12, 0, 0)
        
        # Should return datetime object as-is (lines 233-234)
        result = processor._convert_initial_value(dt, IncrementalStrategy.TIMESTAMP)
        assert result == dt
        assert isinstance(result, datetime)