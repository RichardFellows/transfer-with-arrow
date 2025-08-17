#!/bin/bash

# Wait for SQL Server to be ready
echo "Waiting for SQL Server to be ready..."
sleep 30

# Download StackOverflowMini backup if not exists
if [ ! -f "/var/opt/mssql/backups/StackOverflowMini.bak" ]; then
    echo "Downloading StackOverflowMini backup..."
    cd /var/opt/mssql/backups
    wget https://github.com/brentozar/Stack-Overflow-Database/releases/download/2023-01/StackOverflowMini.bak
fi

# Restore the backup
echo "Restoring StackOverflowMini database..."
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'SecurePass123' -Q "
RESTORE DATABASE [StackOverflowMini] 
FROM DISK = N'/var/opt/mssql/backups/StackOverflowMini.bak' 
WITH MOVE 'StackOverflowMini' TO '/var/opt/mssql/data/StackOverflowMini.mdf',
MOVE 'StackOverflowMini_log' TO '/var/opt/mssql/data/StackOverflowMini_log.ldf',
REPLACE, STATS = 10"

echo "Database restore completed!"