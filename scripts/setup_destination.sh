#!/bin/bash

# Create destination database
echo "Creating destination database..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'SecurePass123' -Q "
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'TargetDB')
BEGIN
    CREATE DATABASE TargetDB;
END"

echo "Destination database created!"