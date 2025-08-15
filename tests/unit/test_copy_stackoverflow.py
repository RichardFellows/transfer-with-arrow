#!/usr/bin/env python3

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts'))
from copy_stackoverflow import copy_stackoverflow_tables, verify_copy


class TestCopyStackoverflowTables:
    """Unit tests for copy_stackoverflow_tables function."""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv(
            'SOURCE_CONNECTION_STRING', 
            'mssql+pyodbc://sa:password@source:1433/StackOverflowMini?driver=test'
        )
        monkeypatch.setenv(
            'DEST_CONNECTION_STRING',
            'mssql+pyodbc://sa:password@dest:1433/TargetDB?driver=test'
        )
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('copy_stackoverflow.sa.create_engine') as mock_engine, \
             patch('copy_stackoverflow.sql_database') as mock_sql_db, \
             patch('copy_stackoverflow.dlt.pipeline') as mock_pipeline, \
             patch('copy_stackoverflow.dlt.destinations.sqlalchemy') as mock_dest:
            
            # Mock engine
            mock_engine.return_value = Mock()
            
            # Mock sql_database source with proper DLT structure
            mock_source = Mock()
            
            # Create mock resources that behave like DltResourceDict
            mock_users_resource = Mock()
            mock_users_resource.name = 'Users'
            mock_posts_resource = Mock()
            mock_posts_resource.name = 'Posts'
            
            # Mock the resources dict-like object
            mock_resources = Mock()
            mock_resources.values.return_value = [mock_users_resource, mock_posts_resource]
            mock_source.resources = mock_resources
            
            mock_sql_db.return_value = mock_source
            mock_source.with_resources.return_value = mock_source
            
            # Mock Posts resource for incremental
            mock_source.Posts = Mock()
            mock_source.Posts.apply_hints = Mock()
            
            # Mock pipeline
            mock_pipeline_instance = Mock()
            mock_load_info = Mock()
            mock_load_info.load_packages = [Mock()]
            mock_load_info.load_packages[0].tables = {'Users': Mock(), 'Posts': Mock()}
            mock_pipeline_instance.run.return_value = mock_load_info
            mock_pipeline.return_value = mock_pipeline_instance
            
            yield {
                'engine': mock_engine,
                'sql_db': mock_sql_db,
                'pipeline': mock_pipeline,
                'destination': mock_dest,
                'source': mock_source,
                'pipeline_instance': mock_pipeline_instance,
                'load_info': mock_load_info
            }
    
    @pytest.mark.unit
    def test_missing_source_connection_string(self, monkeypatch):
        """Test that missing SOURCE_CONNECTION_STRING raises SystemExit."""
        monkeypatch.delenv('SOURCE_CONNECTION_STRING', raising=False)
        monkeypatch.setenv('DEST_CONNECTION_STRING', 'test_dest')
        
        with pytest.raises(SystemExit) as exc_info:
            copy_stackoverflow_tables()
        
        assert exc_info.value.code == 1
    
    @pytest.mark.unit
    def test_missing_dest_connection_string(self, monkeypatch):
        """Test that missing DEST_CONNECTION_STRING raises SystemExit."""
        monkeypatch.setenv('SOURCE_CONNECTION_STRING', 'test_source')
        monkeypatch.delenv('DEST_CONNECTION_STRING', raising=False)
        
        with pytest.raises(SystemExit) as exc_info:
            copy_stackoverflow_tables()
        
        assert exc_info.value.code == 1
    
    @pytest.mark.unit
    def test_default_tables_configuration(self, mock_env_vars, mock_dependencies):
        """Test that default tables are configured correctly."""
        load_info = copy_stackoverflow_tables()
        
        # Verify sql_database was called with correct parameters
        mock_dependencies['sql_db'].assert_called_once()
        call_args = mock_dependencies['sql_db'].call_args
        
        # Check backend configuration
        assert call_args[1]['backend'] == 'pyarrow'
        assert call_args[1]['backend_kwargs']['tz'] == 'UTC'
        assert call_args[1]['reflection_level'] == 'full_with_precision'
        assert call_args[1]['chunk_size'] == 10000
        
        # Verify with_resources was called with default tables
        mock_dependencies['source'].with_resources.assert_called_once()
        tables_arg = mock_dependencies['source'].with_resources.call_args[0]
        expected_tables = ["Users", "Posts", "Comments", "Votes", "Badges", "PostTags", "Tags"]
        assert list(tables_arg) == expected_tables
    
    @pytest.mark.unit
    def test_custom_tables_configuration(self, mock_env_vars, mock_dependencies):
        """Test that custom tables are configured correctly."""
        custom_tables = ["Users", "Posts"]
        copy_stackoverflow_tables(tables_to_copy=custom_tables)
        
        # Verify with_resources was called with custom tables
        mock_dependencies['source'].with_resources.assert_called_once_with(*custom_tables)
    
    @pytest.mark.unit
    def test_incremental_loading_configuration(self, mock_env_vars, mock_dependencies):
        """Test that incremental loading is configured correctly."""
        with patch('copy_stackoverflow.dlt.sources.incremental') as mock_incremental:
            mock_incremental.return_value = Mock()
            
            copy_stackoverflow_tables(use_incremental=True)
            
            # Verify incremental was configured
            mock_incremental.assert_called_once_with(
                "CreationDate",
                initial_value=datetime(2020, 1, 1)
            )
            mock_dependencies['source'].Posts.apply_hints.assert_called_once()
    
    @pytest.mark.unit
    def test_pipeline_configuration(self, mock_env_vars, mock_dependencies):
        """Test that DLT pipeline is configured correctly."""
        copy_stackoverflow_tables()
        
        # Verify pipeline was created with correct parameters
        mock_dependencies['pipeline'].assert_called_once_with(
            pipeline_name="stackoverflow_copy",
            destination=mock_dependencies['destination'].return_value,
            dataset_name="stackoverflow_data"
        )
        
        # Verify pipeline.run was called with correct parameters
        run_call = mock_dependencies['pipeline_instance'].run
        run_call.assert_called_once()
        call_kwargs = run_call.call_args[1]
        assert call_kwargs['write_disposition'] == 'replace'
        assert call_kwargs['loader_file_format'] == 'parquet'
    
    @pytest.mark.unit
    def test_different_write_dispositions(self, mock_env_vars, mock_dependencies):
        """Test different write dispositions."""
        for disposition in ['replace', 'append', 'merge']:
            copy_stackoverflow_tables(write_disposition=disposition)
            
            call_kwargs = mock_dependencies['pipeline_instance'].run.call_args[1]
            assert call_kwargs['write_disposition'] == disposition
    
    @pytest.mark.unit
    def test_successful_execution_returns_load_info(self, mock_env_vars, mock_dependencies):
        """Test that successful execution returns load_info."""
        result = copy_stackoverflow_tables()
        
        assert result is not None
        assert result == mock_dependencies['load_info']


