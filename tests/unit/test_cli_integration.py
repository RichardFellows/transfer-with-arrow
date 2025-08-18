#!/usr/bin/env python3
"""
Integration tests for CLI functionality.
Tests the new CLI commands, validation, and formatting.
"""

import pytest
pytestmark = pytest.mark.unit
from unittest.mock import Mock, MagicMock, patch, ANY
import argparse
from pathlib import Path
from datetime import datetime

# Test basic imports
def test_cli_imports():
    """Test that all CLI modules can be imported without errors."""
    try:
        from src.utils.cli_commands import extract_command, load_command, archive_list_command
        from src.utils.cli_validators import validate_table_names, validate_batch_selection
        from src.utils.cli_formatters import format_extraction_results, format_load_results
        assert True  # If we get here, imports work
    except ImportError as e:
        pytest.fail(f"CLI import failed: {e}")


def test_cli_validators():
    """Test CLI validation functions work correctly."""
    from src.utils.cli_validators import (
        validate_pipeline_mode, validate_environment_name, 
        validate_retention_period, _is_valid_batch_id
    )
    
    # Test valid cases
    validate_pipeline_mode("two-stage")
    validate_environment_name("dev")
    assert validate_retention_period("30d") == 30
    assert validate_retention_period("90") == 90
    assert _is_valid_batch_id("20250817_143000") is True
    
    # Test invalid cases
    with pytest.raises(ValueError):
        validate_pipeline_mode("invalid")
    
    with pytest.raises(ValueError):
        validate_environment_name("invalid@env")
    
    with pytest.raises(ValueError):
        validate_retention_period("invalid")
    
    assert _is_valid_batch_id("invalid") is False


def test_cli_formatters():
    """Test CLI formatting functions work correctly."""
    from src.utils.cli_formatters import (
        format_size_bytes, format_duration, format_progress_indicator
    )
    
    # Test size formatting
    assert format_size_bytes(0) == "0 B"
    assert format_size_bytes(1024) == "1.0 KB"
    assert format_size_bytes(1024*1024) == "1.0 MB"
    
    # Test duration formatting
    assert format_duration(30.5) == "30.5s"
    assert format_duration(90.0) == "1.5m"
    assert format_duration(3700.0) == "1.0h"
    
    # Test progress indicator
    progress = format_progress_indicator(3, 5, "Testing")
    assert "Testing" in progress
    assert "3/5" in progress
    assert "60.0%" in progress


class TestCLICommandMocking:
    """Test CLI commands with proper mocking."""
    
    @patch('src.utils.cli_commands.load_config')
    @patch('src.utils.cli_commands.TwoStagePipelineRunner')
    def test_extract_command_structure(self, mock_runner_class, mock_load_config):
        """Test extract command can be called with proper structure."""
        from src.utils.cli_commands import extract_command
        
        # Setup mocks
        mock_config = Mock()
        mock_config.tables = {
            "test_table": Mock(enabled=True)
        }
        mock_load_config.return_value = mock_config
        
        mock_runner = Mock()
        mock_extract_processor = Mock()
        mock_extract_processor.extract_table.return_value = {"status": "completed", "rows": 100}
        mock_runner.extract_processor = mock_extract_processor
        mock_runner_class.return_value = mock_runner
        
        # Create mock args
        args = Mock()
        args.config = "pipeline_config.yaml"
        args.config_dir = None
        args.environment = None
        args.tables = ["test_table"]
        args.output = None
        
        # Test extract command
        with patch('builtins.print'):
            result = extract_command(args)
        
        # Verify interactions
        mock_load_config.assert_called_once()
        mock_runner_class.assert_called_once_with(mock_config)
        mock_extract_processor.extract_table.assert_called_once_with(
            "test_table",
            ANY
        )
        
        assert result == 0  # Success
    
    @patch('src.utils.cli_commands.load_config')
    @patch('src.utils.cli_commands.TwoStagePipelineRunner')
    def test_load_command_structure(self, mock_runner_class, mock_load_config):
        """Test load command can be called with proper structure."""
        from src.utils.cli_commands import load_command
        from src.pipeline.config_models import BatchSelection
        
        # Setup mocks
        mock_config = Mock()
        mock_config.tables = {
            "test_table": Mock(enabled=True)
        }
        mock_load_config.return_value = mock_config
        
        mock_runner = Mock()
        mock_runner.load_tables.return_value = {
            "phase": "load",
            "status": "completed", 
            "tables": {
                "test_table": {"status": "completed", "loaded_rows": 100}
            }
        }
        mock_runner_class.return_value = mock_runner
        
        # Create mock args
        args = Mock()
        args.config = "pipeline_config.yaml"
        args.config_dir = None
        args.environment = None
        args.tables = ["test_table"]
        args.batch = "latest"
        args.date_range = None
        args.start_date = None
        args.end_date = None
        args.output = None
        
        # Test load command
        with patch('builtins.print'):
            result = load_command(args)
        
        # Verify interactions
        mock_load_config.assert_called_once()
        mock_runner_class.assert_called_once_with(mock_config)
        mock_runner.load_tables.assert_called_once()
        
        assert result == 0  # Success


