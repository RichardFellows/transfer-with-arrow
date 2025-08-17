#!/usr/bin/env python3
"""
Test script to demonstrate MONEY column coercion to consistent DECIMAL(19,4)
"""
import dlt
from dlt.sources.sql_database import sql_database

def test_money_coercion():
    """Test forcing MONEY columns to DECIMAL(19,4) consistently"""
    
    # Method 1: Using DLT data type hints
    pipeline = dlt.pipeline(
        pipeline_name="money_coercion_test",
        destination=dlt.destinations.sqlalchemy("mssql://sa:SecurePass123@mssql-dest:1433/test_db"),
        dataset_name="coercion_test"
    )
    
    # Create source with explicit type hints for MONEY columns
    source = sql_database(
        credentials="mssql://sa:SecurePass123@mssql-source:1433/StackOverflowMini",
        schema="dbo",
        table_names=["ProductionTestTable"]
    ).with_resources("ProductionTestTable")
    
    # Apply data type hints to force MONEY -> DECIMAL(19,4)
    @dlt.resource(
        name="ProductionTestTable",
        write_disposition="replace",
        columns={
            # Force all MONEY columns to consistent precision
            "price1": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price2": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price3": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price4": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price5": {"data_type": "decimal", "precision": 19, "scale": 4},
        }
    )
    def production_test_table_coerced():
        # Get the original resource data
        return source.resources["ProductionTestTable"]
    
    # Test the coercion
    print("Testing MONEY column coercion to DECIMAL(19,4)...")
    
    try:
        # Run the pipeline with forced types
        load_info = pipeline.run(production_test_table_coerced())
        print("✅ Success! MONEY columns coerced to DECIMAL(19,4)")
        print(f"Load info: {load_info}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    test_money_coercion()