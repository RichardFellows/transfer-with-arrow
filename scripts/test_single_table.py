#!/usr/bin/env python3
"""
Script to test individual tables for DLT compatibility
"""
import sys
import os
import time
import subprocess
import json

# Add the app directory to Python path
sys.path.insert(0, '/app')

def test_table(table_name, table_config):
    """Test a single table and return results"""
    start_time = time.time()
    
    try:
        # Create a temporary config file for this table
        temp_config = {
            "pipeline": {
                "name": "compatibility_test",
                "dataset_name": "compatibility_data", 
                "chunk_size": 1000,
                "backend": "pyarrow",
                "loader_file_format": "parquet"
            },
            "connections": {
                "source": {
                    "connection_string": "${SOURCE_CONNECTION_STRING}",
                    "schema": "dbo"
                },
                "destination": {
                    "connection_string": "${DEST_CONNECTION_STRING}",
                    "schema": "compatibility_data"
                }
            },
            "tables": {
                table_name: table_config
            },
            "verification": {"enabled": False},
            "logging": {"level": "ERROR"}  # Reduce noise
        }
        
        # Write temp config
        with open('/tmp/test_config.yaml', 'w') as f:
            import yaml
            yaml.dump(temp_config, f)
        
        # Run the pipeline
        cmd = [
            'python', '/app/run_pipeline.py', 
            '--config', '/tmp/test_config.yaml',
            'run', '--tables', table_name
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            return {
                'status': 'SUCCESS',
                'duration': duration,
                'error': None
            }
        else:
            return {
                'status': 'FAILED', 
                'duration': duration,
                'error': result.stderr[-500:] if result.stderr else result.stdout[-500:]
            }
            
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'duration': time.time() - start_time,
            'error': 'Test timed out after 2 minutes'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'duration': time.time() - start_time, 
            'error': str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_single_table.py <table_name>")
        sys.exit(1)
        
    table_name = sys.argv[1]
    
    # Define table configurations
    table_configs = {
        'Test_Minimal': {
            'source_table': 'dbo.Test_Minimal',
            'destination_table': 'test_minimal',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_Decimal_Only': {
            'source_table': 'dbo.Test_Decimal_Only', 
            'destination_table': 'test_decimal_only',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_Money_Only': {
            'source_table': 'dbo.Test_Money_Only',
            'destination_table': 'test_money_only', 
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_VarcharMax_Only': {
            'source_table': 'dbo.Test_VarcharMax_Only',
            'destination_table': 'test_varcharmax_only',
            'disposition': 'replace', 
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_Mixed_Problematic': {
            'source_table': 'dbo.Test_Mixed_Problematic',
            'destination_table': 'test_mixed_problematic',
            'disposition': 'replace',
            'incremental': {'enabled': False}, 
            'enabled': True
        },
        'Test_10_Columns': {
            'source_table': 'dbo.Test_10_Columns',
            'destination_table': 'test_10_columns',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_25_Columns': {
            'source_table': 'dbo.Test_25_Columns',
            'destination_table': 'test_25_columns', 
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_10_Complex': {
            'source_table': 'dbo.Test_10_Complex',
            'destination_table': 'test_10_complex',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_VarcharMax_Heavy': {
            'source_table': 'dbo.Test_VarcharMax_Heavy',
            'destination_table': 'test_varcharmax_heavy',
            'disposition': 'replace',
            'incremental': {'enabled': False}, 
            'enabled': True
        },
        'Test_Decimal_Heavy': {
            'source_table': 'dbo.Test_Decimal_Heavy',
            'destination_table': 'test_decimal_heavy',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_Money_Heavy': {
            'source_table': 'dbo.Test_Money_Heavy',
            'destination_table': 'test_money_heavy',
            'disposition': 'replace', 
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_50_Columns': {
            'source_table': 'dbo.Test_50_Columns',
            'destination_table': 'test_50_columns',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_25_Complex': {
            'source_table': 'dbo.Test_25_Complex',
            'destination_table': 'test_25_complex',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        },
        'Test_100_Simple': {
            'source_table': 'dbo.Test_100_Simple',
            'destination_table': 'test_100_simple',
            'disposition': 'replace',
            'incremental': {'enabled': False},
            'enabled': True
        }
    }
    
    if table_name not in table_configs:
        print(f"Unknown table: {table_name}")
        print(f"Available tables: {list(table_configs.keys())}")
        sys.exit(1)
        
    config = table_configs[table_name] 
    result = test_table(table_name, config)
    
    # Output JSON result for easy parsing
    print(json.dumps({
        'table': table_name,
        'result': result
    }))