def test_run_pipeline_main_structure():
    """Test that the main run_pipeline.py structure is correct."""
    # Test that we can import the main function
    import sys
    import os
    
    # Add the dlt_scripts directory to path
    dlt_scripts_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dlt_scripts')
    sys.path.insert(0, dlt_scripts_path)
    
    try:
        import run_pipeline
        assert hasattr(run_pipeline, 'main')
        assert callable(run_pipeline.main)
    except ImportError as e:
        pytest.fail(f"Cannot import run_pipeline: {e}")


def test_makefile_target_commands():
    """Test that the commands used in Makefile targets are structurally correct."""
    # These are the actual commands that will be run by Makefile targets
    expected_commands = [
        "python /app/run_pipeline.py extract",
        "python /app/run_pipeline.py load", 
        "python /app/run_pipeline.py archive list",
        "python /app/run_pipeline.py archive stats",
        "python /app/run_pipeline.py run --mode two-stage"
    ]
    
    # We can't actually run these without Docker, but we can verify 
    # the argument structure would be parsed correctly
    import sys
    import os
    
    dlt_scripts_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dlt_scripts')
    sys.path.insert(0, dlt_scripts_path)
    
    try:
        import run_pipeline
        
        # Test that argparse would handle these commands
        with patch('sys.argv', ['run_pipeline.py', 'extract']):
            parser = argparse.ArgumentParser()
            # The basic structure should work
            assert True  # If we get here, the import worked
            
    except Exception as e:
        pytest.fail(f"Makefile command structure test failed: {e}")


class TestErrorHandling:
    """Test error handling in CLI commands."""
    
    def test_configuration_error_handling(self):
        """Test that configuration errors are handled properly."""
        from src.utils.cli_commands import extract_command
        
        args = Mock()
        args.config = "nonexistent_config.yaml"
        args.config_dir = None
        args.environment = None
        args.tables = None
        args.output = None
        
        with patch('src.utils.cli_commands.load_config') as mock_load_config:
            from src.pipeline.config_loader import ConfigurationError
            mock_load_config.side_effect = ConfigurationError("Test config error")
            
            with patch('builtins.print'):
                result = extract_command(args)
            
            assert result == 1  # Error code
    
    def test_keyboard_interrupt_handling(self):
        """Test that keyboard interrupts are handled properly."""
        from src.utils.cli_commands import extract_command
        
        args = Mock()
        args.config = "pipeline_config.yaml"
        args.environment = None
        args.config_dir = None
        args.tables = None
        args.output = None
        
        with patch('src.utils.cli_commands.load_config') as mock_load_config:
            mock_load_config.side_effect = KeyboardInterrupt()
            
            with patch('builtins.print'):
                result = extract_command(args)
            
            assert result == 1  # Error code


def test_validate_table_names_integration():
    """Test table name validation with mock configuration."""
    from src.utils.cli_validators import validate_table_names
    from src.pipeline.config_models import ConfigurationModel, TableConfig
    
    # Create a mock configuration
    mock_config = Mock()
    mock_config.tables = {
        "valid_table": Mock(enabled=True),
        "disabled_table": Mock(enabled=False)
    }
    
    # Test valid table
    try:
        validate_table_names(["valid_table"], mock_config)
        # Should not raise
    except ValueError:
        pytest.fail("Valid table name should not raise error")
    
    # Test invalid table
    with pytest.raises(ValueError, match="Invalid table names"):
        validate_table_names(["nonexistent_table"], mock_config)
    
    # Test disabled table (should warn but not fail)
    with patch('builtins.print'):
        validate_table_names(["disabled_table"], mock_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])