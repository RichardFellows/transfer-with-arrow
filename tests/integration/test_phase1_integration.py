#!/usr/bin/env python3
"""
Integration tests for Phase 1 parquet intermediate layer workflows.
Tests end-to-end data flow from extraction to storage to loading.
"""

import pytest
import pandas as pd
import pyarrow as pa
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import sys
import logging

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dlt_scripts"))

from src.pipeline.archive_manager import ArchiveManager
from src.pipeline.extract_processor import ExtractProcessor
from src.pipeline.load_processor import LoadProcessor
from src.pipeline.two_stage_runner import TwoStagePipelineRunner
from src.pipeline.config_models import ConfigurationModel, TableConfig, IncrementalConfig, PipelineMode, BatchSelection
from src.utils.manifest_manager import BatchStatus
from src.utils.parquet_utils import ParquetUtils


@pytest.fixture
def temp_directories():
    """Create temporary directories for integration testing."""
    with tempfile.TemporaryDirectory() as archive_dir, \
         tempfile.TemporaryDirectory() as manifest_dir, \
         tempfile.TemporaryDirectory() as config_dir:
        yield Path(archive_dir), Path(manifest_dir), Path(config_dir)


@pytest.fixture
def sample_tables_data():
    """Create sample table data for testing."""
    return {
        "users": pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'username': ['alice', 'bob', 'charlie', 'diana', 'eve'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'diana@test.com', 'eve@test.com'],
            'created_at': pd.date_range('2023-01-01', periods=5),
            'is_active': [True, True, False, True, True]
        }),
        "posts": pd.DataFrame({
            'post_id': [101, 102, 103, 104],
            'user_id': [1, 2, 1, 3],
            'title': ['First Post', 'Hello World', 'Second Post', 'My Thoughts'],
            'content': ['This is my first post', 'Hello everyone!', 'Another post here', 'Some thoughts...'],
            'created_at': pd.date_range('2023-01-02', periods=4),
            'view_count': [10, 25, 5, 12]
        }),
        "comments": pd.DataFrame({
            'comment_id': [201, 202, 203, 204, 205],
            'post_id': [101, 101, 102, 103, 104],
            'user_id': [2, 3, 1, 4, 5],
            'content': ['Great post!', 'Thanks for sharing', 'Nice work', 'Interesting', 'Cool stuff'],
            'created_at': pd.date_range('2023-01-03', periods=5)
        })
    }


@pytest.fixture
def archive_manager_setup(temp_directories):
    """Set up ArchiveManager for integration testing."""
    archive_path, manifest_path, _ = temp_directories
    
    return ArchiveManager(
        archive_path=archive_path,
        manifest_path=manifest_path,
        retention_days=30,
        logger=logging.getLogger("test_archive")
    )


