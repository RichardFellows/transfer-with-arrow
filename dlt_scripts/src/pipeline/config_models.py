#!/usr/bin/env python3

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class WriteDisposition(str, Enum):
    """Supported write dispositions for DLT."""
    REPLACE = "replace"
    APPEND = "append"
    MERGE = "merge"


class BackendType(str, Enum):
    """Supported DLT backend types."""
    PYARROW = "pyarrow"
    PANDAS = "pandas"
    SQLALCHEMY = "sqlalchemy"


class IncrementalStrategy(str, Enum):
    """Supported incremental loading strategies."""
    TIMESTAMP = "timestamp"
    SEQUENCE = "sequence"
    CUSTOM = "custom"


class LogLevel(str, Enum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ConnectionConfig(BaseModel):
    """Database connection configuration."""
    connection_string: str = Field(..., description="Database connection string")
    schema_name: str = Field(default="dbo", description="Default schema name", alias="schema")
    timeout: Optional[int] = Field(default=30, description="Connection timeout in seconds")
    
    @field_validator('connection_string')
    @classmethod
    def validate_connection_string(cls, v):
        if not v or not v.strip():
            raise ValueError("Connection string cannot be empty")
        return v.strip()


class IncrementalConfig(BaseModel):
    """Incremental loading configuration for a table."""
    enabled: bool = Field(default=False, description="Enable incremental loading")
    strategy: IncrementalStrategy = Field(default=IncrementalStrategy.TIMESTAMP, description="Incremental strategy")
    watermark_column: Optional[str] = Field(None, description="Column to use for incremental loading")
    initial_value: Optional[Union[str, int, datetime]] = Field(None, description="Initial watermark value")
    
    @model_validator(mode='after')
    def validate_incremental_fields(self):
        if self.enabled:
            if not self.watermark_column:
                raise ValueError("watermark_column is required when incremental is enabled")
            if self.initial_value is None:
                raise ValueError("initial_value is required when incremental is enabled")
        return self


class TableConfig(BaseModel):
    """Configuration for a single table migration."""
    source_table: str = Field(..., description="Source table name (can include schema)")
    destination_table: Optional[str] = Field(None, description="Destination table name (defaults to source)")
    disposition: WriteDisposition = Field(default=WriteDisposition.REPLACE, description="Write disposition")
    incremental: IncrementalConfig = Field(default_factory=IncrementalConfig, description="Incremental settings")
    primary_key: Optional[List[str]] = Field(None, description="Primary key columns for merge operations")
    where_clause: Optional[str] = Field(None, description="Custom WHERE clause for source data")
    column_mapping: Optional[Dict[str, str]] = Field(None, description="Column name mapping (source -> dest)")
    custom_sql: Optional[str] = Field(None, description="Custom SQL query instead of table name")
    enabled: bool = Field(default=True, description="Whether to process this table")
    
    @model_validator(mode='after')
    def validate_table_config(self):
        # Set default destination table if not provided
        if self.destination_table is None:
            # Extract table name from schema.table format
            self.destination_table = self.source_table.split('.')[-1].lower()
        
        # Validate primary key for merge disposition
        if self.disposition == WriteDisposition.MERGE and not self.primary_key:
            raise ValueError("primary_key is required when disposition is 'merge'")
        
        return self


class PipelineConfig(BaseModel):
    """Main pipeline configuration."""
    name: str = Field(default="data_migration", description="Pipeline name")
    dataset_name: str = Field(default="migrated_data", description="Dataset name in destination")
    chunk_size: int = Field(default=10000, description="Chunk size for data processing")
    backend: BackendType = Field(default=BackendType.PYARROW, description="DLT backend to use")
    loader_file_format: str = Field(default="parquet", description="File format for loading")
    reflection_level: str = Field(default="full_with_precision", description="Schema reflection level")
    backend_kwargs: Dict[str, Any] = Field(default_factory=lambda: {"tz": "UTC"}, description="Backend-specific kwargs")
    preserve_column_names: bool = Field(default=False, description="Preserve original column names (disable snake_case transformation)")
    
    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError("chunk_size must be positive")
        return v


class VerificationConfig(BaseModel):
    """Data verification configuration."""
    enabled: bool = Field(default=True, description="Enable verification")
    tables: Optional[List[str]] = Field(None, description="Tables to verify (None = all tables)")
    tolerance: int = Field(default=0, description="Allowed row count difference")
    custom_checks: Optional[Dict[str, str]] = Field(None, description="Custom verification SQL queries")
    
    @field_validator('tolerance')
    @classmethod
    def validate_tolerance(cls, v):
        if v < 0:
            raise ValueError("tolerance cannot be negative")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(None, description="Log file path (None = console only)")
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files to keep")


class ConfigurationModel(BaseModel):
    """Root configuration model."""
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig, description="Pipeline settings")
    connections: Dict[str, ConnectionConfig] = Field(..., description="Database connections")
    tables: Dict[str, TableConfig] = Field(..., description="Table configurations")
    verification: VerificationConfig = Field(default_factory=VerificationConfig, description="Verification settings")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    
    @model_validator(mode='after')
    def validate_configuration(self):
        # Validate connections
        if 'source' not in self.connections:
            raise ValueError("'source' connection is required")
        if 'destination' not in self.connections:
            raise ValueError("'destination' connection is required")
        
        # Validate tables
        if not self.tables:
            raise ValueError("At least one table configuration is required")
        
        # Validate enabled tables have source_table
        for table_name, config in self.tables.items():
            if config.enabled and not config.source_table:
                raise ValueError(f"source_table is required for table '{table_name}'")
        
        return self


# Utility functions for working with configurations
def get_enabled_tables(config: ConfigurationModel) -> Dict[str, TableConfig]:
    """Get only enabled table configurations."""
    return {name: table for name, table in config.tables.items() if table.enabled}


def get_incremental_tables(config: ConfigurationModel) -> Dict[str, TableConfig]:
    """Get table configurations that have incremental loading enabled."""
    return {
        name: table 
        for name, table in config.tables.items() 
        if table.enabled and table.incremental.enabled
    }


def get_verification_tables(config: ConfigurationModel) -> List[str]:
    """Get list of tables to verify."""
    if config.verification.tables:
        return config.verification.tables
    return list(get_enabled_tables(config).keys())