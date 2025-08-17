#!/usr/bin/env python3
"""
Comprehensive verification script for incremental sync testing
Validates record counts, schema consistency, and data integrity between source and destination
"""

import sys
import os
import sqlalchemy as sa
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IncrementalSyncVerifier:
    """Verifies incremental sync results between source and destination databases"""
    
    def __init__(self, source_conn_str: str, dest_conn_str: str):
        self.source_conn_str = source_conn_str
        self.dest_conn_str = dest_conn_str
        self.source_engine = sa.create_engine(source_conn_str)
        self.dest_engine = sa.create_engine(dest_conn_str)
    
    def verify_record_counts_by_calendar_id(self) -> Dict[str, Any]:
        """Verify record counts match by SystemCalendarID between source and destination"""
        logger.info("🔍 Verifying record counts by SystemCalendarID...")
        
        # Query source counts
        source_query = """
        SELECT 
            SystemCalendarID,
            COUNT(*) as RecordCount
        FROM dbo.Reporting_Client 
        GROUP BY SystemCalendarID 
        ORDER BY SystemCalendarID
        """
        
        # Query destination counts (table name might be different)
        dest_query = """
        SELECT 
            systemcalendarid,
            COUNT(*) as RecordCount
        FROM reporting_client 
        GROUP BY systemcalendarid 
        ORDER BY systemcalendarid
        """
        
        try:
            with self.source_engine.connect() as source_conn:
                source_results = source_conn.execute(sa.text(source_query)).fetchall()
            
            with self.dest_engine.connect() as dest_conn:
                dest_results = dest_conn.execute(sa.text(dest_query)).fetchall()
            
            # Convert to dictionaries for comparison
            source_counts = {row[0]: row[1] for row in source_results}
            dest_counts = {row[0]: row[1] for row in dest_results}
            
            # Compare counts
            verification_results = {
                "status": "success",
                "source_calendar_ids": len(source_counts),
                "dest_calendar_ids": len(dest_counts),
                "total_source_records": sum(source_counts.values()),
                "total_dest_records": sum(dest_counts.values()),
                "calendar_id_details": [],
                "mismatches": [],
                "missing_in_dest": [],
                "extra_in_dest": []
            }
            
            # Check each SystemCalendarID
            all_calendar_ids = set(source_counts.keys()) | set(dest_counts.keys())
            
            for calendar_id in sorted(all_calendar_ids):
                source_count = source_counts.get(calendar_id, 0)
                dest_count = dest_counts.get(calendar_id, 0)
                
                detail = {
                    "calendar_id": calendar_id,
                    "source_count": source_count,
                    "dest_count": dest_count,
                    "match": source_count == dest_count
                }
                verification_results["calendar_id_details"].append(detail)
                
                if source_count != dest_count:
                    if source_count == 0:
                        verification_results["extra_in_dest"].append(calendar_id)
                    elif dest_count == 0:
                        verification_results["missing_in_dest"].append(calendar_id)
                    else:
                        verification_results["mismatches"].append({
                            "calendar_id": calendar_id,
                            "source_count": source_count,
                            "dest_count": dest_count,
                            "difference": dest_count - source_count
                        })
            
            # Determine overall status
            if verification_results["mismatches"] or verification_results["missing_in_dest"] or verification_results["extra_in_dest"]:
                verification_results["status"] = "failed"
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify record counts: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def verify_schema_consistency(self) -> Dict[str, Any]:
        """Verify that table schemas are consistent between source and destination"""
        logger.info("🔍 Verifying schema consistency...")
        
        source_schema_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Reporting_Client' 
        AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
        """
        
        dest_schema_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'reporting_client'
        ORDER BY ORDINAL_POSITION
        """
        
        try:
            with self.source_engine.connect() as source_conn:
                source_schema = source_conn.execute(sa.text(source_schema_query)).fetchall()
            
            with self.dest_engine.connect() as dest_conn:
                dest_schema = dest_conn.execute(sa.text(dest_schema_query)).fetchall()
            
            verification_results = {
                "status": "success",
                "source_columns": len(source_schema),
                "dest_columns": len(dest_schema),
                "schema_differences": [],
                "missing_columns": [],
                "extra_columns": [],
                "type_mismatches": []
            }
            
            # Convert to dictionaries for easier comparison
            source_cols = {row[0].lower(): row for row in source_schema}
            dest_cols = {row[0].lower(): row for row in dest_schema}
            
            # Check for missing columns in destination
            for col_name in source_cols:
                if col_name not in dest_cols:
                    verification_results["missing_columns"].append(col_name)
            
            # Check for extra columns in destination
            for col_name in dest_cols:
                if col_name not in source_cols:
                    verification_results["extra_columns"].append(col_name)
            
            # Check for type mismatches in common columns
            common_columns = set(source_cols.keys()) & set(dest_cols.keys())
            for col_name in common_columns:
                source_col = source_cols[col_name]
                dest_col = dest_cols[col_name]
                
                # Compare key attributes
                if (source_col[1] != dest_col[1] or  # DATA_TYPE
                    source_col[3] != dest_col[3] or  # NUMERIC_PRECISION
                    source_col[4] != dest_col[4]):   # NUMERIC_SCALE
                    
                    verification_results["type_mismatches"].append({
                        "column_name": col_name,
                        "source_type": f"{source_col[1]}({source_col[3]},{source_col[4]})" if source_col[3] else source_col[1],
                        "dest_type": f"{dest_col[1]}({dest_col[3]},{dest_col[4]})" if dest_col[3] else dest_col[1]
                    })
            
            # Determine overall status
            if (verification_results["missing_columns"] or 
                verification_results["extra_columns"] or 
                verification_results["type_mismatches"]):
                verification_results["status"] = "failed"
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify schema consistency: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def verify_data_integrity_sample(self, sample_size: int = 1000) -> Dict[str, Any]:
        """Verify data integrity by comparing a sample of records"""
        logger.info(f"🔍 Verifying data integrity with sample size: {sample_size}...")
        
        # Sample records from source
        source_sample_query = f"""
        SELECT TOP {sample_size}
            RecordID,
            SystemCalendarID,
            ClientID,
            AccountNumber,
            Revenue,
            NetAmount,
            IsActive,
            CreatedDate
        FROM dbo.Reporting_Client 
        ORDER BY RecordID
        """
        
        # Get corresponding records from destination
        dest_sample_query = f"""
        SELECT TOP {sample_size}
            recordid,
            systemcalendarid,
            clientid,
            accountnumber,
            revenue,
            netamount,
            isactive,
            createddate
        FROM reporting_client 
        ORDER BY recordid
        """
        
        try:
            with self.source_engine.connect() as source_conn:
                source_sample = source_conn.execute(sa.text(source_sample_query)).fetchall()
            
            with self.dest_engine.connect() as dest_conn:
                dest_sample = dest_conn.execute(sa.text(dest_sample_query)).fetchall()
            
            verification_results = {
                "status": "success",
                "sample_size": len(source_sample),
                "dest_sample_size": len(dest_sample),
                "data_mismatches": [],
                "integrity_score": 0.0
            }
            
            # Compare samples (assuming same order)
            matches = 0
            total_compared = min(len(source_sample), len(dest_sample))
            
            for i in range(total_compared):
                source_row = source_sample[i]
                dest_row = dest_sample[i]
                
                # Compare key fields
                if (source_row[0] == dest_row[0] and  # RecordID
                    source_row[1] == dest_row[1] and  # SystemCalendarID
                    source_row[2] == dest_row[2] and  # ClientID
                    str(source_row[3]) == str(dest_row[3])):  # AccountNumber
                    matches += 1
                else:
                    verification_results["data_mismatches"].append({
                        "record_id": source_row[0],
                        "source_data": source_row,
                        "dest_data": dest_row
                    })
            
            verification_results["integrity_score"] = (matches / total_compared) * 100 if total_compared > 0 else 0
            
            if verification_results["integrity_score"] < 99.0:
                verification_results["status"] = "failed"
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify data integrity: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_latest_calendar_id(self, database: str = "source") -> int:
        """Get the latest SystemCalendarID from source or destination"""
        if database == "source":
            query = "SELECT MAX(SystemCalendarID) FROM dbo.Reporting_Client"
            engine = self.source_engine
        else:
            query = "SELECT MAX(systemcalendarid) FROM reporting_client"
            engine = self.dest_engine
        
        try:
            with engine.connect() as conn:
                result = conn.execute(sa.text(query)).scalar()
                return result if result is not None else 0
        except Exception as e:
            logger.error(f"Failed to get latest calendar ID from {database}: {e}")
            return 0
    
    def verify_incremental_loading(self, expected_calendar_ids: List[int]) -> Dict[str, Any]:
        """Verify that incremental loading worked correctly for specific calendar IDs"""
        logger.info(f"🔍 Verifying incremental loading for calendar IDs: {expected_calendar_ids}...")
        
        verification_results = {
            "status": "success",
            "expected_calendar_ids": expected_calendar_ids,
            "found_calendar_ids": [],
            "missing_calendar_ids": [],
            "calendar_id_counts": {}
        }
        
        try:
            # Check each expected calendar ID in destination
            for calendar_id in expected_calendar_ids:
                dest_query = """
                SELECT COUNT(*) 
                FROM reporting_client 
                WHERE systemcalendarid = ?
                """
                
                with self.dest_engine.connect() as dest_conn:
                    count = dest_conn.execute(sa.text(dest_query), calendar_id).scalar()
                
                verification_results["calendar_id_counts"][calendar_id] = count
                
                if count > 0:
                    verification_results["found_calendar_ids"].append(calendar_id)
                else:
                    verification_results["missing_calendar_ids"].append(calendar_id)
            
            if verification_results["missing_calendar_ids"]:
                verification_results["status"] = "failed"
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify incremental loading: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

