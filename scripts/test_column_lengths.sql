-- Quick test to verify column length compliance
USE StackOverflowMini;

-- Clear any existing data
TRUNCATE TABLE dbo.Reporting_Client;

-- Test insert with corrected column lengths
DECLARE @TestCalendarID INT = 20250815;

INSERT INTO dbo.Reporting_Client (
    SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
    ExternalClientID, CategoryCode, SubCategoryCode, ClassificationCode
)
SELECT 
    @TestCalendarID,
    NEWID(),
    1000001,
    'DAY1-' + RIGHT('000000' + CAST(123456 AS VARCHAR), 6),
    'CLI' + RIGHT('000000' + CAST(123456 AS VARCHAR), 6),  -- Should be 9 chars: CLI123456
    'EXT' + RIGHT('000000' + CAST(123456 AS VARCHAR), 6),  -- Should be 9 chars: EXT123456  
    'CAT' + RIGHT('000' + CAST(123 AS VARCHAR), 3),        -- Should be 6 chars: CAT123
    'SUB' + RIGHT('000' + CAST(123 AS VARCHAR), 3),        -- Should be 6 chars: SUB123
    'CLS' + RIGHT('00' + CAST(12 AS VARCHAR), 2);          -- Should be 5 chars: CLS12

-- Verify insert worked and show lengths
SELECT 
    'Test Results' AS Info,
    SystemCalendarID,
    LEN(ClientCode) AS ClientCodeLength,
    ClientCode,
    LEN(CategoryCode) AS CategoryCodeLength,
    CategoryCode,
    LEN(SubCategoryCode) AS SubCategoryCodeLength,
    SubCategoryCode,
    LEN(ClassificationCode) AS ClassificationCodeLength,
    ClassificationCode
FROM dbo.Reporting_Client;

PRINT 'Column length test completed successfully!';