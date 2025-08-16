"""
Solution for consistent MONEY column coercion to DECIMAL(19,4)
This shows how to modify the table processor to handle MONEY types consistently.
"""

import dlt
from dlt.sources.sql_database import sql_database
from typing import Dict, Any, Optional

def create_money_coerced_source(
    source_conn: str,
    table_config: Any,
    backend: str = "pyarrow",
    chunk_size: int = 10000
) -> Any:
    """
    Create a DLT source with MONEY columns coerced to DECIMAL(19,4)
    
    Args:
        source_conn: Source database connection string
        table_config: Table configuration
        backend: DLT backend to use
        chunk_size: Chunk size for processing
        
    Returns:
        DLT source with MONEY type coercion applied
    """
    
    # Create base source
    source = sql_database(
        source_conn,
        backend=backend,
        chunk_size=chunk_size
    )
    
    # Get the source table resource
    table_resource = source.with_resources(table_config.source_table)
    
    # Define MONEY column coercion hints
    money_column_hints = {
        # Force all known MONEY columns to DECIMAL(19,4)
        "price1": {"data_type": "decimal", "precision": 19, "scale": 4},
        "price2": {"data_type": "decimal", "precision": 19, "scale": 4}, 
        "price3": {"data_type": "decimal", "precision": 19, "scale": 4},
        "price4": {"data_type": "decimal", "precision": 19, "scale": 4},
        "price5": {"data_type": "decimal", "precision": 19, "scale": 4},
        
        # Add any other MONEY columns from your schema
        "moneyvalue": {"data_type": "decimal", "precision": 19, "scale": 4},
        
        # You can add pattern-based coercion for unknown MONEY columns
        # This would require dynamic column detection
    }
    
    # Apply column hints to the resource
    resource = table_resource.resources[table_config.source_table]
    
    # Method 1: Apply hints using DLT's column configuration
    resource = resource.apply_hints(columns=money_column_hints)
    
    return source

def detect_money_columns_and_create_hints(
    source_conn: str, 
    table_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Dynamically detect MONEY columns and create coercion hints
    
    Args:
        source_conn: Source database connection string
        table_name: Table name to analyze
        
    Returns:
        Dictionary of column hints for MONEY columns
    """
    import pyodbc
    from urllib.parse import urlparse
    
    # Parse connection string to get connection parameters
    # This is simplified - you'd want more robust parsing
    conn_parts = source_conn.replace("mssql://", "").split("@")
    user_pass = conn_parts[0].split(":")
    server_db = conn_parts[1].split("/")
    
    # Connect to source database to detect MONEY columns
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server_db[0]};"
        f"DATABASE={server_db[1]};"
        f"UID={user_pass[0]};"
        f"PWD={user_pass[1]};"
        f"TrustServerCertificate=yes;"
    )
    
    money_hints = {}
    
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Query to find MONEY columns
            query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND DATA_TYPE = 'money'
            """
            
            cursor.execute(query, table_name)
            
            for row in cursor.fetchall():
                column_name = row[0].lower()  # DLT typically uses lowercase
                money_hints[column_name] = {
                    "data_type": "decimal", 
                    "precision": 19, 
                    "scale": 4
                }
                
    except Exception as e:
        print(f"Warning: Could not detect MONEY columns: {e}")
        # Fall back to known columns
        money_hints = {
            "price1": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price2": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price3": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price4": {"data_type": "decimal", "precision": 19, "scale": 4},
            "price5": {"data_type": "decimal", "precision": 19, "scale": 4},
        }
    
    return money_hints

# Example usage in table processor
def enhanced_process_table_with_money_coercion(table_name: str, table_config: Any, config: Any) -> Any:
    """
    Enhanced table processing with automatic MONEY coercion
    
    Args:
        table_name: Name of the table
        table_config: Table configuration
        config: Pipeline configuration
        
    Returns:
        Processing result
    """
    source_conn = config.connections["source"].connection_string
    
    # Step 1: Detect MONEY columns dynamically
    money_hints = detect_money_columns_and_create_hints(source_conn, table_config.source_table)
    
    print(f"Applying MONEY coercion for columns: {list(money_hints.keys())}")
    
    # Step 2: Create source with coercion
    source = sql_database(
        source_conn,
        backend=config.pipeline.backend.value,
        chunk_size=config.pipeline.chunk_size
    ).with_resources(table_config.source_table)
    
    # Step 3: Apply MONEY column hints
    resource = source.resources[table_config.source_table]
    resource = resource.apply_hints(columns=money_hints)
    
    # Step 4: Configure for destination
    resource = resource.apply_hints(
        write_disposition=table_config.disposition.value,
        table_name=table_config.destination_table
    )
    
    # Step 5: Handle incremental loading if configured
    if table_config.incremental and table_config.incremental.enabled:
        if table_config.incremental.strategy == "timestamp":
            resource = resource.apply_hints(
                incremental=dlt.sources.incremental(
                    table_config.incremental.watermark_column,
                    initial_value=table_config.incremental.initial_value
                )
            )
    
    return resource

if __name__ == "__main__":
    # Test the MONEY coercion
    print("Testing MONEY column coercion...")
    
    # Example configuration
    class MockTableConfig:
        source_table = "ProductionTestTable"
        destination_table = "production_test_table" 
        disposition = "replace"
        incremental = None
    
    class MockConfig:
        class connections:
            class source:
                connection_string = "mssql://sa:Strong!Passw0rd@mssql-source:1433/StackOverflowMini"
        class pipeline:
            backend = "pyarrow"
            chunk_size = 10000
    
    # Test detection
    money_hints = detect_money_columns_and_create_hints(
        MockConfig.connections.source.connection_string,
        "ProductionTestTable" 
    )
    
    print(f"Detected MONEY columns: {money_hints}")