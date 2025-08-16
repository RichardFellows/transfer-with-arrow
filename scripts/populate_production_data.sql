-- Populate production-scale test tables with 1M+ rows
-- Uses efficient batch insertion techniques

USE StackOverflowMini;
GO

PRINT 'Starting production data population...';

-- First, populate ProductionTestSmall with 100K rows for faster testing
PRINT 'Populating ProductionTestSmall with 100K rows...';

DECLARE @i INT = 1;
DECLARE @batch_size INT = 5000;
DECLARE @total_rows INT = 100000;

WHILE @i <= @total_rows
BEGIN
    WITH NumberSequence AS (
        SELECT @i + ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS RowNum
        FROM sys.objects s1
        CROSS JOIN sys.objects s2
    )
    INSERT INTO dbo.ProductionTestSmall (
        HighPrecisionAmount,
        MoneyValue, 
        LargeText,
        StandardText,
        Counter,
        IsActive,
        CreatedDate,
        ModifiedDate
    )
    SELECT TOP (@batch_size)
        CAST(RAND(CHECKSUM(NEWID())) * 999999999999999999.999999999999999999 AS DECIMAL(38,18)) AS HighPrecisionAmount,
        CAST(RAND(CHECKSUM(NEWID())) * 10000 AS MONEY) AS MoneyValue,
        'Large text content for row ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('This is sample data content. ', 10) AS LargeText,
        'Standard text for row ' + CAST(RowNum AS VARCHAR(50)) AS StandardText,
        RowNum AS Counter,
        CASE WHEN RowNum % 10 = 0 THEN 0 ELSE 1 END AS IsActive,
        DATEADD(DAY, -(RowNum % 1000), GETDATE()) AS CreatedDate,
        DATEADD(HOUR, -(RowNum % 24), GETDATE()) AS ModifiedDate
    FROM NumberSequence
    WHERE RowNum BETWEEN @i AND @i + @batch_size - 1;

    SET @i = @i + @batch_size;
    
    IF @i % 25000 = 1
        PRINT 'Inserted ' + CAST(@i - 1 AS VARCHAR(10)) + ' rows into ProductionTestSmall...';
END;

PRINT 'ProductionTestSmall population complete: ' + CAST(@@ROWCOUNT AS VARCHAR(10)) + ' rows inserted.';

-- Now populate ProductionTestTable with 1M+ rows using efficient batch processing
PRINT 'Starting ProductionTestTable population with 1M+ rows...';

SET @i = 1;
SET @batch_size = 5000;  -- Smaller batches for complex table
SET @total_rows = 1000000;  -- 1 million rows