@pytest.mark.integration
class TestPhase1BasicWorkflows:
    """Test basic Phase 1 workflows with real components."""
    
    def test_single_table_extract_store_load_workflow(self, archive_manager_setup, sample_tables_data):
        """Test: Complete workflow for a single table."""
        archive_manager = archive_manager_setup
        table_name = "users"
        table_data = sample_tables_data[table_name]
        
        # Phase 1: Create extraction batch
        batch_id, initial_batch = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query=f"SELECT * FROM {table_name}",
            metadata={
                "extraction_type": "full",
                "test_mode": True,
                "source_rows": len(table_data)
            }
        )
        
        assert initial_batch.status == BatchStatus.PENDING
        assert initial_batch.metadata["test_mode"] is True
        
        # Phase 2: Store data in archive
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=table_data,
            compression="snappy",
            metadata={"compression_type": "snappy"}
        )
        
        # Verify storage
        assert file_info.row_count == len(table_data)
        assert file_info.path.exists()
        assert file_info.size_bytes > 0
        
        # Verify batch was updated
        stored_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert stored_batch.status == BatchStatus.COMPLETED
        assert stored_batch.row_count == len(table_data)
        assert stored_batch.completed_at is not None
        
        # Phase 3: Load data from archive
        loaded_data = archive_manager.load_extraction_data(
            batch_id=batch_id,
            table_name=table_name
        )
        
        # Verify data integrity
        assert isinstance(loaded_data, pa.Table)
        assert loaded_data.num_rows == len(table_data)
        assert loaded_data.num_columns == len(table_data.columns)
        
        # Convert back to DataFrame for comparison
        loaded_df = loaded_data.to_pandas()
        
        # Verify column names match
        assert set(loaded_df.columns) == set(table_data.columns)
        
        # Verify row count matches
        assert len(loaded_df) == len(table_data)
        
        # Verify final batch state
        final_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert final_batch.status == BatchStatus.LOADED
        assert final_batch.completed_at is not None  # Should preserve original completion time
    
    def test_multiple_tables_workflow(self, archive_manager_setup, sample_tables_data):
        """Test: Workflow with multiple tables extracted and stored."""
        archive_manager = archive_manager_setup
        batch_results = {}
        
        # Extract and store all tables
        for table_name, table_data in sample_tables_data.items():
            # Create batch
            batch_id, batch = archive_manager.create_extraction_batch(
                table_name=table_name,
                source_query=f"SELECT * FROM {table_name}",
                metadata={"table_type": "sample", "rows": len(table_data)}
            )
            
            # Store data
            file_info = archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=table_data
            )
            
            batch_results[table_name] = {
                "batch_id": batch_id,
                "file_info": file_info,
                "original_rows": len(table_data)
            }
        
        # Verify all tables were stored
        assert len(batch_results) == 3
        
        # Verify archive statistics
        stats = archive_manager.get_archive_statistics()
        assert stats["batch_statistics"]["total_batches"] == 3
        assert stats["filesystem_statistics"]["total_files"] == 3
        
        # Verify each table's data can be loaded
        for table_name, result in batch_results.items():
            loaded_data = archive_manager.load_extraction_data(
                batch_id=result["batch_id"],
                table_name=table_name
            )
            
            assert loaded_data.num_rows == result["original_rows"]
            
            # Verify batch status
            batch = archive_manager.manifest_manager.get_batch(result["batch_id"])
            assert batch.status == BatchStatus.LOADED
    
    def test_incremental_extraction_simulation(self, archive_manager_setup, sample_tables_data):
        """Test: Simulate incremental extraction with multiple batches."""
        archive_manager = archive_manager_setup
        table_name = "posts"
        original_data = sample_tables_data[table_name]
        
        # Simulate first extraction (initial load) with explicit timestamp
        initial_data = original_data.iloc[:2]  # First 2 rows
        
        batch1_id, _ = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query=f"SELECT * FROM {table_name} WHERE post_id <= 102",
            watermark_value="102",
            metadata={"extraction_type": "initial", "watermark": "102"},
            timestamp=datetime.now() - timedelta(seconds=2)
        )
        
        file1_info = archive_manager.store_extraction_data(
            batch_id=batch1_id,
            table_name=table_name,
            data=initial_data
        )
        
        # Simulate incremental extraction (new data) with different timestamp
        incremental_data = original_data.iloc[2:]  # Remaining rows
        
        batch2_id, _ = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query=f"SELECT * FROM {table_name} WHERE post_id > 102",
            watermark_value="104",
            metadata={"extraction_type": "incremental", "watermark": "104"},
            timestamp=datetime.now()
        )
        
        file2_info = archive_manager.store_extraction_data(
            batch_id=batch2_id,
            table_name=table_name,
            data=incremental_data
        )
        
        # Verify both batches exist
        batches = archive_manager.list_available_batches(
            table_name=table_name,
            status=BatchStatus.COMPLETED
        )
        assert len(batches) == 2
        
        # Verify latest batch
        latest_batch = archive_manager.get_latest_batch(table_name)
        assert latest_batch.batch_id == batch2_id
        assert latest_batch.metadata["extraction_type"] == "incremental"
        
        # Load both batches and verify data
        data1 = archive_manager.load_extraction_data(batch1_id, table_name)
        data2 = archive_manager.load_extraction_data(batch2_id, table_name)
        
        assert data1.num_rows == 2
        assert data2.num_rows == 2
        
        # Combined data should equal original
        total_rows = data1.num_rows + data2.num_rows
        assert total_rows == len(original_data)


