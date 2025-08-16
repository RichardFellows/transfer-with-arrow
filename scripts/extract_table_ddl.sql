-- Extract DDL for source table
USE StackOverflowMini;
GO

PRINT '=== SOURCE TABLE DDL: ProductionTestTable ===';

-- Get table structure
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ProductionTestTable'
ORDER BY ORDINAL_POSITION;

PRINT '';
PRINT '=== SOURCE TABLE COLUMN COUNT ===';
SELECT COUNT(*) as ColumnCount FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ProductionTestTable';

PRINT '';
PRINT '=== SOURCE TABLE ROW COUNT ===';
SELECT COUNT(*) as RecordCount FROM dbo.ProductionTestTable;

GO