class TestVerifyCopy:
    """Unit tests for verify_copy function."""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv(
            'SOURCE_CONNECTION_STRING', 
            'mssql+pyodbc://sa:password@source:1433/StackOverflowMini?driver=test'
        )
        monkeypatch.setenv(
            'DEST_CONNECTION_STRING',
            'mssql+pyodbc://sa:password@dest:1433/TargetDB?driver=test'
        )
    
    @pytest.mark.unit
    def test_verify_copy_with_matching_counts(self, mock_env_vars, capsys):
        """Test verify_copy when source and destination counts match."""
        with patch('copy_stackoverflow.sa.create_engine') as mock_engine:
            # Mock connection and execute
            mock_conn = Mock()
            mock_conn.execute.return_value.scalar.side_effect = [
                1000,  # source count for Users
                1000,  # dest count for Users
                5000,  # source count for Posts
                5000,  # dest count for Posts
            ]
            
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            
            verify_copy()
            
            captured = capsys.readouterr()
            assert "✅ Users: Source=1,000, Destination=1,000" in captured.out
            assert "✅ Posts: Source=5,000, Destination=5,000" in captured.out
    
    @pytest.mark.unit
    def test_verify_copy_with_mismatched_counts(self, mock_env_vars, capsys):
        """Test verify_copy when source and destination counts don't match."""
        with patch('copy_stackoverflow.sa.create_engine') as mock_engine:
            # Mock connection and execute
            mock_conn = Mock()
            mock_conn.execute.return_value.scalar.side_effect = [
                1000,  # source count for Users
                900,   # dest count for Users (mismatch)
            ]
            
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            
            verify_copy()
            
            captured = capsys.readouterr()
            assert "⚠️ Users: Source=1,000, Destination=900" in captured.out
    
    @pytest.mark.unit
    def test_verify_copy_with_database_error(self, mock_env_vars, capsys):
        """Test verify_copy when database query fails."""
        with patch('copy_stackoverflow.sa.create_engine') as mock_engine:
            # Mock connection that raises an exception
            mock_conn = Mock()
            mock_conn.execute.side_effect = Exception("Database connection failed")
            
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            
            verify_copy()
            
            captured = capsys.readouterr()
            assert "❌ Users: Error - Database connection failed" in captured.out


class TestArgumentParsing:
    """Test argument parsing functionality."""
    
    @pytest.mark.unit
    def test_default_arguments(self):
        """Test default argument values."""
        from copy_stackoverflow import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--tables', nargs='+', help='Specific tables to copy')
        parser.add_argument('--incremental', action='store_true', help='Use incremental loading')
        parser.add_argument('--verify', action='store_true', help='Verify copy after completion')
        parser.add_argument('--disposition', default='replace', 
                           choices=['replace', 'append', 'merge'],
                           help='Write disposition (default: replace)')
        
        args = parser.parse_args([])
        
        assert args.tables is None
        assert args.incremental is False
        assert args.verify is False
        assert args.disposition == 'replace'
    
    @pytest.mark.unit
    def test_custom_arguments(self):
        """Test custom argument values."""
        from copy_stackoverflow import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--tables', nargs='+', help='Specific tables to copy')
        parser.add_argument('--incremental', action='store_true', help='Use incremental loading')
        parser.add_argument('--verify', action='store_true', help='Verify copy after completion')
        parser.add_argument('--disposition', default='replace', 
                           choices=['replace', 'append', 'merge'],
                           help='Write disposition (default: replace)')
        
        args = parser.parse_args([
            '--tables', 'Users', 'Posts',
            '--incremental',
            '--verify',
            '--disposition', 'append'
        ])
        
        assert args.tables == ['Users', 'Posts']
        assert args.incremental is True
        assert args.verify is True
        assert args.disposition == 'append'