#!/usr/bin/env python3

import pytest
import os
import sqlalchemy as sa
from contextlib import contextmanager


@pytest.fixture(scope="session")
def test_source_db():
    """Use existing source database with test data setup."""
    # Use environment variables if available, otherwise fall back to defaults
    # These should point to the existing Docker containers
    master_connection_string = os.getenv(
        'TEST_SOURCE_CONNECTION_STRING',
        "mssql+pyodbc://sa:Strong!Passw0rd@mssql-source:1433/StackOverflowMini"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
    ).replace("/StackOverflowMini", "/master")
    
    connection_string = master_connection_string.replace("/master", "/StackOverflowMini")
    
    # Try to connect and setup test database and data
    try:
        # First connect to master to create database
        master_engine = sa.create_engine(master_connection_string)
        with master_engine.connect() as conn:
            conn.autocommit = True
            try:
                conn.execute(sa.text("CREATE DATABASE StackOverflowMini"))
            except:
                # Database might already exist
                pass
        
        # Now connect to the test database
        engine = sa.create_engine(connection_string)
        with engine.connect() as conn:
            # Check if test data exists
            try:
                result = conn.execute(sa.text("SELECT COUNT(*) FROM dbo.Users"))
                if result.scalar() >= 3:
                    # Test data already exists
                    return connection_string
            except:
                # Tables don't exist, we'll create them
                pass
            
            # Create test tables if they don't exist
            conn.execute(sa.text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
                CREATE TABLE dbo.Users (
                    Id INT PRIMARY KEY,
                    DisplayName NVARCHAR(100),
                    CreationDate DATETIME2,
                    Reputation INT
                )
            """))
            
            conn.execute(sa.text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Posts' AND xtype='U')
                CREATE TABLE dbo.Posts (
                    Id INT PRIMARY KEY,
                    PostTypeId INT,
                    OwnerUserId INT,
                    CreationDate DATETIME2,
                    Title NVARCHAR(250),
                    Body NTEXT
                )
            """))
            
            conn.execute(sa.text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Comments' AND xtype='U')
                CREATE TABLE dbo.Comments (
                    Id INT PRIMARY KEY,
                    PostId INT,
                    UserId INT,
                    CreationDate DATETIME2,
                    Text NVARCHAR(MAX)
                )
            """))
            
            # Insert sample data if not exists
            try:
                conn.execute(sa.text("""
                    IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE Id = 1)
                    INSERT INTO dbo.Users (Id, DisplayName, CreationDate, Reputation) VALUES
                    (1, 'TestUser1', '2023-01-01T10:00:00', 100),
                    (2, 'TestUser2', '2023-01-02T11:00:00', 200),
                    (3, 'TestUser3', '2023-01-03T12:00:00', 300)
                """))
                
                conn.execute(sa.text("""
                    IF NOT EXISTS (SELECT 1 FROM dbo.Posts WHERE Id = 1)
                    INSERT INTO dbo.Posts (Id, PostTypeId, OwnerUserId, CreationDate, Title, Body) VALUES
                    (1, 1, 1, '2023-01-01T15:00:00', 'Test Question 1', 'This is a test question'),
                    (2, 2, 2, '2023-01-02T16:00:00', 'Test Answer 1', 'This is a test answer'),
                    (3, 1, 3, '2023-01-03T17:00:00', 'Test Question 2', 'Another test question')
                """))
                
                conn.execute(sa.text("""
                    IF NOT EXISTS (SELECT 1 FROM dbo.Comments WHERE Id = 1)
                    INSERT INTO dbo.Comments (Id, PostId, UserId, CreationDate, Text) VALUES
                    (1, 1, 2, '2023-01-01T18:00:00', 'Great question!'),
                    (2, 1, 3, '2023-01-01T19:00:00', 'I agree with the above'),
                    (3, 2, 1, '2023-01-02T20:00:00', 'Thanks for the answer')
                """))
                
                conn.commit()
            except Exception as e:
                # Data might already exist, continue
                pass
                
    except Exception as e:
        # If connection fails, skip integration tests
        pytest.skip(f"Cannot connect to test source database: {e}")
    
    return connection_string


@pytest.fixture(scope="session") 
def test_dest_db():
    """Use existing destination database."""
    master_connection_string = os.getenv(
        'TEST_DEST_CONNECTION_STRING',
        "mssql+pyodbc://sa:Strong!Passw0rd@mssql-dest:1433/TargetDB"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
    ).replace("/TargetDB", "/master")
    
    connection_string = master_connection_string.replace("/master", "/TargetDB")
    
    # Try to connect and setup destination database
    try:
        # First connect to master to create database
        master_engine = sa.create_engine(master_connection_string)
        with master_engine.connect() as conn:
            conn.autocommit = True
            try:
                conn.execute(sa.text("CREATE DATABASE TargetDB"))
            except:
                # Database might already exist
                pass
        
        # Verify destination is available
        engine = sa.create_engine(connection_string)
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Cannot connect to test destination database: {e}")
    
    return connection_string


@pytest.fixture(scope="function")
def clean_dest_db(test_dest_db):
    """Clean destination database before each test."""
    engine = sa.create_engine(test_dest_db)
    
    with engine.connect() as conn:
        # Drop schema if exists
        conn.execute(sa.text("""
            IF EXISTS (SELECT * FROM sys.schemas WHERE name = 'stackoverflow_data')
            BEGIN
                DROP SCHEMA stackoverflow_data
            END
        """))
        conn.commit()
    
    yield test_dest_db


@pytest.fixture
def test_env_vars(test_source_db, clean_dest_db, monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv('SOURCE_CONNECTION_STRING', test_source_db)
    monkeypatch.setenv('DEST_CONNECTION_STRING', clean_dest_db)
    return {
        'source': test_source_db,
        'dest': clean_dest_db
    }


@pytest.fixture
def sample_table_counts():
    """Expected row counts for test data."""
    return {
        'Users': 3,
        'Posts': 3,
        'Comments': 3
    }


@contextmanager
def database_connection(connection_string):
    """Context manager for database connections."""
    engine = sa.create_engine(connection_string)
    with engine.connect() as conn:
        yield conn


@pytest.fixture
def db_connection_helper():
    """Helper fixture for database connections."""
    return database_connection