@pytest.mark.integration
class TestPhase1AdvancedFeatures:
    """Test advanced Phase 1 features and edge cases."""
    
    def test_data_partitioning_workflow(self, archive_manager_setup, sample_tables_data):
        """Test: Data partitioning functionality."""
        archive_manager = archive_manager_setup
        table_name = "users"
        table_data = sample_tables_data[table_name].copy()
        
        # Add a partition column
        table_data['partition_date'] = table_data['created_at'].dt.date.astype(str)
        
        batch_id, _ = archive_manager.create_extraction_batch(
            table_name=table_name,
            metadata={"partitioning": True}
        )
        
        # Store with partitioning
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name=table_name,
            data=table_data,
            partition_cols=["partition_date"]
        )
        
        # Verify partitioned storage
        assert file_info.path.exists()
        
        # Load and verify data integrity
        loaded_data = archive_manager.load_extraction_data(batch_id, table_name)
        assert loaded_data.num_rows == len(table_data)
        assert loaded_data.num_columns == len(table_data.columns)
    
    def test_compression_variants(self, archive_manager_setup, sample_tables_data):
        """Test: Different compression algorithms."""
        archive_manager = archive_manager_setup
        table_name = "comments"
        table_data = sample_tables_data[table_name]
        
        compression_types = ["snappy", "gzip", "brotli"]
        batch_results = {}
        
        for compression in compression_types:
            batch_id, _ = archive_manager.create_extraction_batch(
                table_name=f"{table_name}_{compression}",
                metadata={"compression": compression}
            )
            
            file_info = archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=f"{table_name}_{compression}",
                data=table_data,
                compression=compression
            )
            
            batch_results[compression] = {
                "batch_id": batch_id,
                "file_size": file_info.size_bytes,
                "row_count": file_info.row_count
            }
        
        # Verify all compressions worked
        assert len(batch_results) == 3
        
        # All should have same row count
        row_counts = [result["row_count"] for result in batch_results.values()]
        assert all(count == len(table_data) for count in row_counts)
        
        # File sizes should be different (compression effectiveness varies)
        file_sizes = [result["file_size"] for result in batch_results.values()]
        assert len(set(file_sizes)) > 1  # At least some variation in file sizes
    
    def test_large_dataset_handling(self, archive_manager_setup):
        """Test: Handling of larger datasets."""
        archive_manager = archive_manager_setup
        
        # Create a larger dataset
        large_data = pd.DataFrame({
            'id': range(1, 10001),  # 10,000 rows
            'value': range(10001, 20001),
            'category': ['A', 'B', 'C', 'D', 'E'] * 2000,
            'timestamp': pd.date_range('2023-01-01', periods=10000, freq='1min'),
            'description': [f'Record {i}' for i in range(1, 10001)]
        })
        
        batch_id, _ = archive_manager.create_extraction_batch(
            table_name="large_table",
            metadata={"size": "large", "rows": len(large_data)}
        )
        
        # Store large dataset
        file_info = archive_manager.store_extraction_data(
            batch_id=batch_id,
            table_name="large_table",
            data=large_data,
            compression="snappy"
        )
        
        # Verify storage
        assert file_info.row_count == 10000
        assert file_info.size_bytes > 10000  # Should be substantial size
        
        # Load and verify
        loaded_data = archive_manager.load_extraction_data(batch_id, "large_table")
        assert loaded_data.num_rows == 10000
        assert loaded_data.num_columns == 5
        
        # Verify data integrity with sample checks
        loaded_df = loaded_data.to_pandas()
        assert loaded_df['id'].min() == 1
        assert loaded_df['id'].max() == 10000
        assert len(loaded_df['category'].unique()) == 5
    
    def test_error_handling_and_recovery(self, archive_manager_setup, sample_tables_data):
        """Test: Error handling and recovery scenarios."""
        archive_manager = archive_manager_setup
        table_name = "users"
        
        # Test 1: Invalid data storage
        batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        # Try to store invalid data (None should cause error)
        with pytest.raises(Exception):
            archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=None
            )
        
        # Verify batch was marked as failed
        failed_batch = archive_manager.manifest_manager.get_batch(batch_id)
        assert failed_batch.status == BatchStatus.FAILED
        assert failed_batch.error_message is not None
        
        # Test 2: Loading from failed batch should fail
        with pytest.raises(ValueError, match="is not ready for loading"):
            archive_manager.load_extraction_data(batch_id, table_name)
        
        # Test 3: Recovery with new batch
        recovery_batch_id, _ = archive_manager.create_extraction_batch(table_name)
        
        file_info = archive_manager.store_extraction_data(
            batch_id=recovery_batch_id,
            table_name=table_name,
            data=sample_tables_data[table_name]
        )
        
        # Verify recovery batch succeeded
        recovery_batch = archive_manager.manifest_manager.get_batch(recovery_batch_id)
        assert recovery_batch.status == BatchStatus.COMPLETED
        
        # Should be able to load from recovery batch
        loaded_data = archive_manager.load_extraction_data(recovery_batch_id, table_name)
        assert loaded_data.num_rows == len(sample_tables_data[table_name])


