-- Extract focused DDL for comparison
USE StackOverflowMini;
GO

PRINT '=== SOURCE TABLE: ProductionTestTable ===';
PRINT 'Column breakdown by data type:';

SELECT 
    DATA_TYPE,
    COUNT(*) as ColumnCount,
    STRING_AGG(COLUMN_NAME, ', ') as SampleColumns
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ProductionTestTable'
GROUP BY DATA_TYPE
ORDER BY DATA_TYPE;

PRINT '';
PRINT 'Total columns:';
SELECT COUNT(*) as TotalColumns FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ProductionTestTable';

PRINT '';
PRINT 'Row count:';
SELECT COUNT(*) as RecordCount FROM dbo.ProductionTestTable;

PRINT '';
PRINT '=== FIRST 10 COLUMNS DETAILS ===';
SELECT TOP 10
    COLUMN_NAME,
    DATA_TYPE,
    CASE 
        WHEN DATA_TYPE = 'decimal' THEN CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR)
        WHEN DATA_TYPE = 'varchar' THEN ISNULL(CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR), 'MAX')
        ELSE ''
    END as TypeDetails,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ProductionTestTable'
ORDER BY ORDINAL_POSITION;

GO