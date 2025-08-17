#!/usr/bin/env python3
"""
Dynamic Schema Analyzer for DLT Pipeline
Analyzes source table schema and generates optimal PyArrow data type mappings
to prevent precision loss and ensure consistent schema evolution.
"""

import pyodbc
import logging
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
import re

class SchemaAnalyzer:
    """Analyzes source database schema and generates optimal DLT column hints"""
    
    def __init__(self, connection_string: str, logger: Optional[logging.Logger] = None):
        """
        Initialize schema analyzer
        
        Args:
            connection_string: Source database connection string
            logger: Logger instance
        """
        self.connection_string = connection_string
        self.logger = logger or logging.getLogger(__name__)
        self._parsed_conn = self._parse_connection_string()
    
    def _parse_connection_string(self) -> Dict[str, str]:
        """Parse MSSQL connection string into components"""
        try:
            # Handle mssql:// format
            if self.connection_string.startswith("mssql://"):
                parsed = urlparse(self.connection_string)
                return {
                    "server": parsed.hostname,
                    "port": parsed.port or 1433,
                    "database": parsed.path.lstrip('/'),
                    "username": parsed.username,
                    "password": parsed.password
                }
            else:
                # Handle direct connection string format
                return {"raw": self.connection_string}
        except Exception as e:
            self.logger.warning(f"Could not parse connection string: {e}")
            return {"raw": self.connection_string}
    
    def _get_odbc_connection_string(self) -> str:
        """Generate ODBC connection string for direct database access"""
        if "raw" in self._parsed_conn:
            return self._parsed_conn["raw"]
        
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self._parsed_conn['server']},{self._parsed_conn['port']};"
            f"DATABASE={self._parsed_conn['database']};"
            f"UID={self._parsed_conn['username']};"
            f"PWD={self._parsed_conn['password']};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=no;"
        )
    
    def analyze_table_schema(self, table_name: str, schema: str = "dbo") -> Dict[str, Dict[str, Any]]:
        """
        Analyze table schema and generate optimal column hints
        
        Args:
            table_name: Name of the table to analyze
            schema: Database schema (default: dbo)
            
        Returns:
            Dictionary of column hints for DLT
        """
        self.logger.info(f"🔍 Analyzing schema for table: {schema}.{table_name}")
        
        try:
            with pyodbc.connect(self._get_odbc_connection_string()) as conn:
                cursor = conn.cursor()
                
                # Query to get detailed column information
                query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                ORDER BY ORDINAL_POSITION
                """
                
                cursor.execute(query, table_name, schema)
                columns = cursor.fetchall()
                
                if not columns:
                    self.logger.warning(f"No columns found for table {schema}.{table_name}")
                    return {}
                
                column_hints = {}
                problematic_columns = []
                
                for column in columns:
                    col_name = column.COLUMN_NAME.lower()  # DLT uses lowercase
                    data_type = column.DATA_TYPE.lower()
                    max_length = column.CHARACTER_MAXIMUM_LENGTH
                    precision = column.NUMERIC_PRECISION
                    scale = column.NUMERIC_SCALE
                    nullable = column.IS_NULLABLE == 'YES'
                    
                    hint = self._generate_column_hint(
                        col_name, data_type, max_length, precision, scale, nullable
                    )
                    
                    if hint:
                        column_hints[col_name] = hint
                        if self._is_problematic_type(data_type):
                            problematic_columns.append(col_name)
                
                self.logger.info(f"✅ Generated hints for {len(column_hints)} columns")
                if problematic_columns:
                    self.logger.info(f"🎯 Optimized problematic columns: {problematic_columns}")
                
                return column_hints
                
        except Exception as e:
            self.logger.error(f"❌ Schema analysis failed: {e}")
            return {}
    
    def _generate_column_hint(
        self, 
        col_name: str, 
        data_type: str, 
        max_length: Optional[int], 
        precision: Optional[int], 
        scale: Optional[int],
        nullable: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Generate optimal column hint based on SQL Server data type
        
        Args:
            col_name: Column name
            data_type: SQL Server data type
            max_length: Maximum character length
            precision: Numeric precision
            scale: Numeric scale
            nullable: Whether column is nullable
            
        Returns:
            Column hint dictionary or None if no hint needed
        """
        
        # MONEY type - force to DECIMAL(19,4) for consistency
        if data_type == "money":
            self.logger.debug(f"🎯 MONEY column {col_name} → DECIMAL(19,4)")
            return {
                "data_type": "decimal",
                "precision": 19,
                "scale": 4,
                "nullable": nullable
            }
        
        # SMALLMONEY type - force to DECIMAL(10,4) for consistency  
        elif data_type == "smallmoney":
            self.logger.debug(f"🎯 SMALLMONEY column {col_name} → DECIMAL(10,4)")
            return {
                "data_type": "decimal", 
                "precision": 10,
                "scale": 4,
                "nullable": nullable
            }
        
        # DECIMAL/NUMERIC - preserve exact precision and scale
        elif data_type in ["decimal", "numeric"]:
            if precision and scale is not None:
                # Handle high-precision decimals explicitly
                if precision > 28:  # PyArrow decimal128 limit considerations
                    self.logger.debug(f"🎯 High-precision DECIMAL({precision},{scale}) column {col_name}")
                    return {
                        "data_type": "decimal",
                        "precision": precision,
                        "scale": scale,
                        "nullable": nullable
                    }
        
        # FLOAT/REAL - specify precision to avoid conversion issues
        elif data_type in ["float", "real"]:
            self.logger.debug(f"🎯 FLOAT column {col_name} → double precision")
            return {
                "data_type": "double",
                "nullable": nullable
            }
        
        # VARCHAR(MAX), NVARCHAR(MAX), TEXT - ensure large text handling
        elif data_type in ["varchar", "nvarchar", "text", "ntext"] and (max_length == -1 or max_length is None or max_length > 8000):
            self.logger.debug(f"🎯 Large text column {col_name} → text")
            return {
                "data_type": "text",
                "nullable": nullable
            }
        
        # UNIQUEIDENTIFIER - ensure proper UUID handling
        elif data_type == "uniqueidentifier":
            self.logger.debug(f"🎯 UNIQUEIDENTIFIER column {col_name} → text")
            return {
                "data_type": "text",
                "nullable": nullable
            }
        
        # DATETIME2 with high precision - preserve precision
        elif data_type == "datetime2":
            self.logger.debug(f"🎯 DATETIME2 column {col_name} → timestamp")
            return {
                "data_type": "timestamp",
                "nullable": nullable
            }
        
        # BIGINT - ensure proper 64-bit integer handling
        elif data_type == "bigint":
            return {
                "data_type": "bigint",
                "nullable": nullable
            }
        
        # BIT - ensure proper boolean handling
        elif data_type == "bit":
            return {
                "data_type": "bool",
                "nullable": nullable
            }
        
        # No hint needed for standard types that DLT handles well
        return None
    
    def _is_problematic_type(self, data_type: str) -> bool:
        """Check if data type is known to cause schema evolution issues"""
        problematic_types = {
            "money", "smallmoney",  # Precision mapping issues
            "uniqueidentifier",     # UUID conversion issues
            "text", "ntext",        # Large text handling
            "float", "real"         # Floating point precision
        }
        return data_type in problematic_types
    
    def get_schema_summary(self, table_name: str, schema: str = "dbo") -> Dict[str, Any]:
        """
        Get summary information about table schema
        
        Args:
            table_name: Name of the table
            schema: Database schema
            
        Returns:
            Schema summary dictionary
        """
        try:
            with pyodbc.connect(self._get_odbc_connection_string()) as conn:
                cursor = conn.cursor()
                
                # Get column count and types
                type_query = """
                SELECT 
                    DATA_TYPE,
                    COUNT(*) as column_count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                GROUP BY DATA_TYPE
                ORDER BY DATA_TYPE
                """
                
                cursor.execute(type_query, table_name, schema)
                type_summary = {row.DATA_TYPE: row.column_count for row in cursor.fetchall()}
                
                # Get row count
                row_count_query = f"SELECT COUNT(*) FROM [{schema}].[{table_name}]"
                cursor.execute(row_count_query)
                row_count = cursor.fetchone()[0]
                
                return {
                    "table_name": f"{schema}.{table_name}",
                    "total_columns": sum(type_summary.values()),
                    "row_count": row_count,
                    "data_types": type_summary,
                    "problematic_types": {
                        dt: count for dt, count in type_summary.items() 
                        if self._is_problematic_type(dt.lower())
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get schema summary: {e}")
            return {}
    
    def generate_config_section(self, table_name: str, schema: str = "dbo") -> Dict[str, Any]:
        """
        Generate complete configuration section for a table with optimized column hints
        
        Args:
            table_name: Name of the table
            schema: Database schema
            
        Returns:
            Complete table configuration with column hints
        """
        column_hints = self.analyze_table_schema(table_name, schema)
        schema_summary = self.get_schema_summary(table_name, schema)
        
        config = {
            "source_table": f"{schema}.{table_name}",
            "destination_table": table_name.lower(),
            "disposition": "replace",
            "incremental": {"enabled": False},
            "enabled": True
        }
        
        if column_hints:
            config["column_hints"] = column_hints
            
        # Add metadata comments
        config["_metadata"] = {
            "total_columns": schema_summary.get("total_columns", 0),
            "row_count": schema_summary.get("row_count", 0),
            "optimized_columns": len(column_hints),
            "problematic_types": schema_summary.get("problematic_types", {})
        }
        
        return config


def analyze_and_generate_hints(connection_string: str, table_name: str, schema: str = "dbo") -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to analyze table and generate column hints
    
    Args:
        connection_string: Database connection string
        table_name: Table name to analyze
        schema: Database schema (default: dbo)
        
    Returns:
        Column hints dictionary
    """
    analyzer = SchemaAnalyzer(connection_string)
    return analyzer.analyze_table_schema(table_name, schema)


if __name__ == "__main__":
    # Test the schema analyzer
    import os
    
    # Example usage
    conn_str = "mssql://sa:SecurePass123@mssql-source:1433/StackOverflowMini"
    
    analyzer = SchemaAnalyzer(conn_str)
    
    # Test with ProductionTestTable
    print("🔍 Analyzing ProductionTestTable...")
    hints = analyzer.analyze_table_schema("ProductionTestTable")
    
    print(f"\n📊 Generated {len(hints)} column hints:")
    for col, hint in hints.items():
        print(f"  {col}: {hint}")
    
    print("\n📋 Schema Summary:")
    summary = analyzer.get_schema_summary("ProductionTestTable")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n⚙️ Complete Config Section:")
    config = analyzer.generate_config_section("ProductionTestTable")
    import json
    print(json.dumps(config, indent=2))