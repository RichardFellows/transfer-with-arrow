-- Populate SCD2 table with test data demonstrating slowly changing dimensions
-- Creates historical records showing how client data changes over time

USE StackOverflowMini;
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;

-- Configuration parameters
DECLARE @BatchSize INT = 50;
DECLARE @RecordsPerDay INT = 500;  -- Smaller than fact table
DECLARE @DaysToAdd INT = 5;  -- 5 days of SCD2 data
DECLARE @StartingCalendarID INT = CAST(FORMAT(DATEADD(DAY, -4, GETDATE()), 'yyyyMMdd') AS INT);
DECLARE @CurrentDay INT = 1;
DECLARE @RecordsInserted INT = 0;
DECLARE @BatchesPerDay INT;
DECLARE @TotalBusinessKeys INT = 200;  -- 200 unique clients

-- Calculate batches needed per day
SET @BatchesPerDay = @RecordsPerDay / @BatchSize;

PRINT 'SCD2 Reporting_Client Data Population Script';
PRINT '==========================================';

-- Clear existing data
TRUNCATE TABLE dbo.Reporting_Client_SCD2;

-- Display current state
SELECT 
    'Initial Data State' AS Info,
    COUNT(*) AS TotalRecords,
    COUNT(DISTINCT ClientBusinessKey) AS UniqueClients,
    COUNT(CASE WHEN IsLatest = 1 THEN 1 END) AS CurrentVersions
FROM dbo.Reporting_Client_SCD2;

PRINT '';
PRINT 'Configuration:';
PRINT '  - Starting SystemCalendarID: ' + CAST(@StartingCalendarID AS VARCHAR(10));
PRINT '  - Days to add: ' + CAST(@DaysToAdd AS VARCHAR(10));
PRINT '  - Records per day: ' + CAST(@RecordsPerDay AS VARCHAR(20));
PRINT '  - Total business keys: ' + CAST(@TotalBusinessKeys AS VARCHAR(20));
PRINT '  - Will demonstrate SCD2 changes over time';