@pytest.mark.integration
class TestPhase1ArchiveManagement:
    """Test archive management and maintenance features."""
    
    def test_archive_statistics_and_reporting(self, archive_manager_setup, sample_tables_data):
        """Test: Archive statistics and reporting functionality."""
        archive_manager = archive_manager_setup
        
        # Create multiple batches across different tables
        batch_info = []
        for table_name, table_data in sample_tables_data.items():
            batch_id, _ = archive_manager.create_extraction_batch(table_name)
            file_info = archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=table_data
            )
            batch_info.append({
                "table": table_name,
                "batch_id": batch_id,
                "rows": len(table_data),
                "size": file_info.size_bytes
            })
        
        # Get comprehensive statistics
        stats = archive_manager.get_archive_statistics()
        
        # Verify batch statistics
        batch_stats = stats["batch_statistics"]
        assert batch_stats["total_batches"] == 3
        assert "status_counts" in batch_stats
        assert batch_stats["status_counts"]["completed"] == 3
        
        # Verify filesystem statistics
        fs_stats = stats["filesystem_statistics"]
        assert fs_stats["total_files"] == 3
        assert fs_stats["total_size_bytes"] > 0
        assert fs_stats["total_size_mb"] > 0
        
        # Verify table statistics
        table_stats = stats["table_statistics"]
        assert len(table_stats) == 3
        for table_name in sample_tables_data.keys():
            assert table_name in table_stats
            assert table_stats[table_name]["file_count"] == 1
            assert table_stats[table_name]["size_bytes"] > 0
    
    def test_archive_integrity_validation(self, archive_manager_setup, sample_tables_data):
        """Test: Archive integrity validation."""
        archive_manager = archive_manager_setup
        
        # Create valid batches
        valid_batches = []
        for table_name, table_data in sample_tables_data.items():
            batch_id, _ = archive_manager.create_extraction_batch(table_name)
            archive_manager.store_extraction_data(batch_id, table_name, table_data)
            valid_batches.append(batch_id)
        
        # Validate archive integrity
        validation_results = archive_manager.validate_archive_integrity()
        
        # All batches should be valid
        assert validation_results["valid_batches"] == 3
        assert validation_results["invalid_batches"] == 0
        assert validation_results["missing_files"] == 0
        assert validation_results["corrupted_files"] == 0
        assert len(validation_results["issues"]) == 0
    
    def test_batch_date_range_queries(self, archive_manager_setup, sample_tables_data):
        """Test: Date range queries for batches."""
        archive_manager = archive_manager_setup
        table_name = "posts"
        table_data = sample_tables_data[table_name]
        
        # Create batches with specific timestamps
        now = datetime.now()
        timestamps = [
            now - timedelta(days=3),
            now - timedelta(days=1),
            now
        ]
        
        batch_ids = []
        for i, timestamp in enumerate(timestamps):
            batch_id, _ = archive_manager.create_extraction_batch(
                table_name=table_name,
                timestamp=timestamp,
                metadata={"day": f"day_{i}"}
            )
            archive_manager.store_extraction_data(batch_id, table_name, table_data)
            batch_ids.append(batch_id)
        
        # Test date range queries
        
        # Query last 2 days (should get 2 batches: day_1 and day_2)
        # Use explicit range between day_0 and day_1 to exclude day_0
        recent_batches = archive_manager.get_batches_in_date_range(
            table_name=table_name,
            start_date=now - timedelta(days=2),  # Between day_0 (3 days) and day_1 (1 day)
            end_date=now + timedelta(hours=1)
        )
        assert len(recent_batches) == 2
        
        # Query specific day (should get 1 batch)
        single_day_batches = archive_manager.get_batches_in_date_range(
            table_name=table_name,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1)
        )
        assert len(single_day_batches) == 1
        
        # Query all time (should get 3 batches)
        all_batches = archive_manager.get_batches_in_date_range(
            table_name=table_name,
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=1)
        )
        assert len(all_batches) == 3
    
    def test_batch_info_and_metadata(self, archive_manager_setup, sample_tables_data):
        """Test: Detailed batch information and metadata handling."""
        archive_manager = archive_manager_setup
        table_name = "users"
        table_data = sample_tables_data[table_name]
        
        # Create batch with rich metadata
        metadata = {
            "extraction_type": "full",
            "source_system": "test_database",
            "extracted_by": "integration_test",
            "data_quality_score": 95.5,
            "tags": ["test", "users", "sample"],
            "validation_rules": {
                "min_rows": 1,
                "required_columns": ["user_id", "username", "email"]
            }
        }
        
        batch_id, _ = archive_manager.create_extraction_batch(
            table_name=table_name,
            source_query="SELECT * FROM users WHERE is_active = 1",
            watermark_value="2023-01-05",
            metadata=metadata
        )
        
        archive_manager.store_extraction_data(batch_id, table_name, table_data)
        
        # Get detailed batch information
        batch_info = archive_manager.get_batch_info(batch_id)
        
        # Verify basic batch info
        assert batch_info["batch_id"] == batch_id
        assert batch_info["table_name"] == table_name
        assert batch_info["status"] == "completed"
        assert batch_info["row_count"] == len(table_data)
        
        # Verify metadata preservation
        assert batch_info["metadata"]["extraction_type"] == "full"
        assert batch_info["metadata"]["data_quality_score"] == 95.5
        assert batch_info["metadata"]["tags"] == ["test", "users", "sample"]
        
        # Verify parquet metadata
        assert "parquet_metadata" in batch_info
        assert batch_info["file_valid"] is True
        
        parquet_meta = batch_info["parquet_metadata"]
        assert parquet_meta["num_rows"] == len(table_data)
        assert parquet_meta["num_columns"] == len(table_data.columns)