def run_comprehensive_verification():
    """Run all verification tests and generate a comprehensive report"""
    print("🚀 Comprehensive Incremental Sync Verification")
    print("=" * 80)
    
    # Connection strings (adjust as needed)
    source_conn = "mssql+pyodbc://sa:Strong!Passw0rd@mssql-source:1433/StackOverflowMini?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
    dest_conn = "mssql+pyodbc://sa:Strong!Passw0rd@mssql-dest:1434/TargetDB?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=no"
    
    verifier = IncrementalSyncVerifier(source_conn, dest_conn)
    
    print("\n1️⃣ Record Count Verification")
    print("-" * 40)
    count_results = verifier.verify_record_counts_by_calendar_id()
    
    if count_results["status"] == "success":
        print(f"✅ Record counts match perfectly!")
        print(f"   📊 Total source records: {count_results['total_source_records']:,}")
        print(f"   📊 Total dest records: {count_results['total_dest_records']:,}")
        print(f"   📅 Calendar IDs found: {count_results['source_calendar_ids']}")
        
        for detail in count_results["calendar_id_details"]:
            status = "✅" if detail["match"] else "❌"
            print(f"   {status} {detail['calendar_id']}: {detail['source_count']:,} → {detail['dest_count']:,}")
    else:
        print(f"❌ Record count verification failed!")
        if count_results.get("mismatches"):
            print("   Count mismatches:")
            for mismatch in count_results["mismatches"]:
                print(f"     📅 {mismatch['calendar_id']}: {mismatch['source_count']:,} vs {mismatch['dest_count']:,} (diff: {mismatch['difference']:+,})")
        if count_results.get("missing_in_dest"):
            print(f"   Missing in destination: {count_results['missing_in_dest']}")
        if count_results.get("extra_in_dest"):
            print(f"   Extra in destination: {count_results['extra_in_dest']}")
    
    print("\n2️⃣ Schema Consistency Verification")
    print("-" * 40)
    schema_results = verifier.verify_schema_consistency()
    
    if schema_results["status"] == "success":
        print(f"✅ Schema consistency verified!")
        print(f"   📋 Source columns: {schema_results['source_columns']}")
        print(f"   📋 Dest columns: {schema_results['dest_columns']}")
    else:
        print(f"❌ Schema consistency issues found!")
        if schema_results.get("missing_columns"):
            print(f"   Missing columns in dest: {schema_results['missing_columns']}")
        if schema_results.get("extra_columns"):
            print(f"   Extra columns in dest: {schema_results['extra_columns']}")
        if schema_results.get("type_mismatches"):
            print("   Type mismatches:")
            for mismatch in schema_results["type_mismatches"]:
                print(f"     {mismatch['column_name']}: {mismatch['source_type']} → {mismatch['dest_type']}")
    
    print("\n3️⃣ Data Integrity Verification")
    print("-" * 40)
    integrity_results = verifier.verify_data_integrity_sample(1000)
    
    if integrity_results["status"] == "success":
        print(f"✅ Data integrity verified!")
        print(f"   🎯 Integrity score: {integrity_results['integrity_score']:.2f}%")
        print(f"   📊 Sample size: {integrity_results['sample_size']} records")
    else:
        print(f"❌ Data integrity issues found!")
        print(f"   🎯 Integrity score: {integrity_results['integrity_score']:.2f}%")
        print(f"   ⚠️ Mismatches: {len(integrity_results.get('data_mismatches', []))}")
    
    print("\n4️⃣ Latest Data Status")
    print("-" * 40)
    latest_source = verifier.get_latest_calendar_id("source")
    latest_dest = verifier.get_latest_calendar_id("dest")
    
    print(f"   📅 Latest source calendar ID: {latest_source}")
    print(f"   📅 Latest dest calendar ID: {latest_dest}")
    
    if latest_source == latest_dest:
        print("   ✅ Latest data synchronized")
    else:
        print("   ⚠️ Data synchronization lag detected")
    
    print("\n" + "=" * 80)
    print("📋 Verification Summary")
    
    overall_success = (
        count_results["status"] == "success" and
        schema_results["status"] == "success" and
        integrity_results["status"] == "success" and
        latest_source == latest_dest
    )
    
    if overall_success:
        print("🎉 ALL VERIFICATIONS PASSED! Incremental sync is working perfectly.")
    else:
        print("⚠️ Some verifications failed. Review the issues above.")
    
    return {
        "overall_success": overall_success,
        "count_verification": count_results,
        "schema_verification": schema_results,
        "integrity_verification": integrity_results,
        "latest_source_calendar_id": latest_source,
        "latest_dest_calendar_id": latest_dest
    }

if __name__ == "__main__":
    results = run_comprehensive_verification()
    
    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    sys.exit(exit_code)