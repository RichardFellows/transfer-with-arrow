-- Simple production data population script
USE StackOverflowMini;
GO

PRINT 'Starting production data population...';

-- Populate ProductionTestSmall with 50K rows first for quick testing
PRINT 'Populating ProductionTestSmall...';

DECLARE @counter INT = 1;
WHILE @counter <= 50000
BEGIN
    INSERT INTO dbo.ProductionTestSmall (
        HighPrecisionAmount,
        MoneyValue, 
        LargeText,
        StandardText,
        Counter,
        IsActive
    ) VALUES (
        CAST(RAND() * 999999999999999999.999999999999999999 AS DECIMAL(38,18)),
        CAST(RAND() * 10000 AS MONEY),
        'Large text content for row ' + CAST(@counter AS VARCHAR(50)) + '. ' + REPLICATE('Sample data. ', 20),
        'Standard text for row ' + CAST(@counter AS VARCHAR(50)),
        @counter,
        CASE WHEN @counter % 10 = 0 THEN 0 ELSE 1 END
    );
    
    SET @counter = @counter + 1;
    
    IF @counter % 10000 = 1
        PRINT 'Inserted ' + CAST(@counter - 1 AS VARCHAR(10)) + ' rows...';
END;

PRINT 'ProductionTestSmall population complete.';

-- Show counts
SELECT COUNT(*) AS ProductionTestSmallCount FROM dbo.ProductionTestSmall;
SELECT COUNT(*) AS ProductionTestTableCount FROM dbo.ProductionTestTable;

GO