-- Main data generation loop
WHILE @CurrentDay <= @DaysToAdd
BEGIN
    DECLARE @CurrentCalendarID INT = @StartingCalendarID + (@CurrentDay - 1);
    DECLARE @CurrentDate DATETIME2 = CAST(CAST(@CurrentCalendarID AS VARCHAR(8)) AS DATETIME2);
    
    PRINT '';
    PRINT 'Processing Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' - SystemCalendarID: ' + CAST(@CurrentCalendarID AS VARCHAR(10));
    PRINT 'Date: ' + CONVERT(VARCHAR(10), @CurrentDate, 120);
    
    SET @RecordsInserted = 0;
    
    -- For Day 1, insert initial versions
    IF @CurrentDay = 1
    BEGIN
        PRINT 'Creating initial client versions...';
        
        INSERT INTO dbo.Reporting_Client_SCD2 (
            ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest, SystemCalendarID,
            ClientID, ClientName, CompanyName, Industry, Sector, BusinessType,
            ContactName, EmailAddress, PhoneNumber, Address1, City, StateProvince, 
            PostalCode, CountryCode, ClientTypeID, RegionCode, TerritoryCode, SegmentCode,
            PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode,
            CreditLimit, PaymentTerms, DiscountRate, TaxRate, Currency,
            IsActive, IsVip, IsPremium, IsVerified, AcceptsMarketing, RequiresApproval,
            CreatedBy, ModifiedBy, SourceSystem, ChangeType, ChangeReason
        )
        SELECT TOP (@RecordsPerDay)
            'CLIENT_' + RIGHT('0000' + CAST((ROW_NUMBER() OVER (ORDER BY NEWID()) % @TotalBusinessKeys) + 1 AS VARCHAR), 4) AS ClientBusinessKey,
            @CurrentDate AS EffectiveFromDate,
            NULL AS EffectiveToDate,  -- Current version
            1 AS IsLatest,
            @CurrentCalendarID AS SystemCalendarID,
            
            -- Core client data
            ABS(CHECKSUM(NEWID())) % 100000 + 1000 AS ClientID,
            'Initial Client ' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR) AS ClientName,
            'Company ' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR) + ' Inc' AS CompanyName,
            CASE ABS(CHECKSUM(NEWID())) % 5 
                WHEN 0 THEN 'Technology' WHEN 1 THEN 'Healthcare' WHEN 2 THEN 'Finance'
                WHEN 3 THEN 'Manufacturing' ELSE 'Retail' END AS Industry,
            CASE ABS(CHECKSUM(NEWID())) % 3 
                WHEN 0 THEN 'Services' WHEN 1 THEN 'Products' ELSE 'Mixed' END AS Sector,
            CASE ABS(CHECKSUM(NEWID())) % 4 
                WHEN 0 THEN 'B2B' WHEN 1 THEN 'B2C' WHEN 2 THEN 'B2G' ELSE 'Mixed' END AS BusinessType,
            
            -- Contact info
            'John Doe' AS ContactName,
            'contact@company.com' AS EmailAddress,
            '+1-555-' + RIGHT('0000' + CAST(ABS(CHECKSUM(NEWID())) % 10000 AS VARCHAR), 4) AS PhoneNumber,
            CAST(ABS(CHECKSUM(NEWID())) % 9999 + 1 AS VARCHAR) + ' Main St' AS Address1,
            'Initial City' AS City,
            CASE ABS(CHECKSUM(NEWID())) % 5 
                WHEN 0 THEN 'CA' WHEN 1 THEN 'NY' WHEN 2 THEN 'TX' WHEN 3 THEN 'FL' ELSE 'WA' END AS StateProvince,
            RIGHT('00000' + CAST(ABS(CHECKSUM(NEWID())) % 100000 AS VARCHAR), 5) AS PostalCode,
            'US' AS CountryCode,
            
            -- Business attributes
            ABS(CHECKSUM(NEWID())) % 10 + 1 AS ClientTypeID,
            'NAM' AS RegionCode,
            'TERR' + CAST(ABS(CHECKSUM(NEWID())) % 10 + 1 AS VARCHAR) AS TerritoryCode,
            CASE ABS(CHECKSUM(NEWID())) % 3 
                WHEN 0 THEN 'Enterprise' WHEN 1 THEN 'SMB' ELSE 'Startup' END AS SegmentCode,
            CASE ABS(CHECKSUM(NEWID())) % 3 
                WHEN 0 THEN 'High' WHEN 1 THEN 'Medium' ELSE 'Low' END AS PriorityLevel,
            'Active' AS StatusCode,
            'CAT_A' AS CategoryCode,
            'SUB_01' AS SubCategoryCode,
            'CLS_1' AS ClassificationCode,
            
            -- Financial
            CAST((ABS(CHECKSUM(NEWID())) % 100000 + 10000) AS MONEY) AS CreditLimit,
            'Net 30' AS PaymentTerms,
            CAST((ABS(CHECKSUM(NEWID())) % 500) / 10000.0 AS DECIMAL(5,4)) AS DiscountRate,
            CAST(0.0875 AS DECIMAL(5,4)) AS TaxRate,  -- Standard tax rate
            'USD' AS Currency,
            
            -- Flags
            1 AS IsActive, 0 AS IsVip, 0 AS IsPremium, 1 AS IsVerified, 1 AS AcceptsMarketing, 0 AS RequiresApproval,
            
            -- Audit
            'SCD2_ETL_INITIAL' AS CreatedBy,
            'SCD2_ETL_INITIAL' AS ModifiedBy,
            'StackOverflow' AS SourceSystem,
            'INSERT' AS ChangeType,
            'Initial client load' AS ChangeReason
        FROM master.dbo.spt_values v1
        CROSS JOIN master.dbo.spt_values v2
        WHERE v1.type = 'P' AND v2.type = 'P';
        
        SET @RecordsInserted = @@ROWCOUNT;
    END
    ELSE
    BEGIN
        -- For subsequent days, create some updates (SCD2 changes)
        PRINT 'Creating SCD2 updates for existing clients...';
        
        -- Step 1: Close some existing records and create new versions
        DECLARE @ChangesToMake INT = @RecordsPerDay / 4;  -- 25% of daily records are changes
        
        -- Update existing current records to close them
        WITH ClientsToUpdate AS (
            SELECT TOP (@ChangesToMake) 
                [Key], ClientBusinessKey, EffectiveFromDate
            FROM dbo.Reporting_Client_SCD2 
            WHERE IsLatest = 1 
            ORDER BY NEWID()
        )
        UPDATE scd2 
        SET EffectiveToDate = DATEADD(SECOND, -1, @CurrentDate),
            IsLatest = 0,
            ModifiedBy = 'SCD2_ETL_UPDATE'
        FROM dbo.Reporting_Client_SCD2 scd2
        INNER JOIN ClientsToUpdate ctu ON scd2.[Key] = ctu.[Key];
        
        -- Step 2: Insert new versions of those clients with changes
        INSERT INTO dbo.Reporting_Client_SCD2 (
            ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest, SystemCalendarID,
            ClientID, ClientName, CompanyName, Industry, Sector, BusinessType,
            ContactName, EmailAddress, PhoneNumber, Address1, City, StateProvince, 
            PostalCode, CountryCode, ClientTypeID, RegionCode, TerritoryCode, SegmentCode,
            PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode,
            CreditLimit, PaymentTerms, DiscountRate, TaxRate, Currency,
            IsActive, IsVip, IsPremium, IsVerified, AcceptsMarketing, RequiresApproval,
            CreatedBy, ModifiedBy, SourceSystem, ChangeType, ChangeReason
        )
        SELECT TOP (@ChangesToMake)
            old.ClientBusinessKey,
            @CurrentDate AS EffectiveFromDate,
            NULL AS EffectiveToDate,  -- New current version
            1 AS IsLatest,
            @CurrentCalendarID AS SystemCalendarID,
            
            -- Copy most attributes, but change some to simulate SCD2
            old.ClientID,
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 = 0 
                THEN 'Updated ' + old.ClientName 
                ELSE old.ClientName END AS ClientName,  -- 10% chance of name change
            old.CompanyName,
            old.Industry,
            old.Sector,
            old.BusinessType,
            
            -- Contact changes (common SCD2 scenario)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 5 = 0 
                THEN 'Jane Smith' 
                ELSE old.ContactName END AS ContactName,  -- 20% chance of contact change
            CASE WHEN ABS(CHECKSUM(NEWID())) % 8 = 0 
                THEN 'newemail@company.com' 
                ELSE old.EmailAddress END AS EmailAddress,  -- 12.5% chance of email change
            CASE WHEN ABS(CHECKSUM(NEWID())) % 6 = 0 
                THEN '+1-555-' + RIGHT('0000' + CAST(ABS(CHECKSUM(NEWID())) % 10000 AS VARCHAR), 4)
                ELSE old.PhoneNumber END AS PhoneNumber,  -- 16% chance of phone change
            old.Address1,
            old.City,
            old.StateProvince,
            old.PostalCode,
            old.CountryCode,
            
            -- Business attribute changes
            old.ClientTypeID,
            old.RegionCode,
            old.TerritoryCode,
            CASE WHEN ABS(CHECKSUM(NEWID())) % 15 = 0 
                THEN CASE ABS(CHECKSUM(NEWID())) % 3 WHEN 0 THEN 'Enterprise' WHEN 1 THEN 'SMB' ELSE 'Startup' END
                ELSE old.SegmentCode END AS SegmentCode,  -- 6.7% chance of segment change
            CASE WHEN ABS(CHECKSUM(NEWID())) % 12 = 0 
                THEN CASE ABS(CHECKSUM(NEWID())) % 3 WHEN 0 THEN 'High' WHEN 1 THEN 'Medium' ELSE 'Low' END
                ELSE old.PriorityLevel END AS PriorityLevel,  -- 8.3% chance of priority change
            CASE WHEN ABS(CHECKSUM(NEWID())) % 20 = 0 
                THEN 'Premium' 
                ELSE old.StatusCode END AS StatusCode,  -- 5% chance of status upgrade
            old.CategoryCode,
            old.SubCategoryCode,
            old.ClassificationCode,
            
            -- Financial changes
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 = 0 
                THEN CAST((ABS(CHECKSUM(NEWID())) % 200000 + 20000) AS MONEY)
                ELSE old.CreditLimit END AS CreditLimit,  -- 10% chance of credit limit change
            old.PaymentTerms,
            CASE WHEN ABS(CHECKSUM(NEWID())) % 15 = 0 
                THEN CAST((ABS(CHECKSUM(NEWID())) % 750) / 10000.0 AS DECIMAL(5,4))
                ELSE old.DiscountRate END AS DiscountRate,  -- 6.7% chance of discount change
            old.TaxRate,
            old.Currency,
            
            -- Flag changes
            old.IsActive,
            CASE WHEN ABS(CHECKSUM(NEWID())) % 25 = 0 THEN 1 ELSE old.IsVip END AS IsVip,  -- 4% chance of VIP upgrade
            CASE WHEN ABS(CHECKSUM(NEWID())) % 20 = 0 THEN 1 ELSE old.IsPremium END AS IsPremium,  -- 5% chance of Premium upgrade
            old.IsVerified,
            old.AcceptsMarketing,
            old.RequiresApproval,
            
            -- Audit
            'SCD2_ETL_UPDATE' AS CreatedBy,
            'SCD2_ETL_UPDATE' AS ModifiedBy,
            'StackOverflow' AS SourceSystem,
            'UPDATE' AS ChangeType,
            CASE 
                WHEN ABS(CHECKSUM(NEWID())) % 4 = 0 THEN 'Contact information updated'
                WHEN ABS(CHECKSUM(NEWID())) % 4 = 1 THEN 'Business segment changed'
                WHEN ABS(CHECKSUM(NEWID())) % 4 = 2 THEN 'Credit limit adjustment'
                ELSE 'Status or priority change'
            END AS ChangeReason
        FROM dbo.Reporting_Client_SCD2 old
        WHERE old.IsLatest = 0 
        AND old.EffectiveToDate = DATEADD(SECOND, -1, @CurrentDate)
        ORDER BY old.ClientBusinessKey;
        
        SET @RecordsInserted = @@ROWCOUNT;
        
        -- Step 3: Add some completely new clients
        DECLARE @NewClients INT = @RecordsPerDay - @ChangesToMake;
        
        INSERT INTO dbo.Reporting_Client_SCD2 (
            ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest, SystemCalendarID,
            ClientID, ClientName, CompanyName, Industry, Sector, BusinessType,
            ContactName, EmailAddress, PhoneNumber, Address1, City, StateProvince, 
            PostalCode, CountryCode, ClientTypeID, RegionCode, TerritoryCode, SegmentCode,
            PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode,
            CreditLimit, PaymentTerms, DiscountRate, TaxRate, Currency,
            IsActive, IsVip, IsPremium, IsVerified, AcceptsMarketing, RequiresApproval,
            CreatedBy, ModifiedBy, SourceSystem, ChangeType, ChangeReason
        )
        SELECT TOP (@NewClients)
            'CLIENT_' + RIGHT('0000' + CAST((ABS(CHECKSUM(NEWID())) % 900) + @TotalBusinessKeys + (@CurrentDay * 100) AS VARCHAR), 4) AS ClientBusinessKey,
            @CurrentDate AS EffectiveFromDate,
            NULL AS EffectiveToDate,
            1 AS IsLatest,
            @CurrentCalendarID AS SystemCalendarID,
            
            -- New client data
            ABS(CHECKSUM(NEWID())) % 100000 + (@CurrentDay * 10000) AS ClientID,
            'New Client Day' + CAST(@CurrentDay AS VARCHAR) + ' #' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR) AS ClientName,
            'NewCorp Day' + CAST(@CurrentDay AS VARCHAR) + ' #' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR) AS CompanyName,
            CASE ABS(CHECKSUM(NEWID())) % 6 
                WHEN 0 THEN 'Technology' WHEN 1 THEN 'Healthcare' WHEN 2 THEN 'Finance'
                WHEN 3 THEN 'Manufacturing' WHEN 4 THEN 'Retail' ELSE 'Energy' END AS Industry,
            CASE ABS(CHECKSUM(NEWID())) % 3 
                WHEN 0 THEN 'Services' WHEN 1 THEN 'Products' ELSE 'Mixed' END AS Sector,
            'B2B' AS BusinessType,
            
            -- New contact info
            'New Contact' AS ContactName,
            'newcontact@newcorp.com' AS EmailAddress,
            '+1-555-' + RIGHT('0000' + CAST(ABS(CHECKSUM(NEWID())) % 10000 AS VARCHAR), 4) AS PhoneNumber,
            CAST(ABS(CHECKSUM(NEWID())) % 9999 + 1 AS VARCHAR) + ' Innovation Blvd' AS Address1,
            'New City' AS City,
            'CA' AS StateProvince,
            RIGHT('00000' + CAST(ABS(CHECKSUM(NEWID())) % 100000 AS VARCHAR), 5) AS PostalCode,
            'US' AS CountryCode,
            
            -- Standard new client attributes
            1 AS ClientTypeID, 'NAM' AS RegionCode, 'TERR_NEW' AS TerritoryCode, 'Startup' AS SegmentCode,
            'Medium' AS PriorityLevel, 'New' AS StatusCode, 'CAT_NEW' AS CategoryCode, 'SUB_NEW' AS SubCategoryCode, 'CLS_NEW' AS ClassificationCode,
            
            -- Conservative financial settings for new clients
            CAST(25000 AS MONEY) AS CreditLimit, 'Net 15' AS PaymentTerms,
            CAST(0.0000 AS DECIMAL(5,4)) AS DiscountRate, CAST(0.0875 AS DECIMAL(5,4)) AS TaxRate, 'USD' AS Currency,
            
            -- Default flags for new clients
            1 AS IsActive, 0 AS IsVip, 0 AS IsPremium, 0 AS IsVerified, 1 AS AcceptsMarketing, 1 AS RequiresApproval,
            
            -- Audit
            'SCD2_ETL_NEW' AS CreatedBy, 'SCD2_ETL_NEW' AS ModifiedBy, 'StackOverflow' AS SourceSystem,
            'INSERT' AS ChangeType, 'New client onboarding' AS ChangeReason
        FROM master.dbo.spt_values v1
        WHERE v1.type = 'P' AND v1.number <= @NewClients;
        
        SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
    END
    
    PRINT 'Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' completed. Records inserted: ' + CAST(@RecordsInserted AS VARCHAR(20));
    SET @CurrentDay = @CurrentDay + 1;
