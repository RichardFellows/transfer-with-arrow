#!/usr/bin/env python3

import pytest
import os
import time
import sqlalchemy as sa
from testcontainers.mssql import SqlServerContainer
from contextlib import contextmanager


@pytest.fixture(scope="session")
def test_source_db():
    """Create a test SQL Server container for source database."""
    with SqlServerContainer(
        password="SecurePass123123",
        image="mcr.microsoft.com/mssql/server:2022-latest"
    ) as sqlserver:
        # Wait for SQL Server to be ready
        time.sleep(10)
        
        # Create connection string
        connection_string = sqlserver.get_connection_url().replace(
            "mssql+pyodbc://", "mssql+pyodbc://"
        ) + "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
        
        # Create engine and setup test database
        engine = sa.create_engine(connection_string)
        
        # Create test database
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE DATABASE StackOverflowMini"))
            conn.commit()
        
        # Switch to test database
        test_connection_string = connection_string.replace("/master", "/StackOverflowMini")
        test_engine = sa.create_engine(test_connection_string)
        
        # Create test tables with sample data
        with test_engine.connect() as conn:
            # Create Users table
            conn.execute(sa.text("""
                CREATE TABLE dbo.Users (
                    Id INT PRIMARY KEY,
                    DisplayName NVARCHAR(100),
                    CreationDate DATETIME2,
                    Reputation INT
                )
            """))
            
            # Create Posts table
            conn.execute(sa.text("""
                CREATE TABLE dbo.Posts (
                    Id INT PRIMARY KEY,
                    PostTypeId INT,
                    OwnerUserId INT,
                    CreationDate DATETIME2,
                    Title NVARCHAR(250),
                    Body NTEXT
                )
            """))
            
            # Create Comments table
            conn.execute(sa.text("""
                CREATE TABLE dbo.Comments (
                    Id INT PRIMARY KEY,
                    PostId INT,
                    UserId INT,
                    CreationDate DATETIME2,
                    Text NVARCHAR(MAX)
                )
            """))
            
            # Insert sample data
            conn.execute(sa.text("""
                INSERT INTO dbo.Users (Id, DisplayName, CreationDate, Reputation) VALUES
                (1, 'TestUser1', '2023-01-01T10:00:00', 100),
                (2, 'TestUser2', '2023-01-02T11:00:00', 200),
                (3, 'TestUser3', '2023-01-03T12:00:00', 300)
            """))
            
            conn.execute(sa.text("""
                INSERT INTO dbo.Posts (Id, PostTypeId, OwnerUserId, CreationDate, Title, Body) VALUES
                (1, 1, 1, '2023-01-01T15:00:00', 'Test Question 1', 'This is a test question'),
                (2, 2, 2, '2023-01-02T16:00:00', 'Test Answer 1', 'This is a test answer'),
                (3, 1, 3, '2023-01-03T17:00:00', 'Test Question 2', 'Another test question')
            """))
            
            conn.execute(sa.text("""
                INSERT INTO dbo.Comments (Id, PostId, UserId, CreationDate, Text) VALUES
                (1, 1, 2, '2023-01-01T18:00:00', 'Great question!'),
                (2, 1, 3, '2023-01-01T19:00:00', 'I agree with the above'),
                (3, 2, 1, '2023-01-02T20:00:00', 'Thanks for the answer')
            """))
            
            conn.commit()
        
        yield test_connection_string


@pytest.fixture(scope="session")
def test_dest_db():
    """Create a test SQL Server container for destination database."""
    with SqlServerContainer(
        password="SecurePass123123",
        image="mcr.microsoft.com/mssql/server:2022-latest"
    ) as sqlserver:
        # Wait for SQL Server to be ready
        time.sleep(10)
        
        # Create connection string
        connection_string = sqlserver.get_connection_url().replace(
            "mssql+pyodbc://", "mssql+pyodbc://"
        ) + "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
        
        # Create engine and setup test database
        engine = sa.create_engine(connection_string)
        
        # Create test database
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE DATABASE TargetDB"))
            conn.commit()
        
        # Switch to test database
        test_connection_string = connection_string.replace("/master", "/TargetDB")
        
        yield test_connection_string


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