#!/usr/bin/env python3
"""
CLI output formatting utilities.
"""

from typing import Dict, Any, List
from datetime import datetime


def format_extraction_results(results: Dict[str, Any]) -> None:
    """
    Format and display extraction results.
    
    Args:
        results: Extraction results dictionary
    """
    print(f"\n{'='*60}")
    print("EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"Phase: {results.get('phase', 'extract').upper()}")
    print(f"Status: {results.get('status', 'unknown').upper()}")
    print(f"Timestamp: {results.get('timestamp', 'unknown')}")
    
    tables = results.get('tables', {})
    if not tables:
        print("No tables processed")
        return
    
    print(f"\nTables Processed ({len(tables)}):")
    
    for table_name, table_result in tables.items():
        status = table_result.get('status', 'unknown')
        status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⚠️"
        
        print(f"\n  {status_icon} {table_name}")
        print(f"    Status: {status}")
        
        if table_result.get('batch_id'):
            print(f"    Batch ID: {table_result['batch_id']}")
        
        if table_result.get('rows') is not None:
            print(f"    Rows: {table_result['rows']:,}")
        
        if table_result.get('file_size_mb') is not None:
            print(f"    Size: {table_result['file_size_mb']:.2f} MB")
        
        if table_result.get('duration_seconds') is not None:
            print(f"    Duration: {table_result['duration_seconds']:.2f}s")
        
        if table_result.get('compression'):
            print(f"    Compression: {table_result['compression']}")
        
        if status == "failed" and table_result.get('error'):
            print(f"    Error: {table_result['error']}")


def format_load_results(results: Dict[str, Any]) -> None:
    """
    Format and display load results.
    
    Args:
        results: Load results dictionary
    """
    print(f"\n{'='*60}")
    print("LOAD RESULTS")
    print(f"{'='*60}")
    print(f"Phase: {results.get('phase', 'load').upper()}")
    print(f"Status: {results.get('status', 'unknown').upper()}")
    print(f"Timestamp: {results.get('timestamp', 'unknown')}")
    
    tables = results.get('tables', {})
    if not tables:
        print("No tables processed")
        return
    
    print(f"\nTables Processed ({len(tables)}):")
    
    for table_name, table_result in tables.items():
        status = table_result.get('status', 'unknown')
        status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⚠️"
        
        print(f"\n  {status_icon} {table_name}")
        print(f"    Status: {status}")
        
        if table_result.get('batch_id'):
            print(f"    Batch ID: {table_result['batch_id']}")
        
        if table_result.get('loaded_rows') is not None:
            print(f"    Loaded Rows: {table_result['loaded_rows']:,}")
        
        if table_result.get('source_rows') is not None:
            print(f"    Source Rows: {table_result['source_rows']:,}")
        
        if table_result.get('duration_seconds') is not None:
            print(f"    Duration: {table_result['duration_seconds']:.2f}s")
        
        # Show verification results if available
        if table_result.get('verification'):
            verification = table_result['verification']
            if verification.get('enabled'):
                verified_icon = "✅" if verification.get('passed') else "❌"
                print(f"    Verification: {verified_icon} {verification.get('status', 'unknown')}")
                
                if verification.get('row_count_match') is not None:
                    match_icon = "✅" if verification['row_count_match'] else "❌"
                    print(f"      Row Count: {match_icon}")
                
                if verification.get('tolerance_check') is not None:
                    tolerance_icon = "✅" if verification['tolerance_check'] else "❌"
                    print(f"      Tolerance: {tolerance_icon}")
        
        if status == "failed" and table_result.get('error'):
            print(f"    Error: {table_result['error']}")


def format_archive_status(status: Dict[str, Any]) -> None:
    """
    Format and display archive status.
    
    Args:
        status: Archive status dictionary
    """
    print(f"\n{'='*60}")
    print("ARCHIVE STATUS")
    print(f"{'='*60}")
    
    archive_status = status.get('status', 'unknown')
    mode = status.get('mode', 'unknown')
    
    print(f"Status: {archive_status.upper()}")
    print(f"Pipeline Mode: {mode}")
    print(f"Timestamp: {status.get('timestamp', 'unknown')}")
    
    if archive_status == "archive_disabled":
        print("\n💡 Archive is not available for this pipeline mode")
        print("   Use extract-only, load-only, or two-stage mode to enable archive functionality")
        return
    
    if archive_status == "error":
        print(f"\n❌ Archive Error: {status.get('error', 'Unknown error')}")
        return
    
    # Show archive statistics
    stats = status.get('archive_statistics', {})
    if stats:
        print(f"\n📊 Archive Statistics:")
        print(f"  Total Batches: {stats.get('total_batches', 0):,}")
        print(f"  Total Size: {stats.get('total_size_mb', 0):.2f} MB")
        print(f"  Oldest Batch: {stats.get('oldest_batch_date', 'N/A')}")
        print(f"  Newest Batch: {stats.get('newest_batch_date', 'N/A')}")
        
        if stats.get('tables_with_data'):
            print(f"  Tables with Data: {len(stats['tables_with_data'])}")
    
    # Show table summaries
    table_summaries = status.get('table_summaries', {})
    if table_summaries:
        print(f"\n📋 Table Summaries:")
        
        for table_name, summary in table_summaries.items():
            table_status = summary.get('status', 'unknown')
            
            if table_status == "no_batches":
                print(f"  📊 {table_name}: No batches available")
            else:
                latest_date = summary.get('latest_batch_date', 'unknown')
                if latest_date != 'unknown':
                    try:
                        # Parse and format the date
                        parsed_date = datetime.fromisoformat(latest_date.replace('Z', '+00:00'))
                        formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_date = latest_date
                else:
                    formatted_date = 'unknown'
                
                row_count = summary.get('latest_row_count', 0)
                batch_id = summary.get('latest_batch_id', 'unknown')
                
                print(f"  📊 {table_name}:")
                print(f"    Latest Batch: {batch_id}")
                print(f"    Latest Date: {formatted_date}")
                print(f"    Latest Rows: {row_count:,}")
    
    # Show recent batches
    recent_batches = status.get('recent_batches', [])
    if recent_batches:
        print(f"\n🕒 Recent Batches ({len(recent_batches)}):")
        
        for batch in recent_batches[-5:]:  # Show last 5
            batch_status = batch.get('status', 'unknown')
            status_icon = "✅" if batch_status == "completed" else "❌" if batch_status == "failed" else "⚠️"
            
            created_at = batch.get('created_at', 'unknown')
            if created_at != 'unknown':
                try:
                    parsed_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = parsed_date.strftime('%m-%d %H:%M')
                except:
                    formatted_date = created_at
            else:
                formatted_date = 'unknown'
            
            table_name = batch.get('table_name', 'unknown')
            batch_id = batch.get('batch_id', 'unknown')
            row_count = batch.get('row_count', 0)
            
            print(f"  {status_icon} {formatted_date} | {table_name} | {batch_id} | {row_count:,} rows")


def format_pipeline_summary(results: Dict[str, Any]) -> None:
    """
    Format and display comprehensive pipeline execution summary.
    
    Args:
        results: Pipeline execution results
    """
    print(f"\n{'='*80}")
    print("PIPELINE EXECUTION SUMMARY")
    print(f"{'='*80}")
    
    mode = results.get('mode', 'unknown')
    status = results.get('status', 'unknown')
    duration = results.get('duration', 0)
    
    print(f"Mode: {mode.upper()}")
    print(f"Status: {status.upper()}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Started: {results.get('started_at', 'unknown')}")
    print(f"Completed: {results.get('completed_at', 'unknown')}")
    
    # Show extract results if available
    if results.get('extract_results'):
        print(f"\n📦 EXTRACT PHASE")
        print(f"{'-'*40}")
        extract_results = results['extract_results']
        extract_tables = extract_results.get('tables', {})
        
        successful_extracts = sum(1 for result in extract_tables.values() 
                                if result.get('status') == 'completed')
        
        print(f"Tables: {successful_extracts}/{len(extract_tables)} successful")
        
        for table_name, result in extract_tables.items():
            status_icon = "✅" if result.get('status') == 'completed' else "❌"
            batch_id = result.get('batch_id', 'unknown')
            rows = result.get('rows', 0)
            print(f"  {status_icon} {table_name}: {batch_id} ({rows:,} rows)")
    
    # Show load results if available
    if results.get('load_results'):
        print(f"\n🚚 LOAD PHASE")
        print(f"{'-'*40}")
        load_results = results['load_results']
        load_tables = load_results.get('tables', {})
        
        successful_loads = sum(1 for result in load_tables.values() 
                             if result.get('status') == 'completed')
        
        print(f"Tables: {successful_loads}/{len(load_tables)} successful")
        
        for table_name, result in load_tables.items():
            status_icon = "✅" if result.get('status') == 'completed' else "❌"
            loaded_rows = result.get('loaded_rows', 0)
            batch_id = result.get('batch_id', 'unknown')
            print(f"  {status_icon} {table_name}: {batch_id} ({loaded_rows:,} rows)")
    
    # Show direct mode results if available
    if results.get('results') and mode == 'direct':
        print(f"\n📊 DIRECT MODE RESULTS")
        print(f"{'-'*40}")
        direct_results = results['results']
        
        for table_name, result in direct_results.items():
            status_icon = "✅" if result.get('status') == 'completed' else "❌"
            rows = result.get('rows_processed', 0)
            duration = result.get('duration_seconds', 0)
            print(f"  {status_icon} {table_name}: {rows:,} rows ({duration:.2f}s)")


def format_table_list(tables: List[str], title: str = "Tables") -> None:
    """
    Format and display a list of tables.
    
    Args:
        tables: List of table names
        title: Title for the list
    """
    if not tables:
        print(f"No {title.lower()}")
        return
    
    print(f"\n{title} ({len(tables)}):")
    for i, table in enumerate(sorted(tables), 1):
        print(f"  {i:2d}. {table}")


def format_batch_list(batches: List[Dict[str, Any]], title: str = "Batches") -> None:
    """
    Format and display a list of batches.
    
    Args:
        batches: List of batch dictionaries
        title: Title for the list
    """
    if not batches:
        print(f"No {title.lower()}")
        return
    
    print(f"\n{title} ({len(batches)}):")
    print(f"{'Status':<8} {'Date':<16} {'Table':<20} {'Batch ID':<18} {'Rows':<10}")
    print(f"{'-'*8} {'-'*16} {'-'*20} {'-'*18} {'-'*10}")
    
    for batch in batches:
        status = batch.get('status', 'unknown')
        status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⚠️"
        
        created_at = batch.get('created_at', 'unknown')
        if created_at != 'unknown':
            try:
                parsed_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = parsed_date.strftime('%m-%d %H:%M')
            except:
                formatted_date = created_at[:16]
        else:
            formatted_date = 'unknown'
        
        table_name = batch.get('table_name', 'unknown')[:20]
        batch_id = batch.get('batch_id', 'unknown')[:18]
        row_count = batch.get('row_count', 0)
        
        print(f"{status_icon:<7} {formatted_date:<16} {table_name:<20} {batch_id:<18} {row_count:>9,}")


def format_error_message(error: str, context: str = None) -> None:
    """
    Format and display an error message.
    
    Args:
        error: Error message
        context: Optional context information
    """
    print(f"\n❌ ERROR")
    if context:
        print(f"Context: {context}")
    print(f"Message: {error}")
    
    # Provide helpful suggestions based on common errors
    error_lower = error.lower()
    
    if "configuration" in error_lower:
        print(f"\n💡 Tips:")
        print(f"  • Check your pipeline_config.yaml file")
        print(f"  • Validate configuration with: python run_pipeline.py validate")
        print(f"  • Check environment-specific config files")
    
    elif "connection" in error_lower or "database" in error_lower:
        print(f"\n💡 Tips:")
        print(f"  • Verify database containers are running: make up")
        print(f"  • Check connection strings in configuration")
        print(f"  • Test database connectivity")
    
    elif "table" in error_lower:
        print(f"\n💡 Tips:")
        print(f"  • Check table names in configuration")
        print(f"  • Verify tables exist in source database")
        print(f"  • Use 'python run_pipeline.py stats' to see available tables")
    
    elif "batch" in error_lower or "archive" in error_lower:
        print(f"\n💡 Tips:")
        print(f"  • Check available batches: python run_pipeline.py archive list")
        print(f"  • Verify archive storage path exists")
        print(f"  • Use extract operation to create batches first")


def format_progress_indicator(current: int, total: int, operation: str = "Processing") -> str:
    """
    Format a progress indicator string.
    
    Args:
        current: Current progress count
        total: Total items to process
        operation: Operation description
        
    Returns:
        Formatted progress string
    """
    if total == 0:
        percentage = 100.0
    else:
        percentage = (current / total) * 100
    
    # Create progress bar
    bar_length = 20
    filled_length = int(bar_length * current // total) if total > 0 else bar_length
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    return f"{operation}: [{bar}] {current}/{total} ({percentage:.1f}%)"


def format_size_bytes(size_bytes: int) -> str:
    """
    Format byte size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"