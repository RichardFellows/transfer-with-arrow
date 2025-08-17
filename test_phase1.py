#!/usr/bin/env python3
"""
Test script for Phase 1 implementation of parquet intermediate layer.
Tests core components and basic workflow functionality.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil
import sqlite3
from datetime import datetime
import logging

# Add the dlt_scripts src to Python path
sys.path.insert(0, str(Path(__file__).parent / "dlt_scripts" / "src"))

# Test imports
try:
    from utils.parquet_utils import ParquetUtils, ParquetFileInfo
    from utils.manifest_manager import ManifestManager, BatchStatus, ExtractionBatch
    from pipeline.archive_manager import ArchiveManager
    from pipeline.config_models import ConfigurationModel, PipelineMode, ArchiveConfig, ExtractConfig, LoadConfig
    from pipeline.config_loader import ConfigLoader
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_configuration_models():
    """Test the new configuration models."""
    print("\n🧪 Testing Configuration Models...")
    
    try:
        # Test PipelineMode enum
        assert PipelineMode.DIRECT == "direct"
        assert PipelineMode.TWO_STAGE == "two_stage"
        print("✅ PipelineMode enum works")
        
        # Test ArchiveConfig
        archive_config = ArchiveConfig(
            enabled=True,
            storage_path="/tmp/test_archive",
            retention_days=30
        )
        assert archive_config.enabled == True
        assert archive_config.retention_days == 30
        print("✅ ArchiveConfig validation works")
        
        # Test validation
        try:
            ArchiveConfig(retention_days=-1)  # Should fail
            print("❌ ArchiveConfig validation failed - negative days allowed")
            return False
        except ValueError:
            print("✅ ArchiveConfig validation works - negative days rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration model test failed: {e}")
        return False


def test_parquet_utils():
    """Test ParquetUtils functionality."""
    print("\n🧪 Testing ParquetUtils...")
    
    try:
        import pandas as pd
        import pyarrow as pa
        
        # Create test data
        test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'value': [10.5, 20.3, 30.1, 40.8, 50.2],
            'date': pd.date_range('2024-01-01', periods=5)
        })
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize ParquetUtils
            parquet_utils = ParquetUtils(logger)
            
            # Test writing parquet
            file_info = parquet_utils.write_parquet_dataset(
                data=test_data,
                output_path=temp_path / "test_output",
                table_name="test_table",
                batch_id="test_batch_001",
                compression="snappy",
                metadata={"test": "metadata"}
            )
            
            assert isinstance(file_info, ParquetFileInfo)
            assert file_info.row_count == 5
            assert file_info.table_name == "test_table"
            print("✅ Parquet write test passed")
            
            # Test reading parquet
            read_data = parquet_utils.read_parquet_dataset(file_info.path)
            assert len(read_data) == 5
            print("✅ Parquet read test passed")
            
            # Test metadata extraction
            metadata = parquet_utils.get_parquet_metadata(file_info.path)
            assert metadata["num_rows"] == 5
            assert metadata["num_columns"] == 4
            print("✅ Parquet metadata test passed")
            
            # Test validation
            is_valid = parquet_utils.validate_parquet_file(file_info.path)
            assert is_valid == True
            print("✅ Parquet validation test passed")
            
        return True
        
    except Exception as e:
        print(f"❌ ParquetUtils test failed: {e}")
        return False


def test_manifest_manager():
    """Test ManifestManager functionality."""
    print("\n🧪 Testing ManifestManager...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize ManifestManager
            manifest_manager = ManifestManager(temp_path, logger)
            
            # Test creating a batch
            batch = manifest_manager.create_batch(
                batch_id="test_batch_001",
                table_name="test_table",
                source_query="SELECT * FROM test_table",
                watermark_value=20240101,
                metadata={"test": "data"}
            )
            
            assert batch.batch_id == "test_batch_001"
            assert batch.status == BatchStatus.PENDING
            assert batch.table_name == "test_table"
            print("✅ Batch creation test passed")
            
            # Test updating batch status
            success = manifest_manager.update_batch_status(
                batch_id="test_batch_001",
                status=BatchStatus.COMPLETED,
                completed_at=datetime.now()
            )
            assert success == True
            print("✅ Batch status update test passed")
            
            # Test updating batch results
            success = manifest_manager.update_batch_results(
                batch_id="test_batch_001",
                row_count=1000,
                file_path="/test/path/file.parquet",
                file_size_bytes=5000000
            )
            assert success == True
            print("✅ Batch results update test passed")
            
            # Test retrieving batch
            retrieved_batch = manifest_manager.get_batch("test_batch_001")
            assert retrieved_batch is not None
            assert retrieved_batch.row_count == 1000
            assert retrieved_batch.status == BatchStatus.COMPLETED
            print("✅ Batch retrieval test passed")
            
            # Test listing batches
            batches = manifest_manager.list_batches(table_name="test_table")
            assert len(batches) == 1
            assert batches[0].batch_id == "test_batch_001"
            print("✅ Batch listing test passed")
            
            # Test statistics
            stats = manifest_manager.get_batch_statistics()
            assert stats["total_batches"] == 1
            assert stats["status_counts"]["completed"] == 1
            print("✅ Batch statistics test passed")
            
        return True
        
    except Exception as e:
        print(f"❌ ManifestManager test failed: {e}")
        return False


def test_archive_manager():
    """Test ArchiveManager functionality."""
    print("\n🧪 Testing ArchiveManager...")
    
    try:
        import pandas as pd
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            archive_path = temp_path / "archive"
            manifest_path = temp_path / "manifests"
            
            # Initialize ArchiveManager
            archive_manager = ArchiveManager(
                archive_path=archive_path,
                manifest_path=manifest_path,
                retention_days=30,
                logger=logger
            )
            
            # Test batch ID generation
            batch_id = archive_manager.generate_batch_id("test_table")
            assert "test_table" in batch_id
            assert len(batch_id.split("_")) >= 3  # table_YYYYMMDD_HHMMSS
            print("✅ Batch ID generation test passed")
            
            # Test creating extraction batch
            batch_id, batch = archive_manager.create_extraction_batch(
                table_name="test_table",
                source_query="SELECT * FROM test_table",
                watermark_value=20240101,
                metadata={"test": "metadata"}
            )
            assert batch_id is not None
            assert batch.table_name == "test_table"
            print("✅ Extraction batch creation test passed")
            
            # Test storing extraction data
            test_data = pd.DataFrame({
                'id': [1, 2, 3],
                'name': ['A', 'B', 'C'],
                'date': pd.date_range('2024-01-01', periods=3)
            })
            
            file_info = archive_manager.store_extraction_data(
                batch_id=batch_id,
                table_name="test_table",
                data=test_data,
                compression="snappy"
            )
            
            assert file_info.row_count == 3
            assert file_info.table_name == "test_table"
            print("✅ Data storage test passed")
            
            # Test loading extraction data
            loaded_data = archive_manager.load_extraction_data(
                batch_id=batch_id,
                table_name="test_table"
            )
            assert len(loaded_data) == 3
            print("✅ Data loading test passed")
            
            # Test listing batches
            batches = archive_manager.list_available_batches(table_name="test_table")
            assert len(batches) >= 1
            print("✅ Batch listing test passed")
            
            # Test archive statistics
            stats = archive_manager.get_archive_statistics()
            assert "batch_statistics" in stats
            assert "filesystem_statistics" in stats
            print("✅ Archive statistics test passed")
            
        return True
        
    except Exception as e:
        print(f"❌ ArchiveManager test failed: {e}")
        return False


def test_config_loading():
    """Test loading our test configuration."""
    print("\n🧪 Testing Configuration Loading...")
    
    try:
        # Test loading the test configuration
        config_path = Path(__file__).parent / "dlt_scripts" / "config" / "test_two_stage_config.yaml"
        
        if not config_path.exists():
            print(f"❌ Test config file not found: {config_path}")
            return False
        
        # Set environment variables for testing
        os.environ["SOURCE_CONNECTION_STRING"] = "test://source"
        os.environ["DEST_CONNECTION_STRING"] = "test://dest"
        
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_config(str(config_path))
        
        assert isinstance(config, ConfigurationModel)
        assert config.pipeline.pipeline_mode == PipelineMode.TWO_STAGE
        assert config.archive.enabled == True
        assert config.archive.storage_path == "/data/parquet_archive"
        print("✅ Test configuration loaded successfully")
        
        # Test validation
        assert config.pipeline.pipeline_mode == PipelineMode.TWO_STAGE
        assert config.archive.enabled == True  # Should be required for two-stage mode
        print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False


def run_all_tests():
    """Run all Phase 1 tests."""
    print("🚀 Starting Phase 1 Implementation Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration Models", test_configuration_models),
        ("ParquetUtils", test_parquet_utils),
        ("ManifestManager", test_manifest_manager),
        ("ArchiveManager", test_archive_manager),
        ("Config Loading", test_config_loading),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 1 tests PASSED! Ready for integration testing.")
        return True
    else:
        print("⚠️  Some tests FAILED. Check implementation before proceeding.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)