-- Extract destination table DDL
USE stackoverflow_data;
GO

PRINT '=== DESTINATION TABLE: production_test_table ===';

-- Check if table exists
IF OBJECT_ID('production_test_table', 'U') IS NOT NULL
BEGIN
    PRINT 'Table exists. Analyzing structure:';
    
    PRINT '';
    PRINT 'Column breakdown by data type:';
    SELECT 
        DATA_TYPE,
        COUNT(*) as ColumnCount,
        LEFT(STRING_AGG(COLUMN_NAME, ', '), 200) + CASE WHEN COUNT(*) > 5 THEN '...' ELSE '' END as SampleColumns
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'production_test_table'
    GROUP BY DATA_TYPE
    ORDER BY DATA_TYPE;
    
    PRINT '';
    PRINT 'Total columns:';
    SELECT COUNT(*) as TotalColumns FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'production_test_table';
    
    PRINT '';
    PRINT 'Row count:';
    SELECT COUNT(*) as RecordCount FROM production_test_table;
    
    PRINT '';
    PRINT '=== FIRST 10 COLUMNS DETAILS ===';
    SELECT TOP 10
        COLUMN_NAME,
        DATA_TYPE,
        CASE 
            WHEN DATA_TYPE = 'decimal' THEN CAST(NUMERIC_PRECISION AS VARCHAR) + ',' + CAST(NUMERIC_SCALE AS VARCHAR)
            WHEN DATA_TYPE IN ('varchar', 'nvarchar') THEN ISNULL(CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR), 'MAX')
            ELSE ''
        END as TypeDetails,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'production_test_table'
    ORDER BY ORDINAL_POSITION;
    
    PRINT '';
    PRINT '=== DLT METADATA COLUMNS ===';
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'production_test_table' 
    AND COLUMN_NAME LIKE '_dlt_%'
    ORDER BY COLUMN_NAME;
END
ELSE
BEGIN
    PRINT 'Table does not exist in destination database.';
END

GO