@pytest.mark.integration
class TestPhase1EndToEndScenarios:
    """Test realistic end-to-end scenarios."""
    
    def test_daily_extraction_simulation(self, archive_manager_setup, sample_tables_data):
        """Test: Simulate daily extraction workflow."""
        archive_manager = archive_manager_setup
        
        # Simulate 3 days of extractions
        for day in range(3):
            day_timestamp = datetime.now() - timedelta(days=2-day)
            
            for table_name, table_data in sample_tables_data.items():
                # Create daily batch
                batch_id, _ = archive_manager.create_extraction_batch(
                    table_name=table_name,
                    timestamp=day_timestamp,
                    metadata={
                        "extraction_date": day_timestamp.date().isoformat(),
                        "extraction_day": f"day_{day+1}",
                        "scheduled": True
                    }
                )
                
                # Store daily data
                archive_manager.store_extraction_data(
                    batch_id=batch_id,
                    table_name=table_name,
                    data=table_data
                )
        
        # Verify 9 total batches (3 days × 3 tables)
        all_batches = archive_manager.list_available_batches()
        assert len(all_batches) == 9
        
        # Verify each table has 3 batches
        for table_name in sample_tables_data.keys():
            table_batches = archive_manager.list_available_batches(table_name=table_name)
            assert len(table_batches) == 3
            
            # Verify latest batch for each table
            latest_batch = archive_manager.get_latest_batch(table_name)
            assert latest_batch.metadata["extraction_day"] == "day_3"
        
        # Verify archive statistics reflect all extractions
        stats = archive_manager.get_archive_statistics()
        assert stats["batch_statistics"]["total_batches"] == 9
        assert stats["filesystem_statistics"]["total_files"] == 9
    
    def test_data_pipeline_workflow_with_load_scenarios(self, archive_manager_setup, sample_tables_data):
        """Test: Complete data pipeline with various load scenarios."""
        archive_manager = archive_manager_setup
        
        # Phase 1: Extract and store multiple tables
        extraction_results = {}
        for table_name, table_data in sample_tables_data.items():
            batch_id, _ = archive_manager.create_extraction_batch(
                table_name=table_name,
                metadata={"pipeline_stage": "extraction", "priority": "high"}
            )
            
            file_info = archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=table_data
            )
            
            extraction_results[table_name] = {
                "batch_id": batch_id,
                "extracted_rows": file_info.row_count,
                "file_size": file_info.size_bytes
            }
        
        # Phase 2: Load scenarios
        
        # Scenario 1: Load latest batch for each table
        load_results = {}
        for table_name in sample_tables_data.keys():
            latest_batch = archive_manager.get_latest_batch(table_name)
            loaded_data = archive_manager.load_extraction_data(
                latest_batch.batch_id,
                table_name
            )
            
            load_results[table_name] = {
                "batch_id": latest_batch.batch_id,
                "loaded_rows": loaded_data.num_rows,
                "original_rows": extraction_results[table_name]["extracted_rows"]
            }
        
        # Verify all loads completed successfully
        for table_name, result in load_results.items():
            assert result["loaded_rows"] == result["original_rows"]
            
            # Verify batch status is now LOADED
            batch = archive_manager.manifest_manager.get_batch(result["batch_id"])
            assert batch.status == BatchStatus.LOADED
        
        # Phase 3: Verify final state
        final_stats = archive_manager.get_archive_statistics()
        
        # All batches should be loaded
        batch_stats = final_stats["batch_statistics"]
        assert batch_stats["status_counts"]["loaded"] == 3
        
        # Archive integrity should be maintained
        validation_results = archive_manager.validate_archive_integrity()
        assert validation_results["valid_batches"] == 3
        assert len(validation_results["issues"]) == 0
    
    def test_disaster_recovery_scenario(self, archive_manager_setup, sample_tables_data):
        """Test: Disaster recovery and data consistency scenarios."""
        archive_manager = archive_manager_setup
        table_name = "users"
        table_data = sample_tables_data[table_name]
        
        # Create multiple backup batches
        backup_batches = []
        for i in range(3):
            batch_id, _ = archive_manager.create_extraction_batch(
                table_name=table_name,
                timestamp=datetime.now() - timedelta(hours=i),
                metadata={
                    "backup_number": i + 1,
                    "purpose": "disaster_recovery"
                }
            )
            
            archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name=table_name,
                data=table_data
            )
            
            backup_batches.append(batch_id)
        
        # Simulate disaster recovery: verify all backups are intact
        for i, batch_id in enumerate(backup_batches):
            # Verify batch exists and is complete
            batch = archive_manager.manifest_manager.get_batch(batch_id)
            assert batch.status == BatchStatus.COMPLETED
            assert batch.metadata["backup_number"] == i + 1
            
            # Verify data can be recovered
            recovered_data = archive_manager.load_extraction_data(batch_id, table_name)
            assert recovered_data.num_rows == len(table_data)
            
            # Verify file integrity
            batch_info = archive_manager.get_batch_info(batch_id)
            assert batch_info["file_valid"] is True
        
        # Verify archive integrity across all backups
        validation_results = archive_manager.validate_archive_integrity()
        assert validation_results["valid_batches"] == 3
        assert validation_results["invalid_batches"] == 0
        
        # Test point-in-time recovery (get specific backup)
        specific_backup = archive_manager.manifest_manager.get_batch(backup_batches[1])
        assert specific_backup.metadata["backup_number"] == 2
        
        # Load specific backup
        recovered_data = archive_manager.load_extraction_data(
            backup_batches[1], 
            table_name
        )
        assert recovered_data.num_rows == len(table_data)