END

-- Final statistics
PRINT '';
PRINT 'SCD2 data population completed successfully!';
PRINT 'Final statistics:';

-- Overall counts
SELECT 
    'Overall Statistics' AS Category,
    COUNT(*) AS TotalRecords,
    COUNT(DISTINCT ClientBusinessKey) AS UniqueBusinessKeys,
    COUNT(CASE WHEN IsLatest = 1 THEN 1 END) AS CurrentVersions,
    COUNT(CASE WHEN IsLatest = 0 THEN 1 END) AS HistoricalVersions,
    FORMAT(COUNT(*), 'N0') AS FormattedTotalRecords
FROM dbo.Reporting_Client_SCD2;

-- By day breakdown
SELECT 
    SystemCalendarID,
    COUNT(*) AS RecordCount,
    COUNT(DISTINCT ClientBusinessKey) AS UniqueClients,
    COUNT(CASE WHEN ChangeType = 'INSERT' THEN 1 END) AS NewClients,
    COUNT(CASE WHEN ChangeType = 'UPDATE' THEN 1 END) AS UpdatedClients,
    FORMAT(COUNT(*), 'N0') AS FormattedCount
FROM dbo.Reporting_Client_SCD2
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID;

-- Change type distribution
SELECT 
    ChangeType,
    COUNT(*) AS RecordCount,
    FORMAT(COUNT(*), 'N0') AS FormattedCount,
    CAST(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dbo.Reporting_Client_SCD2) AS DECIMAL(5,2)) AS Percentage
FROM dbo.Reporting_Client_SCD2
GROUP BY ChangeType
ORDER BY COUNT(*) DESC;

-- Sample of SCD2 history for one client
SELECT TOP 5 
    'Sample SCD2 History' AS Info,
    ClientBusinessKey, [Key], EffectiveFromDate, EffectiveToDate, IsLatest, 
    ClientName, ContactName, SegmentCode, StatusCode, ChangeType, ChangeReason
FROM dbo.Reporting_Client_SCD2 
WHERE ClientBusinessKey = (SELECT TOP 1 ClientBusinessKey FROM dbo.Reporting_Client_SCD2 WHERE IsLatest = 0 ORDER BY ClientBusinessKey)
ORDER BY EffectiveFromDate;

PRINT 'SCD2 table ready for incremental loading tests!';
PRINT 'Use SystemCalendarID for incremental watermark.';
PRINT 'Use IsLatest = 1 for current dimension lookups.';
PRINT 'Historical versions preserved with EffectiveFromDate/EffectiveToDate ranges.';