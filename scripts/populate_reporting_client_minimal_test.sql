-- Minimal test to verify the unified script logic works
USE StackOverflowMini;
SET NOCOUNT ON;

-- Clear any existing data
TRUNCATE TABLE dbo.Reporting_Client;

PRINT 'Testing unified script logic with minimal data...';

-- Insert a few test records to verify column lengths work
INSERT INTO dbo.Reporting_Client (
    SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
    ExternalClientID, Revenue, Cost, Profit, IsActive, CreatedDate
)
VALUES 
    (20250815, NEWID(), 1000001, 'DAY1-123456', 'CLI123456', 'EXT123456', 1000.00, 800.00, 200.00, 1, GETUTCDATE()),
    (20250815, NEWID(), 1000002, 'DAY1-123457', 'CLI123457', 'EXT123457', 1100.00, 850.00, 250.00, 1, GETUTCDATE()),
    (20250815, NEWID(), 1000003, 'DAY1-123458', 'CLI123458', 'EXT123458', 1200.00, 900.00, 300.00, 1, GETUTCDATE());

-- Check what we inserted
SELECT 
    'Initial Test Data' AS Info,
    COUNT(*) AS RecordCount,
    MAX(LEN(ClientCode)) AS MaxClientCodeLength,
    MAX(ClientCode) AS SampleClientCode
FROM dbo.Reporting_Client;

-- Now test the unified script detection logic
DECLARE @DaysToAdd INT;
DECLARE @StartingCalendarID INT;
DECLARE @IsInitialLoad BIT = 0;

IF NOT EXISTS (SELECT 1 FROM dbo.Reporting_Client)
BEGIN
    SET @IsInitialLoad = 1;
    SET @DaysToAdd = 3;
    SET @StartingCalendarID = CAST(FORMAT(DATEADD(DAY, -2, GETDATE()), 'yyyyMMdd') AS INT);
    PRINT 'INITIAL LOAD MODE: Table is empty, loading 3 days of historical data';
END
ELSE
BEGIN
    SET @IsInitialLoad = 0;
    SET @DaysToAdd = 1;
    SELECT @StartingCalendarID = MAX(SystemCalendarID) + 1 FROM dbo.Reporting_Client;
    PRINT 'INCREMENTAL LOAD MODE: Adding next day data';
END

PRINT 'Detection test results:';
PRINT '  - IsInitialLoad: ' + CASE WHEN @IsInitialLoad = 1 THEN 'TRUE' ELSE 'FALSE' END;
PRINT '  - DaysToAdd: ' + CAST(@DaysToAdd AS VARCHAR(10));
PRINT '  - StartingCalendarID: ' + CAST(@StartingCalendarID AS VARCHAR(10));

-- Add one more record to test incremental detection
INSERT INTO dbo.Reporting_Client (
    SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
    ExternalClientID, Revenue, Cost, Profit, IsActive, CreatedDate
)
VALUES 
    (@StartingCalendarID, NEWID(), 2000001, 'NEXT-123459', 'CLI123459', 'EXT123459', 1300.00, 950.00, 350.00, 1, GETUTCDATE());

-- Final check
SELECT 
    'Final Test Results' AS Info,
    SystemCalendarID,
    COUNT(*) AS RecordCount
FROM dbo.Reporting_Client 
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID;

PRINT 'Minimal test completed successfully!';