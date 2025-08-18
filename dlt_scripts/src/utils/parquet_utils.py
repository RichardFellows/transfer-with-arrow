#!/usr/bin/env python3
"""
Parquet utilities for archive management and file operations.
Provides functionality for reading, writing, and managing parquet files in the archive.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import fs


class ParquetFileInfo:
    """Information about a parquet file or dataset."""
    
    def __init__(
        self, 
        path: Path,
        table_name: str,
        batch_id: str,
        created_at: datetime,
        size_bytes: int,
        row_count: Optional[int] = None,
        schema_info: Optional[Dict[str, Any]] = None
    ):
        self.path = path
        self.table_name = table_name
        self.batch_id = batch_id
        self.created_at = created_at
        self.size_bytes = size_bytes
        self.row_count = row_count
        self.schema_info = schema_info or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": str(self.path),
            "table_name": self.table_name,
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "row_count": self.row_count,
            "schema_info": self.schema_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParquetFileInfo":
        """Create from dictionary representation."""
        return cls(
            path=Path(data["path"]),
            table_name=data["table_name"],
            batch_id=data["batch_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            size_bytes=data["size_bytes"],
            row_count=data.get("row_count"),
            schema_info=data.get("schema_info", {})
        )


class ParquetUtils:
    """Utility class for parquet file operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize parquet utilities.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def write_parquet_dataset(
        self,
        data: Union[pd.DataFrame, pa.Table], 
        output_path: Path,
        table_name: str,
        batch_id: str,
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ParquetFileInfo:
        """
        Write data to parquet format with metadata.
        
        Args:
            data: Data to write (DataFrame or Arrow Table)
            output_path: Output directory path
            table_name: Name of the table
            batch_id: Unique batch identifier
            partition_cols: Columns to partition by
            compression: Compression algorithm
            metadata: Additional metadata to store
            
        Returns:
            Information about the written parquet file
        """
        try:
            # Ensure output directory exists
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Convert to Arrow Table if needed
            if isinstance(data, pd.DataFrame):
                table = pa.Table.from_pandas(data)
            else:
                table = data
            
            # Fix chunked array issues - combine chunks and ensure consistent structure
            if hasattr(table, 'combine_chunks'):
                try:
                    table = table.combine_chunks()
                    self.logger.debug("Combined chunked arrays for parquet serialization")
                except Exception as e:
                    self.logger.warning(f"Failed to combine chunks: {e}")
            
            # Additional validation and flattening for complex nested structures
            if hasattr(table, 'to_pandas') and hasattr(table, 'from_pandas'):
                try:
                    # Convert through pandas to normalize the data structure
                    # This handles complex nested arrays that can't be serialized directly
                    temp_df = table.to_pandas()
                    table = pa.Table.from_pandas(temp_df)
                    self.logger.debug("Normalized table structure via pandas conversion")
                except Exception as e:
                    self.logger.warning(f"Failed to normalize via pandas: {e}")
                    # Continue with original table if normalization fails
            
            # Add metadata to schema
            if metadata:
                existing_metadata = table.schema.metadata or {}
                updated_metadata = {
                    **existing_metadata,
                    b"table_name": table_name.encode(),
                    b"batch_id": batch_id.encode(),
                    b"created_at": datetime.now().isoformat().encode(),
                    b"custom_metadata": json.dumps(metadata).encode()
                }
                table = table.replace_schema_metadata(updated_metadata)
            
            # Write parquet file
            if partition_cols:
                # Write partitioned dataset
                pq.write_to_dataset(
                    table,
                    root_path=str(output_path),
                    partition_cols=partition_cols,
                    compression=compression
                )
                file_path = output_path
            else:
                # Write single parquet file
                file_path = output_path / f"{table_name}_{batch_id}.parquet"
                pq.write_table(
                    table,
                    str(file_path),
                    compression=compression
                )
            
            # Get file size
            if file_path.is_file():
                size_bytes = file_path.stat().st_size
            else:
                # Calculate total size for partitioned datasets
                size_bytes = sum(
                    f.stat().st_size 
                    for f in file_path.rglob("*.parquet")
                )
            
            # Create file info
            file_info = ParquetFileInfo(
                path=file_path,
                table_name=table_name,
                batch_id=batch_id,
                created_at=datetime.now(),
                size_bytes=size_bytes,
                row_count=len(table),
                schema_info={
                    "columns": [field.name for field in table.schema],
                    "dtypes": {field.name: str(field.type) for field in table.schema},
                    "compression": compression,
                    "partitioned": partition_cols is not None
                }
            )
            
            self.logger.info(f"Successfully wrote parquet dataset: {file_path}")
            self.logger.info(f"  Rows: {len(table):,}, Size: {size_bytes:,} bytes")
            
            return file_info
            
        except Exception as e:
            self.logger.error(f"Failed to write parquet dataset: {e}")
            raise
    
    def read_parquet_dataset(
        self,
        input_path: Path,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Any]] = None
    ) -> pa.Table:
        """
        Read parquet dataset from file or directory.
        
        Args:
            input_path: Path to parquet file or directory
            columns: Specific columns to read
            filters: Row filters to apply
            
        Returns:
            Arrow Table with the data
        """
        try:
            if input_path.is_file():
                # Single parquet file
                table = pq.read_table(
                    str(input_path),
                    columns=columns,
                    filters=filters
                )
            else:
                # Partitioned dataset
                dataset = pq.ParquetDataset(str(input_path))
                table = dataset.read(columns=columns)
                
                # Apply filters manually if provided
                if filters:
                    # Note: Manual filtering would need to be implemented here
                    # For now, we'll read all data and let the caller filter
                    pass
            
            self.logger.info(f"Successfully read parquet dataset: {input_path}")
            self.logger.info(f"  Rows: {len(table):,}, Columns: {len(table.schema)}")
            
            return table
            
        except Exception as e:
            self.logger.error(f"Failed to read parquet dataset: {e}")
            raise
    
    def get_parquet_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from parquet file.
        
        Args:
            file_path: Path to parquet file
            
        Returns:
            Dictionary containing metadata
        """
        try:
            if file_path.is_file():
                # Single file
                parquet_file = pq.ParquetFile(str(file_path))
                metadata = parquet_file.metadata
                schema = parquet_file.schema
                
                # Extract custom metadata
                custom_metadata = {}
                if metadata.metadata:
                    for key, value in metadata.metadata.items():
                        try:
                            custom_metadata[key.decode()] = value.decode()
                        except:
                            pass
                
                return {
                    "num_rows": metadata.num_rows,
                    "num_columns": len(schema),
                    "file_size_bytes": file_path.stat().st_size,
                    "schema": [{"name": field.name, "type": str(field.physical_type)} for field in schema],
                    "custom_metadata": custom_metadata,
                    "created": parquet_file.metadata.created_by
                }
            else:
                # Dataset directory
                dataset = pq.ParquetDataset(str(file_path))
                schema = dataset.schema
                
                total_size = sum(f.stat().st_size for f in file_path.rglob("*.parquet"))
                
                return {
                    "num_files": len(list(file_path.rglob("*.parquet"))),
                    "num_columns": len(schema),
                    "total_size": total_size,
                    "schema": [{"name": field.name, "type": str(field.type)} for field in schema],
                    "partitioned": True
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get parquet metadata: {e}")
            raise
    
    def validate_parquet_file(self, file_path: Path) -> bool:
        """
        Validate that a parquet file is readable and not corrupted.
        
        Args:
            file_path: Path to parquet file or directory
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if file_path.is_file():
                # Validate single file
                parquet_file = pq.ParquetFile(str(file_path))
                # Try to read schema and first row group
                schema = parquet_file.schema
                if parquet_file.metadata.num_row_groups > 0:
                    parquet_file.read_row_group(0, columns=[schema[0].name])
            else:
                # Validate dataset
                dataset = pq.ParquetDataset(str(file_path))
                # Try to read schema and a small sample
                schema = dataset.schema
                dataset.read(columns=[schema[0].name]).slice(0, 1)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Parquet validation failed for {file_path}: {e}")
            return False
    
    def cleanup_parquet_files(
        self,
        directory: Path,
        older_than_days: int,
        dry_run: bool = True
    ) -> List[Path]:
        """
        Clean up old parquet files based on age.
        
        Args:
            directory: Directory to clean
            older_than_days: Remove files older than this many days
            dry_run: If True, only return files that would be deleted
            
        Returns:
            List of files that were (or would be) deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            files_to_delete = []
            
            for parquet_file in directory.rglob("*.parquet"):
                if parquet_file.is_file():
                    file_modified = datetime.fromtimestamp(parquet_file.stat().st_mtime)
                    if file_modified < cutoff_date:
                        files_to_delete.append(parquet_file)
                        
                        if not dry_run:
                            parquet_file.unlink()
                            self.logger.info(f"Deleted old parquet file: {parquet_file}")
            
            # Clean up empty directories
            if not dry_run:
                for dir_path in directory.rglob("*"):
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        self.logger.info(f"Removed empty directory: {dir_path}")
            
            if dry_run:
                self.logger.info(f"Dry run: Would delete {len(files_to_delete)} files older than {older_than_days} days")
            else:
                self.logger.info(f"Deleted {len(files_to_delete)} files older than {older_than_days} days")
            
            return files_to_delete
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup parquet files: {e}")
            raise