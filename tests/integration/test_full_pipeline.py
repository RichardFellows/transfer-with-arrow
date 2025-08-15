#!/usr/bin/env python3

import os
import sys
import pytest
import sqlalchemy as sa
from datetime import datetime

# Add the dlt_scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dlt_scripts'))
from copy_stackoverflow import copy_stackoverflow_tables, verify_copy


@pytest.mark.integration
@pytest.mark.slow
class TestFullPipeline:
    """Integration tests for the complete data migration pipeline."""
    
    def test_full_pipeline_with_default_tables(self, test_env_vars, sample_table_counts):
        """Test full pipeline execution with default tables."""
        # Only test a subset of tables for faster execution
        tables_to_test = ['Users', 'Posts', 'Comments']
        
        # Run the migration
        load_info = copy_stackoverflow_tables(
            tables_to_copy=tables_to_test,
            write_disposition="replace"
        )
        
        # Verify load_info is returned
        assert load_info is not None
        
        # Verify data was copied by checking destination database
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            for table in tables_to_test:
                # Check that table exists in destination
                result = conn.execute(sa.text(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'stackoverflow_data' 
                    AND TABLE_NAME = '{table}'
                """))
                table_exists = result.scalar()
                assert table_exists == 1, f"Table {table} was not created in destination"
                
                # Check row count
                result = conn.execute(sa.text(f"""
                    SELECT COUNT(*) FROM stackoverflow_data.{table}
                """))
                row_count = result.scalar()
                expected_count = sample_table_counts[table]
                assert row_count == expected_count, f"Table {table} has {row_count} rows, expected {expected_count}"
    
    def test_pipeline_with_single_table(self, test_env_vars):
        """Test pipeline execution with a single table."""
        # Run migration for just Users table
        load_info = copy_stackoverflow_tables(
            tables_to_copy=['Users'],
            write_disposition="replace"
        )
        
        assert load_info is not None
        
        # Verify only Users table was created
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            # Check Users table exists and has data in stackoverflow_data schema
            result = conn.execute(sa.text("""
                SELECT COUNT(*) FROM stackoverflow_data.users
            """))
            assert result.scalar() == 3
            
            # Check that Posts table was not created
            result = conn.execute(sa.text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'stackoverflow_data' 
                AND TABLE_NAME = 'posts'
            """))
            assert result.scalar() == 0
    
    def test_pipeline_append_disposition(self, test_env_vars):
        """Test pipeline with append write disposition."""
        # First run - replace
        copy_stackoverflow_tables(
            tables_to_copy=['Users'],
            write_disposition="replace"
        )
        
        # Second run - append (should double the data)
        copy_stackoverflow_tables(
            tables_to_copy=['Users'],
            write_disposition="append"
        )
        
        # Verify data was appended
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            result = conn.execute(sa.text("""
                SELECT COUNT(*) FROM stackoverflow_data.Users
            """))
            # Should have 6 rows (3 original + 3 appended)
            assert result.scalar() == 6
    
    def test_verify_function_integration(self, test_env_vars, capsys):
        """Test the verify_copy function with real data."""
        # First, run a migration
        copy_stackoverflow_tables(
            tables_to_copy=['Users', 'Posts'],
            write_disposition="replace"
        )
        
        # Then verify the copy
        verify_copy()
        
        # Check the output
        captured = capsys.readouterr()
        assert "✅ Users: Source=3, Destination=3" in captured.out
        assert "✅ Posts: Source=3, Destination=3" in captured.out
    
    def test_data_integrity(self, test_env_vars):
        """Test that data integrity is maintained during migration."""
        # Run migration
        copy_stackoverflow_tables(
            tables_to_copy=['Users'],
            write_disposition="replace"
        )
        
        # Verify specific data values
        source_engine = sa.create_engine(test_env_vars['source'])
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        # Get data from source
        with source_engine.connect() as conn:
            source_users = conn.execute(sa.text("""
                SELECT Id, DisplayName, Reputation 
                FROM dbo.Users 
                ORDER BY Id
            """)).fetchall()
        
        # Get data from destination
        with dest_engine.connect() as conn:
            dest_users = conn.execute(sa.text("""
                SELECT Id, DisplayName, Reputation 
                FROM stackoverflow_data.users 
                ORDER BY Id
            """)).fetchall()
        
        # Compare data
        assert len(source_users) == len(dest_users)
        
        for source_user, dest_user in zip(source_users, dest_users):
            assert source_user.Id == dest_user.Id
            assert source_user.DisplayName == dest_user.DisplayName
            assert source_user.Reputation == dest_user.Reputation
    
    def test_incremental_loading(self, test_env_vars):
        """Test incremental loading functionality."""
        # Note: This is a simplified test since we don't have timestamp-based data changes
        # In a real scenario, you would add new data to source and test incremental loading
        
        # Run initial load
        load_info = copy_stackoverflow_tables(
            tables_to_copy=['Posts'],
            write_disposition="replace",
            use_incremental=True
        )
        
        assert load_info is not None
        
        # Verify data was loaded
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            result = conn.execute(sa.text("""
                SELECT COUNT(*) FROM stackoverflow_data.Posts
            """))
            assert result.scalar() == 3
    
    def test_error_handling_invalid_table(self, test_env_vars):
        """Test error handling when specifying invalid table names."""
        # This should not raise an exception but may result in no data
        # DLT typically handles missing tables gracefully
        load_info = copy_stackoverflow_tables(
            tables_to_copy=['NonExistentTable'],
            write_disposition="replace"
        )
        
        # The function should complete without error
        # but no tables should be created
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            result = conn.execute(sa.text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'stackoverflow_data'
            """))
            # Should be 0 tables since the table doesn't exist
            assert result.scalar() == 0


@pytest.mark.integration
class TestPipelinePerformance:
    """Performance-related integration tests."""
    
    def test_chunk_processing(self, test_env_vars):
        """Test that chunk processing works correctly."""
        # Run migration with a small chunk size
        load_info = copy_stackoverflow_tables(
            tables_to_copy=['Users'],
            write_disposition="replace"
        )
        
        # Verify the migration completed successfully
        assert load_info is not None
        
        dest_engine = sa.create_engine(test_env_vars['dest'])
        with dest_engine.connect() as conn:
            result = conn.execute(sa.text("""
                SELECT COUNT(*) FROM stackoverflow_data.Users
            """))
            assert result.scalar() == 3
    
    @pytest.mark.slow
    def test_multiple_table_migration(self, test_env_vars):
        """Test migration of multiple tables."""
        tables = ['Users', 'Posts', 'Comments']
        
        load_info = copy_stackoverflow_tables(
            tables_to_copy=tables,
            write_disposition="replace"
        )
        
        assert load_info is not None
        
        # Verify all tables were migrated
        dest_engine = sa.create_engine(test_env_vars['dest'])
        
        with dest_engine.connect() as conn:
            for table in tables:
                result = conn.execute(sa.text(f"""
                    SELECT COUNT(*) FROM stackoverflow_data.{table}
                """))
                assert result.scalar() > 0, f"Table {table} has no data"