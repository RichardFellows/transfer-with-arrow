#!/usr/bin/env python3

import os
import sys
import dlt
from dlt.sources.sql_database import sql_database
import sqlalchemy as sa
from datetime import datetime
import argparse

def copy_stackoverflow_tables(
    tables_to_copy=None,
    write_disposition="replace",
    use_incremental=False
):
    """
    Copy StackOverflow tables from source to destination MSSQL databases.
    """
    
    # Get connection strings from environment
    source_conn = os.getenv('SOURCE_CONNECTION_STRING')
    dest_conn = os.getenv('DEST_CONNECTION_STRING')
    
    if not source_conn or not dest_conn:
        print("Error: Connection strings not found in environment variables")
        sys.exit(1)
    
    print(f"Source: {source_conn.split('@')[1].split('?')[0]}")  # Print host info only
    print(f"Destination: {dest_conn.split('@')[1].split('?')[0]}")
    
    # Create destination engine
    dest_engine = sa.create_engine(dest_conn)
    
    # Configure source with PyArrow backend
    print(f"\nConfiguring source with PyArrow backend...")
    
    if tables_to_copy:
        source = sql_database(
            source_conn,
            backend="pyarrow",
            backend_kwargs={"tz": "UTC"},
            reflection_level="full_with_precision",
            chunk_size=10000  # Process in chunks for large tables
        ).with_resources(*tables_to_copy)
    else:
        # Default: copy main StackOverflow tables
        default_tables = ["Users", "Posts", "Comments", "Votes", "Badges", "PostTags", "Tags"]
        source = sql_database(
            source_conn,
            backend="pyarrow",
            backend_kwargs={"tz": "UTC"},
            reflection_level="full_with_precision",
            chunk_size=10000
        ).with_resources(*default_tables)
    
    # Apply incremental loading if requested
    if use_incremental:
        # Example: incrementally load Posts by CreationDate
        if "Posts" in [r.name for r in source.resources.values()]:
            source.Posts.apply_hints(
                incremental=dlt.sources.incremental(
                    "CreationDate",
                    initial_value=datetime(2020, 1, 1)
                )
            )
            print("Incremental loading enabled for Posts table (CreationDate)")
    
    # Create pipeline
    pipeline = dlt.pipeline(
        pipeline_name="stackoverflow_copy",
        destination=dlt.destinations.sqlalchemy(dest_engine),
        dataset_name="stackoverflow_data"
    )
    
    print(f"\nStarting data copy with {write_disposition} disposition...")
    print(f"Tables to copy: {', '.join([r.name for r in source.resources.values()])}")
    
    # Run the pipeline
    start_time = datetime.now()
    load_info = pipeline.run(
        source,
        write_disposition=write_disposition,
        loader_file_format="parquet"
    )
    end_time = datetime.now()
    
    print(f"\n✅ Copy completed successfully!")
    print(f"Duration: {end_time - start_time}")
    print("\nLoad statistics:")
    print(f"- Tables loaded: {len(load_info.load_packages[0].tables) if load_info.load_packages else 0}")
    
    # Print row counts if available
    if load_info.load_packages:
        for table_name, table_info in load_info.load_packages[0].tables.items():
            if hasattr(table_info, 'row_count'):
                print(f"  - {table_name}: {table_info.row_count} rows")
    
    return load_info


def verify_copy():
    """
    Verify that data was copied correctly by comparing row counts.
    """
    source_conn = os.getenv('SOURCE_CONNECTION_STRING')
    dest_conn = os.getenv('DEST_CONNECTION_STRING')
    
    source_engine = sa.create_engine(source_conn)
    dest_engine = sa.create_engine(dest_conn)
    
    print("\n📊 Verifying data copy...")
    
    tables = ["Users", "Posts", "Comments", "Votes", "Badges", "PostTags", "Tags"]
    
    for table in tables:
        try:
            # Check source count
            with source_engine.connect() as conn:
                source_count = conn.execute(
                    sa.text(f"SELECT COUNT(*) FROM dbo.{table}")
                ).scalar()
            
            # Check destination count
            with dest_engine.connect() as conn:
                dest_count = conn.execute(
                    sa.text(f"SELECT COUNT(*) FROM stackoverflow_data.{table}")
                ).scalar()
            
            status = "✅" if source_count == dest_count else "⚠️"
            print(f"{status} {table}: Source={source_count:,}, Destination={dest_count:,}")
            
        except Exception as e:
            print(f"❌ {table}: Error - {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy StackOverflow data between MSSQL databases')
    parser.add_argument('--tables', nargs='+', help='Specific tables to copy')
    parser.add_argument('--incremental', action='store_true', help='Use incremental loading')
    parser.add_argument('--verify', action='store_true', help='Verify copy after completion')
    parser.add_argument('--disposition', default='replace', 
                       choices=['replace', 'append', 'merge'],
                       help='Write disposition (default: replace)')
    
    args = parser.parse_args()
    
    # Run the copy
    copy_stackoverflow_tables(
        tables_to_copy=args.tables,
        write_disposition=args.disposition,
        use_incremental=args.incremental
    )
    
    # Verify if requested
    if args.verify:
        verify_copy()