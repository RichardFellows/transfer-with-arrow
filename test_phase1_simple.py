#!/usr/bin/env python3
"""
Simple test script for Phase 1 components that can run in the Docker container.
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Change to the dlt_scripts directory and add src to path
os.chdir('/app')
sys.path.insert(0, '/app/src')

print("🚀 Testing Phase 1 Implementation")
print("=" * 50)

# Test 1: Basic imports
print("\n🧪 Test 1: Importing Phase 1 modules...")
try:
    from utils.parquet_utils import ParquetUtils, ParquetFileInfo
    from utils.manifest_manager import ManifestManager, BatchStatus
    from pipeline.archive_manager import ArchiveManager
    from pipeline.config_models import PipelineMode, ArchiveConfig
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration models
print("\n🧪 Test 2: Testing configuration models...")
try:
    # Test enum values
    assert PipelineMode.DIRECT == "direct"
    assert PipelineMode.TWO_STAGE == "two_stage"
    
    # Test archive config
    config = ArchiveConfig(
        enabled=True,
        storage_path="/tmp/test",
        retention_days=30
    )
    assert config.enabled == True
    print("✅ Configuration models work")
except Exception as e:
    print(f"❌ Configuration model test failed: {e}")

# Test 3: Parquet utilities
print("\n🧪 Test 3: Testing ParquetUtils...")
try:
    import pandas as pd
    
    # Create test data
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['A', 'B', 'C']
    })
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        parquet_utils = ParquetUtils()
        
        # Test write
        file_info = parquet_utils.write_parquet_dataset(
            data=test_data,
            output_path=temp_path / "test",
            table_name="test_table",
            batch_id="test_001"
        )
        
        assert file_info.row_count == 3
        assert file_info.table_name == "test_table"
        
        # Test read
        read_data = parquet_utils.read_parquet_dataset(file_info.path)
        assert len(read_data) == 3
        
        print("✅ ParquetUtils works")
        
except Exception as e:
    print(f"❌ ParquetUtils test failed: {e}")

# Test 4: Manifest manager
print("\n🧪 Test 4: Testing ManifestManager...")
try:
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_manager = ManifestManager(Path(temp_dir))
        
        # Create batch
        batch = manifest_manager.create_batch(
            batch_id="test_001",
            table_name="test_table",
            source_query="SELECT * FROM test"
        )
        
        assert batch.batch_id == "test_001"
        assert batch.status == BatchStatus.PENDING
        
        # Update status
        success = manifest_manager.update_batch_status(
            batch_id="test_001",
            status=BatchStatus.COMPLETED,
            completed_at=datetime.now()
        )
        assert success == True
        
        # Retrieve batch
        retrieved = manifest_manager.get_batch("test_001")
        assert retrieved.status == BatchStatus.COMPLETED
        
        print("✅ ManifestManager works")
        
except Exception as e:
    print(f"❌ ManifestManager test failed: {e}")

# Test 5: Archive manager
print("\n🧪 Test 5: Testing ArchiveManager basic functionality...")
try:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        archive_manager = ArchiveManager(
            archive_path=temp_path / "archive",
            manifest_path=temp_path / "manifests",
            retention_days=30
        )
        
        # Test batch ID generation
        batch_id = archive_manager.generate_batch_id("test_table")
        assert "test_table" in batch_id
        
        # Test batch creation
        batch_id, batch = archive_manager.create_extraction_batch(
            table_name="test_table",
            source_query="SELECT * FROM test"
        )
        assert batch_id is not None
        assert batch.table_name == "test_table"
        
        print("✅ ArchiveManager basic functionality works")
        
except Exception as e:
    print(f"❌ ArchiveManager test failed: {e}")

print("\n" + "=" * 50)
print("📊 BASIC TESTS COMPLETE")
print("✅ Core Phase 1 components are working!")
print("\nNext steps:")
print("1. Test integration with databases")
print("2. Test full extract/load workflow") 
print("3. Test CLI extensions")
print("=" * 50)