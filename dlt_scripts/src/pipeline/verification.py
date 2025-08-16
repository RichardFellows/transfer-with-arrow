#!/usr/bin/env python3

import sqlalchemy as sa
from typing import Dict, List, Optional, Any, Tuple
import logging

from .config_models import ConfigurationModel, get_verification_tables
from ..utils.logging_setup import (
    get_logger, log_verification_start, log_verification_result, 
    log_verification_complete
)


class VerificationResult:
    """Represents the result of a verification check."""
    
    def __init__(
        self, 
        table_name: str, 
        check_name: str,
        passed: bool, 
        source_value: Any = None,
        dest_value: Any = None,
        difference: Any = None,
        tolerance: Any = None,
        error: Optional[str] = None
    ):
        self.table_name = table_name
        self.check_name = check_name
        self.passed = passed
        self.source_value = source_value
        self.dest_value = dest_value
        self.difference = difference
        self.tolerance = tolerance
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "table_name": self.table_name,
            "check_name": self.check_name,
            "passed": self.passed,
            "source_value": self.source_value,
            "dest_value": self.dest_value,
            "difference": self.difference,
            "tolerance": self.tolerance,
            "error": self.error
        }


class DataVerifier:
    """Enhanced data verification system with multiple check types."""
    
    def __init__(self, config: ConfigurationModel, logger: logging.Logger):
        """
        Initialize the data verifier.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.verifier_logger = get_logger("verifier")
        
        # Create database connections
        self.source_engine = sa.create_engine(
            self.config.connections["source"].connection_string
        )
        self.dest_engine = sa.create_engine(
            self.config.connections["destination"].connection_string
        )
    
    def verify_all_tables(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run verification for all configured tables.
        
        Args:
            table_names: Specific tables to verify (None = use config)
            
        Returns:
            Comprehensive verification results
        """
        if not self.config.verification.enabled:
            self.verifier_logger.info("Verification is disabled in configuration")
            return {"verification_enabled": False}
        
        # Determine which tables to verify
        if table_names is None:
            tables_to_verify = get_verification_tables(self.config)
        else:
            tables_to_verify = table_names
        
        log_verification_start(self.verifier_logger, tables_to_verify)
        
        results = {
            "verification_enabled": True,
            "tables_verified": [],
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "table_results": {},
            "custom_check_results": {},
            "summary": {}
        }
        
        # Run standard verification checks for each table
        for table_name in tables_to_verify:
            table_results = self._verify_table(table_name)
            results["table_results"][table_name] = table_results
            results["tables_verified"].append(table_name)
            
            # Update counters
            for check_result in table_results:
                results["total_checks"] += 1
                if check_result.passed:
                    results["passed_checks"] += 1
                else:
                    results["failed_checks"] += 1
        
        # Run custom verification checks
        if self.config.verification.custom_checks:
            custom_results = self._run_custom_checks()
            results["custom_check_results"] = custom_results
            
            # Update counters for custom checks
            for check_name, check_result in custom_results.items():
                results["total_checks"] += 1
                if check_result.get("passed", False):
                    results["passed_checks"] += 1
                else:
                    results["failed_checks"] += 1
        
        # Generate summary
        results["summary"] = {
            "overall_passed": results["failed_checks"] == 0,
            "success_rate": (results["passed_checks"] / results["total_checks"] * 100) 
                           if results["total_checks"] > 0 else 0,
            "tables_with_issues": [
                table_name for table_name, table_results in results["table_results"].items()
                if any(not result.passed for result in table_results)
            ]
        }
        
        log_verification_complete(
            self.verifier_logger, 
            results["passed_checks"], 
            results["failed_checks"]
        )
        
        return results
    
    def _verify_table(self, table_name: str) -> List[VerificationResult]:
        """
        Run verification checks for a single table.
        
        Args:
            table_name: Name of the table to verify
            
        Returns:
            List of verification results
        """
        results = []
        
        # Get table configuration
        table_config = self.config.tables.get(table_name)
        if not table_config:
            error_msg = f"Table configuration not found for {table_name}"
            self.verifier_logger.error(error_msg)
            results.append(VerificationResult(
                table_name=table_name,
                check_name="configuration_check",
                passed=False,
                error=error_msg
            ))
            return results
        
        # 1. Row count verification
        row_count_result = self._verify_row_count(table_name, table_config)
        results.append(row_count_result)
        
        # 2. Schema existence verification
        schema_result = self._verify_table_exists(table_name, table_config)
        results.append(schema_result)
        
        # 3. Primary key verification (if configured)
        if table_config.primary_key:
            pk_result = self._verify_primary_key_integrity(table_name, table_config)
            results.append(pk_result)
        
        # 4. Data type consistency (basic check)
        # This would require more sophisticated schema comparison
        # For now, we'll add a placeholder
        
        return results
    
    def _verify_row_count(self, table_name: str, table_config) -> VerificationResult:
        """
        Verify row count between source and destination.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            
        Returns:
            Row count verification result
        """
        try:
            # Get source count
            source_table = table_config.source_table
            source_schema = self.config.connections["source"].schema_name
            
            if table_config.where_clause:
                source_query = f"SELECT COUNT(*) FROM {source_table} WHERE {table_config.where_clause}"
            else:
                source_query = f"SELECT COUNT(*) FROM {source_table}"
            
            with self.source_engine.connect() as conn:
                source_count = conn.execute(sa.text(source_query)).scalar()
            
            # Get destination count
            dest_table = table_config.destination_table
            dest_schema = self.config.connections["destination"].schema_name
            dest_query = f"SELECT COUNT(*) FROM {dest_schema}.{dest_table}"
            
            with self.dest_engine.connect() as conn:
                dest_count = conn.execute(sa.text(dest_query)).scalar()
            
            # Calculate difference and check against tolerance
            difference = abs(source_count - dest_count)
            tolerance = self.config.verification.tolerance
            passed = difference <= tolerance
            
            log_verification_result(
                self.verifier_logger, 
                table_name, 
                source_count, 
                dest_count, 
                tolerance
            )
            
            return VerificationResult(
                table_name=table_name,
                check_name="row_count",
                passed=passed,
                source_value=source_count,
                dest_value=dest_count,
                difference=difference,
                tolerance=tolerance
            )
            
        except Exception as e:
            error_msg = f"Row count verification failed: {e}"
            self.verifier_logger.error(f"❌ {table_name}: {error_msg}")
            
            return VerificationResult(
                table_name=table_name,
                check_name="row_count",
                passed=False,
                error=error_msg
            )
    
    def _verify_table_exists(self, table_name: str, table_config) -> VerificationResult:
        """
        Verify that the destination table exists.
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            
        Returns:
            Table existence verification result
        """
        try:
            dest_table = table_config.destination_table
            dest_schema = self.config.connections["destination"].schema_name
            
            # Check if table exists in destination
            existence_query = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{dest_schema}' 
                AND TABLE_NAME = '{dest_table}'
            """
            
            with self.dest_engine.connect() as conn:
                table_exists = conn.execute(sa.text(existence_query)).scalar() > 0
            
            if table_exists:
                self.verifier_logger.info(f"✅ {table_name}: Table exists in destination")
            else:
                self.verifier_logger.error(f"❌ {table_name}: Table does not exist in destination")
            
            return VerificationResult(
                table_name=table_name,
                check_name="table_existence",
                passed=table_exists,
                dest_value=table_exists
            )
            
        except Exception as e:
            error_msg = f"Table existence check failed: {e}"
            self.verifier_logger.error(f"❌ {table_name}: {error_msg}")
            
            return VerificationResult(
                table_name=table_name,
                check_name="table_existence",
                passed=False,
                error=error_msg
            )
    
    def _verify_primary_key_integrity(self, table_name: str, table_config) -> VerificationResult:
        """
        Verify primary key integrity (no duplicates in destination).
        
        Args:
            table_name: Name of the table
            table_config: Table configuration
            
        Returns:
            Primary key integrity verification result
        """
        try:
            dest_table = table_config.destination_table
            dest_schema = self.config.connections["destination"].schema_name
            pk_columns = table_config.primary_key
            
            if not pk_columns:
                return VerificationResult(
                    table_name=table_name,
                    check_name="primary_key_integrity",
                    passed=True,
                    error="No primary key configured"
                )
            
            # Check for duplicates based on primary key columns
            pk_column_list = ", ".join(pk_columns)
            duplicate_query = f"""
                SELECT COUNT(*) as total_rows,
                       COUNT(DISTINCT {pk_column_list}) as distinct_rows
                FROM {dest_schema}.{dest_table}
            """
            
            with self.dest_engine.connect() as conn:
                result = conn.execute(sa.text(duplicate_query)).fetchone()
                total_rows = result.total_rows
                distinct_rows = result.distinct_rows
            
            has_duplicates = total_rows != distinct_rows
            duplicate_count = total_rows - distinct_rows
            
            if has_duplicates:
                self.verifier_logger.error(
                    f"❌ {table_name}: Found {duplicate_count} duplicate primary key values"
                )
            else:
                self.verifier_logger.info(f"✅ {table_name}: No primary key duplicates found")
            
            return VerificationResult(
                table_name=table_name,
                check_name="primary_key_integrity",
                passed=not has_duplicates,
                source_value=total_rows,
                dest_value=distinct_rows,
                difference=duplicate_count
            )
            
        except Exception as e:
            error_msg = f"Primary key integrity check failed: {e}"
            self.verifier_logger.error(f"❌ {table_name}: {error_msg}")
            
            return VerificationResult(
                table_name=table_name,
                check_name="primary_key_integrity",
                passed=False,
                error=error_msg
            )
    
    def _run_custom_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        Run custom verification checks defined in configuration.
        
        Returns:
            Dictionary of custom check results
        """
        results = {}
        
        if not self.config.verification.custom_checks:
            return results
        
        self.verifier_logger.info("Running custom verification checks")
        
        for check_name, check_query in self.config.verification.custom_checks.items():
            try:
                self.verifier_logger.info(f"Running custom check: {check_name}")
                
                with self.dest_engine.connect() as conn:
                    result = conn.execute(sa.text(check_query)).scalar()
                
                # For custom checks, we assume a result of 0 means "passed"
                # and any other value means "failed" (e.g., count of violations)
                passed = (result == 0)
                
                if passed:
                    self.verifier_logger.info(f"✅ Custom check '{check_name}': PASSED")
                else:
                    self.verifier_logger.error(f"❌ Custom check '{check_name}': FAILED (result: {result})")
                
                results[check_name] = {
                    "check_name": check_name,
                    "query": check_query,
                    "result": result,
                    "passed": passed
                }
                
            except Exception as e:
                error_msg = f"Custom check failed: {e}"
                self.verifier_logger.error(f"❌ Custom check '{check_name}': {error_msg}")
                
                results[check_name] = {
                    "check_name": check_name,
                    "query": check_query,
                    "passed": False,
                    "error": error_msg
                }
        
        return results
    
    def generate_verification_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable verification report.
        
        Args:
            results: Verification results from verify_all_tables()
            
        Returns:
            Formatted report string
        """
        if not results.get("verification_enabled", False):
            return "Verification is disabled."
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("DATA VERIFICATION REPORT")
        report_lines.append("=" * 60)
        
        # Summary
        summary = results["summary"]
        report_lines.append(f"Overall Status: {'✅ PASSED' if summary['overall_passed'] else '❌ FAILED'}")
        report_lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
        report_lines.append(f"Total Checks: {results['total_checks']}")
        report_lines.append(f"Passed: {results['passed_checks']}")
        report_lines.append(f"Failed: {results['failed_checks']}")
        report_lines.append("")
        
        # Table-by-table results
        report_lines.append("TABLE VERIFICATION RESULTS:")
        report_lines.append("-" * 30)
        
        for table_name, table_results in results["table_results"].items():
            table_passed = all(result.passed for result in table_results)
            status = "✅ PASSED" if table_passed else "❌ FAILED"
            report_lines.append(f"{table_name}: {status}")
            
            for result in table_results:
                if not result.passed:
                    report_lines.append(f"  - {result.check_name}: {result.error or 'FAILED'}")
                elif result.check_name == "row_count":
                    report_lines.append(f"  - Row count: {result.source_value:,} → {result.dest_value:,}")
        
        # Custom check results
        if results["custom_check_results"]:
            report_lines.append("")
            report_lines.append("CUSTOM CHECK RESULTS:")
            report_lines.append("-" * 20)
            
            for check_name, check_result in results["custom_check_results"].items():
                status = "✅ PASSED" if check_result.get("passed", False) else "❌ FAILED"
                report_lines.append(f"{check_name}: {status}")
                
                if not check_result.get("passed", False):
                    error = check_result.get("error", f"Result: {check_result.get('result', 'Unknown')}")
                    report_lines.append(f"  - {error}")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)