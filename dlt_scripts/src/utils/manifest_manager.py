#!/usr/bin/env python3
"""
Manifest manager for tracking extraction batches and metadata.
Maintains records of all extractions, their status, and metadata.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class BatchStatus(str, Enum):
    """Status of extraction batches."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"
    LOADING = "loading"
    LOADED = "loaded"
    ARCHIVED = "archived"


@dataclass
class ExtractionBatch:
    """Information about an extraction batch."""
    batch_id: str
    table_name: str
    status: BatchStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    source_query: Optional[str] = None
    row_count: Optional[int] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    watermark_value: Optional[Union[str, int]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with datetime serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionBatch":
        """Create from dictionary with datetime deserialization."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        data["status"] = BatchStatus(data["status"])
        return cls(**data)


class ManifestManager:
    """Manages extraction batch metadata and manifests."""
    
    def __init__(self, manifest_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize manifest manager.
        
        Args:
            manifest_dir: Directory to store manifest files
            logger: Logger instance
        """
        self.manifest_dir = Path(manifest_dir)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.manifest_dir / "extractions.db"
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for manifest storage."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS extraction_batches (
                        batch_id TEXT PRIMARY KEY,
                        table_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        completed_at TEXT NULL,
                        source_query TEXT NULL,
                        row_count INTEGER NULL,
                        file_path TEXT NULL,
                        file_size_bytes INTEGER NULL,
                        watermark_value TEXT NULL,
                        error_message TEXT NULL,
                        metadata TEXT NULL
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_table_status 
                    ON extraction_batches(table_name, status)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON extraction_batches(created_at)
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize manifest database: {e}")
            raise
    
    def create_batch(
        self,
        batch_id: str,
        table_name: str,
        source_query: Optional[str] = None,
        watermark_value: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ) -> ExtractionBatch:
        """
        Create a new extraction batch record.
        
        Args:
            batch_id: Unique batch identifier
            table_name: Name of the table being extracted
            source_query: SQL query used for extraction
            watermark_value: Incremental loading watermark value
            metadata: Additional metadata
            
        Returns:
            Created extraction batch
        """
        try:
            batch = ExtractionBatch(
                batch_id=batch_id,
                table_name=table_name,
                status=BatchStatus.PENDING,
                created_at=created_at if created_at is not None else datetime.now(),
                source_query=source_query,
                watermark_value=watermark_value,
                metadata=metadata or {}
            )
            
            self._save_batch(batch)
            
            self.logger.info(f"Created extraction batch: {batch_id} for table {table_name}")
            return batch
            
        except Exception as e:
            self.logger.error(f"Failed to create batch {batch_id}: {e}")
            raise
    
    def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update the status of an extraction batch.
        
        Args:
            batch_id: Batch identifier
            status: New status
            error_message: Error message if status is FAILED
            completed_at: Completion timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Get current batch
                cursor.execute(
                    "SELECT * FROM extraction_batches WHERE batch_id = ?",
                    (batch_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    self.logger.warning(f"Batch {batch_id} not found")
                    return False
                
                # Update status
                if completed_at is not None:
                    # Only update completed_at if explicitly provided
                    completed_at_str = completed_at.isoformat()
                    cursor.execute("""
                        UPDATE extraction_batches 
                        SET status = ?, error_message = ?, completed_at = ?
                        WHERE batch_id = ?
                    """, (status.value, error_message, completed_at_str, batch_id))
                else:
                    # Don't update completed_at if not provided (preserve existing value)
                    cursor.execute("""
                        UPDATE extraction_batches 
                        SET status = ?, error_message = ?
                        WHERE batch_id = ?
                    """, (status.value, error_message, batch_id))
                
                conn.commit()
                
                self.logger.info(f"Updated batch {batch_id} status to {status.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update batch status: {e}")
            return False
    
    def update_batch_results(
        self,
        batch_id: str,
        row_count: int,
        file_path: str,
        file_size_bytes: int
    ) -> bool:
        """
        Update batch with extraction results.
        
        Args:
            batch_id: Batch identifier
            row_count: Number of rows extracted
            file_path: Path to the parquet file
            file_size_bytes: Size of the file in bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE extraction_batches 
                    SET row_count = ?, file_path = ?, file_size_bytes = ?
                    WHERE batch_id = ?
                """, (row_count, file_path, file_size_bytes, batch_id))
                
                conn.commit()
                
                self.logger.info(f"Updated batch {batch_id} results: {row_count:,} rows, {file_size_bytes:,} bytes")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update batch results: {e}")
            return False
    
    def get_batch(self, batch_id: str) -> Optional[ExtractionBatch]:
        """
        Get extraction batch by ID.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Extraction batch or None if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM extraction_batches WHERE batch_id = ?",
                    (batch_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_batch(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get batch {batch_id}: {e}")
            return None
    
    def list_batches(
        self,
        table_name: Optional[str] = None,
        status: Optional[BatchStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ExtractionBatch]:
        """
        List extraction batches with optional filtering.
        
        Args:
            table_name: Filter by table name
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of extraction batches
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM extraction_batches"
                params = []
                where_clauses = []
                
                if table_name:
                    where_clauses.append("table_name = ?")
                    params.append(table_name)
                
                if status:
                    where_clauses.append("status = ?")
                    params.append(status.value)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                if offset:
                    query += f" OFFSET {offset}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_batch(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to list batches: {e}")
            return []
    
    def get_latest_batch(
        self,
        table_name: str,
        status: Optional[BatchStatus] = None
    ) -> Optional[ExtractionBatch]:
        """
        Get the latest batch for a table.
        
        Args:
            table_name: Table name
            status: Optional status filter
            
        Returns:
            Latest extraction batch or None
        """
        batches = self.list_batches(
            table_name=table_name,
            status=status,
            limit=1
        )
        return batches[0] if batches else None
    
    def cleanup_old_batches(
        self,
        older_than_days: int,
        status: Optional[BatchStatus] = None,
        dry_run: bool = True
    ) -> int:
        """
        Clean up old batch records.
        
        Args:
            older_than_days: Remove batches older than this many days
            status: Only remove batches with this status (optional)
            dry_run: If True, only count batches that would be deleted
            
        Returns:
            Number of batches deleted (or would be deleted)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                query = "SELECT COUNT(*) FROM extraction_batches WHERE created_at < ?"
                params = [cutoff_date.isoformat()]
                
                if status:
                    query = query.replace("WHERE", "WHERE status = ? AND")
                    params.insert(0, status.value)
                
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                
                if not dry_run and count > 0:
                    delete_query = query.replace("SELECT COUNT(*)", "DELETE")
                    cursor.execute(delete_query, params)
                    conn.commit()
                    
                    self.logger.info(f"Deleted {count} old batch records older than {older_than_days} days")
                else:
                    self.logger.info(f"Dry run: Would delete {count} batch records older than {older_than_days} days")
                
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old batches: {e}")
            return 0
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extraction batches.
        
        Returns:
            Dictionary with batch statistics
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Total batches
                cursor.execute("SELECT COUNT(*) FROM extraction_batches")
                total_batches = cursor.fetchone()[0]
                
                # Batches by status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM extraction_batches 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Batches by table
                cursor.execute("""
                    SELECT table_name, COUNT(*) 
                    FROM extraction_batches 
                    GROUP BY table_name
                """)
                table_counts = dict(cursor.fetchall())
                
                # Total data extracted
                cursor.execute("""
                    SELECT 
                        SUM(row_count) as total_rows,
                        SUM(file_size_bytes) as total_size_bytes
                    FROM extraction_batches 
                    WHERE status = 'completed'
                """)
                row = cursor.fetchone()
                total_rows = row[0] or 0
                total_size_bytes = row[1] or 0
                
                return {
                    "total_batches": total_batches,
                    "status_counts": status_counts,
                    "table_counts": table_counts,
                    "total_rows_extracted": total_rows,
                    "total_size_bytes": total_size_bytes,
                    "total_size_mb": round(total_size_bytes / 1024 / 1024, 2)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get batch statistics: {e}")
            return {}
    
    def _save_batch(self, batch: ExtractionBatch):
        """Save batch to database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO extraction_batches
                (batch_id, table_name, status, created_at, completed_at, source_query,
                 row_count, file_path, file_size_bytes, watermark_value, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch.batch_id,
                batch.table_name,
                batch.status.value,
                batch.created_at.isoformat(),
                batch.completed_at.isoformat() if batch.completed_at else None,
                batch.source_query,
                batch.row_count,
                batch.file_path,
                batch.file_size_bytes,
                str(batch.watermark_value) if batch.watermark_value is not None else None,
                batch.error_message,
                json.dumps(batch.metadata) if batch.metadata else None
            ))
            
            conn.commit()
    
    def _row_to_batch(self, row: sqlite3.Row) -> ExtractionBatch:
        """Convert database row to ExtractionBatch."""
        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except:
                pass
        
        return ExtractionBatch(
            batch_id=row["batch_id"],
            table_name=row["table_name"],
            status=BatchStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            source_query=row["source_query"],
            row_count=row["row_count"],
            file_path=row["file_path"],
            file_size_bytes=row["file_size_bytes"],
            watermark_value=row["watermark_value"],
            error_message=row["error_message"],
            metadata=metadata
        )