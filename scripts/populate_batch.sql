-- Efficient batch population for production test tables
USE StackOverflowMini;
GO

PRINT 'Populating production test tables with sample data...';

-- Populate ProductionTestSmall with 10K rows using efficient batch insert
INSERT INTO dbo.ProductionTestSmall (
    HighPrecisionAmount, MoneyValue, LargeText, StandardText, Counter, IsActive
)
SELECT TOP 10000
    CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 123.456789012345678901 AS DECIMAL(38,18)) as HighPrecisionAmount,
    CAST((ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 1.23) AS MONEY) as MoneyValue,
    'Large text for row ' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) + '. ' + REPLICATE('Sample content. ', 15) as LargeText,
    'Standard text row ' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as StandardText,
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) as Counter,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 10 = 0 THEN 0 ELSE 1 END as IsActive
FROM sys.objects s1
CROSS JOIN sys.objects s2;

PRINT 'ProductionTestSmall populated with rows.';

-- Populate ProductionTestTable with 50K rows using efficient batch insert
INSERT INTO dbo.ProductionTestTable (
    RecordCode, Amount1, Amount2, Price1, Price2, 
    Description1, Notes1, Code1, Name1,
    Counter1, Quantity1, IsActive, IsProcessed,
    CreatedDate, ModifiedDate,
    Rate1, Percentage1,
    Field01, Field02, Field03, Field04, Field05,
    Value01, Value02, Flag01, Flag02
)
SELECT TOP 50000
    'REC-' + RIGHT('000000' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(10)), 10) as RecordCode,
    CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 999.123456789012345678 AS DECIMAL(38,18)) as Amount1,
    CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 888.987654321098765432 AS DECIMAL(38,18)) as Amount2,
    CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 12.34 AS MONEY) as Price1,
    CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 56.78 AS MONEY) as Price2,
    'Description for record ' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) + '. ' + REPLICATE('Detailed information content. ', 25) as Description1,
    'Notes for record ' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) + '. ' + REPLICATE('Important notes. ', 20) as Notes1,
    'CODE-' + RIGHT('00000' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(10)), 8) as Code1,
    'Name-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Name1,
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) as Counter1,
    (ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 1000) as Quantity1,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 10 = 0 THEN 0 ELSE 1 END as IsActive,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 5 = 0 THEN 1 ELSE 0 END as IsProcessed,
    DATEADD(DAY, -(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 365), GETDATE()) as CreatedDate,
    DATEADD(HOUR, -(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 24), GETDATE()) as ModifiedDate,
    CAST((ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) * 1.2345) AS DECIMAL(10,4)) as Rate1,
    CAST((ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 100) AS DECIMAL(5,2)) as Percentage1,
    'Field01-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Field01,
    'Field02-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Field02,
    'Field03-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Field03,
    'Field04-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Field04,
    'Field05-' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR(50)) as Field05,
    (ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 100000) as Value01,
    (ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 50000) as Value02,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 2 = 0 THEN 1 ELSE 0 END as Flag01,
    CASE WHEN ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) % 3 = 0 THEN 1 ELSE 0 END as Flag02
FROM sys.objects s1
CROSS JOIN sys.objects s2
CROSS JOIN sys.objects s3;

PRINT 'ProductionTestTable populated with rows.';

-- Show final counts
SELECT 'ProductionTestSmall' as TableName, COUNT(*) as RecordCount FROM dbo.ProductionTestSmall;
SELECT 'ProductionTestTable' as TableName, COUNT(*) as RecordCount FROM dbo.ProductionTestTable;

PRINT 'Production data population completed successfully!';
GO