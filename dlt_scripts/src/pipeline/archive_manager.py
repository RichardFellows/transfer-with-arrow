#!/usr/bin/env python3
"""
Archive manager for parquet file storage and batch management.
Central coordinator for all archive operations including storage, retrieval, and cleanup.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import logging

from ..utils.parquet_utils import ParquetUtils, ParquetFileInfo
from ..utils.manifest_manager import ManifestManager, ExtractionBatch, BatchStatus


class ArchiveManager:
    """Manages the parquet archive storage and batch operations."""
    
    def __init__(
        self,
        archive_path: Path,
        manifest_path: Path,
        retention_days: int = 90,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize archive manager.
        
        Args:
            archive_path: Root path for parquet archive storage
            manifest_path: Path for manifest storage
            retention_days: Number of days to retain archives
            logger: Logger instance
        """
        self.archive_path = Path(archive_path)
        self.manifest_path = Path(manifest_path)
        self.retention_days = retention_days
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.parquet_utils = ParquetUtils(self.logger)
        self.manifest_manager = ManifestManager(self.manifest_path, self.logger)
        
        # Ensure directories exist
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.manifest_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Archive manager initialized:")
        self.logger.info(f"  Archive path: {self.archive_path}")
        self.logger.info(f"  Manifest path: {self.manifest_path}")
        self.logger.info(f"  Retention: {self.retention_days} days")
    
    def generate_batch_id(self, table_name: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a unique batch ID for extraction.
        
        Args:
            table_name: Name of the table
            timestamp: Timestamp for the batch (defaults to now)
            
        Returns:
            Unique batch identifier
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format: TableName_YYYYMMDD_HHMMSS
        batch_id = f"{table_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        return batch_id
    
    def get_table_archive_path(self, table_name: str, batch_id: str) -> Path:
        """
        Get the archive path for a specific table and batch.
        
        Args:
            table_name: Name of the table
            batch_id: Batch identifier
            
        Returns:
            Path to the batch archive directory
        """
        return self.archive_path / table_name / batch_id
    
    def create_extraction_batch(
        self,
        table_name: str,
        source_query: Optional[str] = None,
        watermark_value: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> Tuple[str, ExtractionBatch]:
        """
        Create a new extraction batch.
        
        Args:
            table_name: Name of the table to extract
            source_query: SQL query for extraction
            watermark_value: Incremental loading watermark
            metadata: Additional metadata
            timestamp: Batch timestamp (defaults to now)
            
        Returns:
            Tuple of (batch_id, extraction_batch)
        """
        try:
            # Generate batch ID
            batch_id = self.generate_batch_id(table_name, timestamp)
            
            # Create batch record
            batch = self.manifest_manager.create_batch(
                batch_id=batch_id,
                table_name=table_name,
                source_query=source_query,
                watermark_value=watermark_value,
                metadata=metadata
            )
            
            # Create archive directory
            archive_path = self.get_table_archive_path(table_name, batch_id)
            archive_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Created extraction batch {batch_id} for table {table_name}")
            
            return batch_id, batch
            
        except Exception as e:
            self.logger.error(f"Failed to create extraction batch: {e}")
            raise
    
    def store_extraction_data(
        self,
        batch_id: str,
        table_name: str,
        data: Any,
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ParquetFileInfo:
        """
        Store extracted data as parquet in the archive.
        
        Args:
            batch_id: Batch identifier
            table_name: Name of the table
            data: Data to store (DataFrame or Arrow Table)
            partition_cols: Columns to partition by
            compression: Compression algorithm
            metadata: Additional metadata
            
        Returns:
            Information about the stored parquet file
        """
        try:
            # Update batch status
            self.manifest_manager.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.EXTRACTING
            )
            
            # Get archive path
            archive_path = self.get_table_archive_path(table_name, batch_id)
            
            # Write parquet data
            file_info = self.parquet_utils.write_parquet_dataset(
                data=data,
                output_path=archive_path,
                table_name=table_name,
                batch_id=batch_id,
                partition_cols=partition_cols,
                compression=compression,
                metadata=metadata
            )
            
            # Update batch with results
            self.manifest_manager.update_batch_results(
                batch_id=batch_id,
                row_count=file_info.row_count or 0,
                file_path=str(file_info.path),
                file_size_bytes=file_info.size_bytes
            )
            
            # Mark as completed
            self.manifest_manager.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.COMPLETED,
                completed_at=datetime.now()
            )
            
            self.logger.info(f"Successfully stored extraction data for batch {batch_id}")
            self.logger.info(f"  Rows: {file_info.row_count:,}, Size: {file_info.size_bytes:,} bytes")
            
            return file_info
            
        except Exception as e:
            # Mark batch as failed
            self.manifest_manager.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now()
            )
            
            self.logger.error(f"Failed to store extraction data for batch {batch_id}: {e}")
            raise
    
    def load_extraction_data(
        self,
        batch_id: str,
        table_name: str,
        columns: Optional[List[str]] = None,
        filters: Optional[List[Any]] = None
    ) -> Any:
        """
        Load data from a specific extraction batch.
        
        Args:
            batch_id: Batch identifier
            table_name: Name of the table
            columns: Specific columns to load
            filters: Row filters to apply
            
        Returns:
            Arrow Table with the data
        """
        try:
            # Get batch info
            batch = self.manifest_manager.get_batch(batch_id)
            if not batch:
                raise ValueError(f"Batch {batch_id} not found")
            
            if batch.status != BatchStatus.COMPLETED:
                raise ValueError(f"Batch {batch_id} is not completed (status: {batch.status})")
            
            # Update status to loading
            self.manifest_manager.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.LOADING
            )
            
            # Load parquet data
            archive_path = self.get_table_archive_path(table_name, batch_id)
            data = self.parquet_utils.read_parquet_dataset(
                input_path=archive_path,
                columns=columns,
                filters=filters
            )
            
            # Update status to loaded
            self.manifest_manager.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.LOADED
            )
            
            self.logger.info(f"Successfully loaded data from batch {batch_id}")
            self.logger.info(f"  Rows: {len(data):,}, Columns: {len(data.schema)}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load data from batch {batch_id}: {e}")
            raise
    
    def list_available_batches(
        self,
        table_name: Optional[str] = None,
        status: Optional[BatchStatus] = None,
        last_n: Optional[int] = None
    ) -> List[ExtractionBatch]:
        """
        List available extraction batches.
        
        Args:
            table_name: Filter by table name
            status: Filter by status
            last_n: Return only the last N batches
            
        Returns:
            List of available extraction batches
        """
        return self.manifest_manager.list_batches(
            table_name=table_name,
            status=status,
            limit=last_n
        )
    
    def get_latest_batch(
        self,
        table_name: str,
        status: Optional[BatchStatus] = BatchStatus.COMPLETED
    ) -> Optional[ExtractionBatch]:
        """
        Get the latest extraction batch for a table.
        
        Args:
            table_name: Table name
            status: Status filter (defaults to COMPLETED)
            
        Returns:
            Latest extraction batch or None
        """
        return self.manifest_manager.get_latest_batch(
            table_name=table_name,
            status=status
        )
    
    def get_batches_in_date_range(
        self,
        table_name: str,
        start_date: datetime,
        end_date: datetime,
        status: Optional[BatchStatus] = BatchStatus.COMPLETED
    ) -> List[ExtractionBatch]:
        """
        Get extraction batches within a date range.
        
        Args:
            table_name: Table name
            start_date: Start date (inclusive)
            end_date: End date (inclusive) 
            status: Status filter
            
        Returns:
            List of extraction batches in the date range
        """
        all_batches = self.manifest_manager.list_batches(
            table_name=table_name,
            status=status
        )
        
        # Filter by date range
        filtered_batches = [
            batch for batch in all_batches
            if start_date <= batch.created_at <= end_date
        ]
        
        return filtered_batches
    
    def get_batch_info(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a batch.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Dictionary with batch information
        """
        try:
            batch = self.manifest_manager.get_batch(batch_id)
            if not batch:
                return None
            
            info = batch.to_dict()
            
            # Add file system information if file exists
            if batch.file_path:
                file_path = Path(batch.file_path)
                if file_path.exists():
                    try:
                        parquet_metadata = self.parquet_utils.get_parquet_metadata(file_path)
                        info["parquet_metadata"] = parquet_metadata
                        info["file_valid"] = self.parquet_utils.validate_parquet_file(file_path)
                    except Exception as e:
                        info["parquet_metadata"] = None
                        info["file_valid"] = False
                        info["validation_error"] = str(e)
                else:
                    info["file_exists"] = False
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get batch info for {batch_id}: {e}")
            return None
    
    def cleanup_archive(
        self,
        older_than_days: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, int]:
        """
        Clean up old archives and batch records.
        
        Args:
            older_than_days: Remove archives older than this (defaults to retention_days)
            dry_run: If True, only report what would be cleaned
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            if older_than_days is None:
                older_than_days = self.retention_days
            
            results = {}
            
            # Clean up parquet files
            deleted_files = self.parquet_utils.cleanup_parquet_files(
                directory=self.archive_path,
                older_than_days=older_than_days,
                dry_run=dry_run
            )
            results["parquet_files_deleted"] = len(deleted_files)
            
            # Clean up batch records
            deleted_batches = self.manifest_manager.cleanup_old_batches(
                older_than_days=older_than_days,
                dry_run=dry_run
            )
            results["batch_records_deleted"] = deleted_batches
            
            if dry_run:
                self.logger.info(f"Cleanup dry run completed - would delete {len(deleted_files)} files and {deleted_batches} batch records")
            else:
                self.logger.info(f"Cleanup completed - deleted {len(deleted_files)} files and {deleted_batches} batch records")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup archive: {e}")
            return {}
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive archive statistics.
        
        Returns:
            Dictionary with archive statistics
        """
        try:
            # Get batch statistics from manifest
            batch_stats = self.manifest_manager.get_batch_statistics()
            
            # Get file system statistics
            total_size = 0
            file_count = 0
            
            for parquet_file in self.archive_path.rglob("*.parquet"):
                if parquet_file.is_file():
                    total_size += parquet_file.stat().st_size
                    file_count += 1
            
            # Get table statistics
            table_stats = {}
            for table_dir in self.archive_path.iterdir():
                if table_dir.is_dir():
                    table_size = sum(
                        f.stat().st_size 
                        for f in table_dir.rglob("*.parquet")
                        if f.is_file()
                    )
                    table_file_count = len(list(table_dir.rglob("*.parquet")))
                    
                    table_stats[table_dir.name] = {
                        "size_bytes": table_size,
                        "size_mb": round(table_size / 1024 / 1024, 2),
                        "file_count": table_file_count
                    }
            
            return {
                "batch_statistics": batch_stats,
                "filesystem_statistics": {
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / 1024 / 1024, 2),
                    "total_size_gb": round(total_size / 1024 / 1024 / 1024, 2),
                    "total_files": file_count,
                    "archive_path": str(self.archive_path),
                    "retention_days": self.retention_days
                },
                "table_statistics": table_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get archive statistics: {e}")
            return {}
    
    def validate_archive_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the archive.
        
        Returns:
            Dictionary with validation results
        """
        try:
            results = {
                "valid_batches": 0,
                "invalid_batches": 0,
                "missing_files": 0,
                "corrupted_files": 0,
                "orphaned_files": 0,
                "issues": []
            }
            
            # Check all completed batches
            batches = self.manifest_manager.list_batches(status=BatchStatus.COMPLETED)
            
            for batch in batches:
                if not batch.file_path:
                    results["issues"].append(f"Batch {batch.batch_id} missing file path")
                    results["invalid_batches"] += 1
                    continue
                
                file_path = Path(batch.file_path)
                
                # Check if file exists
                if not file_path.exists():
                    results["issues"].append(f"Missing file for batch {batch.batch_id}: {file_path}")
                    results["missing_files"] += 1
                    results["invalid_batches"] += 1
                    continue
                
                # Validate parquet file
                if not self.parquet_utils.validate_parquet_file(file_path):
                    results["issues"].append(f"Corrupted parquet file for batch {batch.batch_id}: {file_path}")
                    results["corrupted_files"] += 1
                    results["invalid_batches"] += 1
                    continue
                
                results["valid_batches"] += 1
            
            # Check for orphaned files (files without batch records)
            all_parquet_files = set(self.archive_path.rglob("*.parquet"))
            referenced_files = set()
            
            for batch in self.manifest_manager.list_batches():
                if batch.file_path:
                    referenced_files.add(Path(batch.file_path))
            
            orphaned_files = all_parquet_files - referenced_files
            results["orphaned_files"] = len(orphaned_files)
            
            for orphaned_file in orphaned_files:
                results["issues"].append(f"Orphaned parquet file: {orphaned_file}")
            
            self.logger.info(f"Archive validation completed:")
            self.logger.info(f"  Valid batches: {results['valid_batches']}")
            self.logger.info(f"  Invalid batches: {results['invalid_batches']}")
            self.logger.info(f"  Issues found: {len(results['issues'])}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to validate archive integrity: {e}")
            return {"error": str(e)}