WHILE @i <= @total_rows
BEGIN
    WITH NumberSequence AS (
        SELECT @i + ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS RowNum
        FROM sys.objects s1
        CROSS JOIN sys.objects s2
        CROSS JOIN sys.objects s3
    )
    INSERT INTO dbo.ProductionTestTable (
        RecordCode,
        Amount1, Amount2, Amount3, Amount4, Amount5,
        Amount6, Amount7, Amount8, Amount9, Amount10,
        Price1, Price2, Price3, Price4, Price5,
        Description1, Description2, Description3,
        Notes1, Notes2, Comments1, Comments2,
        Code1, Code2, Code3, Code4, Code5,
        Name1, Name2, Name3, Name4, Name5,
        Counter1, Counter2, Counter3, Counter4, Counter5,
        Quantity1, Quantity2, Quantity3, Quantity4, Quantity5,
        IsActive, IsProcessed, IsApproved, IsDeleted, IsPublic,
        IsVisible, IsLocked, IsArchived, IsComplete, IsValid,
        CreatedDate, ModifiedDate, ProcessedDate, ApprovedDate,
        ExpiryDate, StartDate, EndDate,
        Rate1, Rate2, Rate3, Rate4, Rate5,
        Percentage1, Percentage2, Percentage3,
        Field01, Field02, Field03, Field04, Field05,
        Field06, Field07, Field08, Field09, Field10,
        Field11, Field12, Field13, Field14, Field15,
        Field16, Field17, Field18, Field19, Field20,
        Field21, Field22, Field23, Field24, Field25,
        Field26, Field27, Field28, Field29, Field30,
        Value01, Value02, Value03, Value04, Value05,
        Value06, Value07, Value08, Value09, Value10,
        Value11, Value12, Value13, Value14, Value15,
        Value16, Value17, Value18, Value19, Value20,
        Flag01, Flag02, Flag03, Flag04, Flag05,
        Flag06, Flag07, Flag08, Flag09, Flag10
    )
    SELECT TOP (@batch_size)
        'REC-' + RIGHT('000000' + CAST(RowNum AS VARCHAR(10)), 10) AS RecordCode,
        
        -- High precision decimal amounts
        CAST(RAND(CHECKSUM(NEWID())) * 999999999999999999.999999999999999999 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 888888888888888888.888888888888888888 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 777777777777777777.777777777777777777 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 666666666666666666.666666666666666666 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 555555555555555555.555555555555555555 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 444444444444444444.444444444444444444 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 333333333333333333.333333333333333333 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 222222222222222222.222222222222222222 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 111111111111111111.111111111111111111 AS DECIMAL(38,18)),
        CAST(RAND(CHECKSUM(NEWID())) * 999999999999999999.999999999999999999 AS DECIMAL(38,18)),
        
        -- Money values
        CAST(RAND(CHECKSUM(NEWID())) * 10000 AS MONEY),
        CAST(RAND(CHECKSUM(NEWID())) * 5000 AS MONEY),
        CAST(RAND(CHECKSUM(NEWID())) * 2500 AS MONEY),
        CAST(RAND(CHECKSUM(NEWID())) * 1000 AS MONEY),
        CAST(RAND(CHECKSUM(NEWID())) * 500 AS MONEY),
        
        -- Large text fields
        'Description for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('This is extensive description content with detailed information about the record. ', 20),
        'Secondary description for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('Additional descriptive content goes here. ', 15),
        'Tertiary description for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('More detailed information. ', 25),
        'Notes for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('Important notes and observations. ', 30),
        'Additional notes for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('Supplementary information. ', 20),
        'Comments for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('User comments and feedback. ', 25),
        'Extended comments for record ' + CAST(RowNum AS VARCHAR(50)) + '. ' + REPLICATE('Detailed commentary. ', 18),
        
        -- Fixed-length text fields
        'CODE-' + RIGHT('00000' + CAST(RowNum AS VARCHAR(10)), 8),
        'SEC-' + RIGHT('00000' + CAST((RowNum % 10000) AS VARCHAR(10)), 8),
        'TER-' + RIGHT('00000' + CAST((RowNum % 5000) AS VARCHAR(10)), 8),
        'QUA-' + RIGHT('00000' + CAST((RowNum % 2500) AS VARCHAR(10)), 8),
        'QUI-' + RIGHT('00000' + CAST((RowNum % 1000) AS VARCHAR(10)), 8),
        'Name-' + CAST(RowNum AS VARCHAR(50)),
        'SecondaryName-' + CAST((RowNum % 1000) AS VARCHAR(50)),
        'TertiaryName-' + CAST((RowNum % 500) AS VARCHAR(50)),
        'QuaternaryName-' + CAST((RowNum % 250) AS VARCHAR(50)),
        'QuinaryName-' + CAST((RowNum % 100) AS VARCHAR(50)),
        
        -- Integer counters and quantities
        RowNum, (RowNum % 1000), (RowNum % 500), (RowNum % 250), (RowNum % 100),
        (RowNum % 10000), (RowNum % 5000), (RowNum % 2500), (RowNum % 1000), (RowNum % 500),
        
        -- Boolean flags
        CASE WHEN RowNum % 10 = 0 THEN 0 ELSE 1 END,
        CASE WHEN RowNum % 5 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 3 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 100 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 7 = 0 THEN 0 ELSE 1 END,
        CASE WHEN RowNum % 11 = 0 THEN 0 ELSE 1 END,
        CASE WHEN RowNum % 13 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 17 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 19 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 23 = 0 THEN 0 ELSE 1 END,
        
        -- Date/time fields
        DATEADD(DAY, -(RowNum % 3650), GETDATE()),  -- CreatedDate (up to 10 years ago)
        DATEADD(HOUR, -(RowNum % 8760), GETDATE()), -- ModifiedDate (up to 1 year ago)
        CASE WHEN RowNum % 5 = 0 THEN DATEADD(DAY, -(RowNum % 100), GETDATE()) ELSE NULL END,
        CASE WHEN RowNum % 3 = 0 THEN DATEADD(DAY, -(RowNum % 200), GETDATE()) ELSE NULL END,
        DATEADD(DAY, (RowNum % 365), GETDATE()),     -- ExpiryDate (up to 1 year from now)
        DATEADD(DAY, -(RowNum % 180), GETDATE()),    -- StartDate (up to 6 months ago)
        DATEADD(DAY, (RowNum % 90), GETDATE()),      -- EndDate (up to 3 months from now)
        
        -- Rate and percentage fields
        CAST(RAND(CHECKSUM(NEWID())) * 999999.9999 AS DECIMAL(10,4)),
        CAST(RAND(CHECKSUM(NEWID())) * 888888.8888 AS DECIMAL(10,4)),
        CAST(RAND(CHECKSUM(NEWID())) * 777777.7777 AS DECIMAL(10,4)),
        CAST(RAND(CHECKSUM(NEWID())) * 666666.6666 AS DECIMAL(10,4)),
        CAST(RAND(CHECKSUM(NEWID())) * 555555.5555 AS DECIMAL(10,4)),
        CAST(RAND(CHECKSUM(NEWID())) * 100.00 AS DECIMAL(5,2)),
        CAST(RAND(CHECKSUM(NEWID())) * 100.00 AS DECIMAL(5,2)),
        CAST(RAND(CHECKSUM(NEWID())) * 100.00 AS DECIMAL(5,2)),
        
        -- Additional field columns (30 VARCHAR fields)
        'Field01-' + CAST(RowNum AS VARCHAR(50)), 'Field02-' + CAST(RowNum AS VARCHAR(50)),
        'Field03-' + CAST(RowNum AS VARCHAR(50)), 'Field04-' + CAST(RowNum AS VARCHAR(50)),
        'Field05-' + CAST(RowNum AS VARCHAR(50)), 'Field06-' + CAST(RowNum AS VARCHAR(50)),
        'Field07-' + CAST(RowNum AS VARCHAR(50)), 'Field08-' + CAST(RowNum AS VARCHAR(50)),
        'Field09-' + CAST(RowNum AS VARCHAR(50)), 'Field10-' + CAST(RowNum AS VARCHAR(50)),
        'Field11-' + CAST(RowNum AS VARCHAR(50)), 'Field12-' + CAST(RowNum AS VARCHAR(50)),
        'Field13-' + CAST(RowNum AS VARCHAR(50)), 'Field14-' + CAST(RowNum AS VARCHAR(50)),
        'Field15-' + CAST(RowNum AS VARCHAR(50)), 'Field16-' + CAST(RowNum AS VARCHAR(50)),
        'Field17-' + CAST(RowNum AS VARCHAR(50)), 'Field18-' + CAST(RowNum AS VARCHAR(50)),
        'Field19-' + CAST(RowNum AS VARCHAR(50)), 'Field20-' + CAST(RowNum AS VARCHAR(50)),
        'Field21-' + CAST(RowNum AS VARCHAR(50)), 'Field22-' + CAST(RowNum AS VARCHAR(50)),
        'Field23-' + CAST(RowNum AS VARCHAR(50)), 'Field24-' + CAST(RowNum AS VARCHAR(50)),
        'Field25-' + CAST(RowNum AS VARCHAR(50)), 'Field26-' + CAST(RowNum AS VARCHAR(50)),
        'Field27-' + CAST(RowNum AS VARCHAR(50)), 'Field28-' + CAST(RowNum AS VARCHAR(50)),
        'Field29-' + CAST(RowNum AS VARCHAR(50)), 'Field30-' + CAST(RowNum AS VARCHAR(50)),
        
        -- Value columns (20 INT fields)
        (RowNum % 1000000), (RowNum % 900000), (RowNum % 800000), (RowNum % 700000), (RowNum % 600000),
        (RowNum % 500000), (RowNum % 400000), (RowNum % 300000), (RowNum % 200000), (RowNum % 100000),
        (RowNum % 90000), (RowNum % 80000), (RowNum % 70000), (RowNum % 60000), (RowNum % 50000),
        (RowNum % 40000), (RowNum % 30000), (RowNum % 20000), (RowNum % 10000), (RowNum % 5000),
        
        -- Flag columns (10 BIT fields)
        CASE WHEN RowNum % 2 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 3 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 4 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 6 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 8 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 12 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 16 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 20 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 25 = 0 THEN 1 ELSE 0 END,
        CASE WHEN RowNum % 50 = 0 THEN 1 ELSE 0 END
        
    FROM NumberSequence
    WHERE RowNum BETWEEN @i AND @i + @batch_size - 1;

    SET @i = @i + @batch_size;
    
    -- Progress reporting every 50K rows
    IF @i % 50000 = 1
        PRINT 'Inserted ' + CAST(@i - 1 AS VARCHAR(10)) + ' rows into ProductionTestTable...';
END;

PRINT 'Production data population complete!';

-- Show final row counts
SELECT 'ProductionTestSmall' as TableName, COUNT(*) as RowCount FROM dbo.ProductionTestSmall
UNION ALL
SELECT 'ProductionTestTable', COUNT(*) FROM dbo.ProductionTestTable;

-- Show sample data
PRINT 'Sample data from ProductionTestTable:';
SELECT TOP 3 Id, RecordCode, Amount1, Price1, LEN(Description1) as DescriptionLength, Counter1, IsActive, CreatedDate
FROM dbo.ProductionTestTable
ORDER BY Id;

PRINT 'Production data population script completed successfully!';
GO