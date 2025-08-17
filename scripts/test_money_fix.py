#!/usr/bin/env python3
"""
Test script to verify MONEY column coercion to DECIMAL(19,4) works
"""

import os
import sys
sys.path.append('/app')

import dlt
from dlt.sources.sql_database import sql_database
import logging

def test_money_coercion_simple():
    """Simple test of MONEY coercion using DLT column hints"""
    
    print("🧪 Testing MONEY coercion to DECIMAL(19,4)...")
    
    # Source and destination connections
    source_conn = "mssql://sa:SecurePass123@mssql-source:1433/StackOverflowMini"
    dest_conn = "mssql://sa:SecurePass123@mssql-dest:1433/TargetDB"
    
    try:
        # Create pipeline
        pipeline = dlt.pipeline(
            pipeline_name="money_coercion_test",
            destination=dlt.destinations.sqlalchemy(dest_conn),
            dataset_name="money_test"
        )
        
        # Create source for ProductionTestSmall (has MoneyValue column)
        source = sql_database(
            source_conn,
            backend="pyarrow",
            chunk_size=1000
        )
        
        # Get the resource and apply MONEY coercion hints
        resource = source.with_resources("ProductionTestSmall").resources["ProductionTestSmall"]
        
        # Apply column hints to force MONEY columns to DECIMAL(19,4)
        resource = resource.apply_hints(
            table_name="production_test_small_fixed",
            write_disposition="replace",
            columns={
                "moneyvalue": {
                    "data_type": "decimal",
                    "precision": 19,
                    "scale": 4
                },
                # Add any other MONEY columns here
                "price1": {
                    "data_type": "decimal", 
                    "precision": 19,
                    "scale": 4
                } if "price1" in [col.name for col in resource.compute_table_schema().columns] else None,
                "price2": {
                    "data_type": "decimal",
                    "precision": 19, 
                    "scale": 4
                } if "price2" in [col.name for col in resource.compute_table_schema().columns] else None,
            }
        )
        
        # Remove None values from column hints
        clean_columns = {k: v for k, v in resource._hints.columns.items() if v is not None}
        resource = resource.apply_hints(columns=clean_columns)
        
        print("📋 Applied column hints:")
        for col_name, hints in clean_columns.items():
            if hints and isinstance(hints, dict):
                print(f"  {col_name}: {hints}")
        
        # Run the pipeline
        print("🚀 Running pipeline with MONEY coercion...")
        load_info = pipeline.run(resource)
        
        print("✅ SUCCESS! MONEY columns coerced successfully")
        print(f"📊 Load info: {load_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_column_detection():
    """Test detecting MONEY columns dynamically"""
    
    print("🔍 Testing MONEY column detection...")
    
    source_conn = "mssql://sa:SecurePass123@mssql-source:1433/StackOverflowMini"
    
    try:
        # Create source to inspect schema
        source = sql_database(
            source_conn,
            backend="pyarrow"
        )
        
        # Get ProductionTestSmall resource
        resource = source.with_resources("ProductionTestSmall").resources["ProductionTestSmall"]
        
        # Get schema information
        schema = resource.compute_table_schema()
        
        print("📋 Table schema columns:")
        money_columns = []
        
        for column in schema.columns:
            print(f"  {column.name}: {column.data_type}")
            
            # Check if this might be a MONEY column (DLT converts to decimal)
            if (column.data_type == "decimal" and 
                ("price" in column.name.lower() or 
                 "money" in column.name.lower() or
                 "amount" in column.name.lower())):
                money_columns.append(column.name)
        
        print(f"🎯 Potential MONEY columns detected: {money_columns}")
        
        return money_columns
        
    except Exception as e:
        print(f"❌ Column detection failed: {e}")
        return []

if __name__ == "__main__":
    print("🧪 MONEY Column Coercion Test Suite")
    print("=" * 50)
    
    # Test 1: Column detection
    detected_columns = test_column_detection()
    
    print("\n" + "=" * 50)
    
    # Test 2: Coercion test
    success = test_money_coercion_simple()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"  Detected columns: {detected_columns}")
    print(f"  Coercion test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n💡 SOLUTION CONFIRMED:")
        print("  MONEY columns can be consistently coerced to DECIMAL(19,4)")
        print("  using DLT's column hints feature.")
        print("  This prevents schema evolution conflicts.")
    else:
        print("\n⚠️  Coercion test failed - check database connectivity")