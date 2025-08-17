-- Add next day's data to Reporting_Client table for incremental loading testing
-- This script simulates the next day's batch job with ~2M new records

USE StackOverflowMini;

SET NOCOUNT ON;

DECLARE @BatchSize INT = 10000;
DECLARE @RecordsToAdd INT = 2000000;  -- 2M records for next day
DECLARE @BatchesNeeded INT;
DECLARE @CurrentBatch INT = 1;
DECLARE @RecordsInserted INT = 0;
DECLARE @NextSystemCalendarID INT;

-- Calculate next SystemCalendarID (next day after the latest existing date)
SELECT @NextSystemCalendarID = MAX(SystemCalendarID) + 1 FROM dbo.Reporting_Client;

-- If no data exists, start with today
IF @NextSystemCalendarID IS NULL
    SET @NextSystemCalendarID = CAST(FORMAT(GETDATE(), 'yyyyMMdd') AS INT);

SET @BatchesNeeded = @RecordsToAdd / @BatchSize;

PRINT 'Adding next day batch data for incremental loading test';
PRINT 'Configuration:';
PRINT '  - Next SystemCalendarID: ' + CAST(@NextSystemCalendarID AS VARCHAR(10));
PRINT '  - Records to add: ' + CAST(@RecordsToAdd AS VARCHAR(20));
PRINT '  - Batch size: ' + CAST(@BatchSize AS VARCHAR(20));
PRINT '  - Batches needed: ' + CAST(@BatchesNeeded AS VARCHAR(20));

-- Check current state
SELECT 
    'Current Data State' AS Info,
    COUNT(*) AS TotalRecords,
    COUNT(DISTINCT SystemCalendarID) AS UniqueDays,
    MIN(SystemCalendarID) AS EarliestDay,
    MAX(SystemCalendarID) AS LatestDay
FROM dbo.Reporting_Client;

PRINT '';
PRINT 'Starting incremental data load...';

-- Add next day's data in batches
WHILE @CurrentBatch <= @BatchesNeeded
BEGIN
    INSERT INTO dbo.Reporting_Client (
        SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
        ExternalClientID, ParentClientID, ClientTypeID, RegionCode, CountryCode,
        TerritoryCode, SegmentCode,
        
        -- Financial metrics
        Revenue, Cost, Profit, MarginAmount, TaxAmount, DiscountAmount,
        CommissionAmount, BonusAmount, PenaltyAmount, AdjustmentAmount,
        NetAmount, GrossAmount, CumulativeAmount, YearToDateAmount, LifetimeValue,
        
        -- Performance metrics  
        ConversionRate, ClickThroughRate, BounceRate, EngagementScore, SatisfactionScore,
        NpsScore, ChurnProbability, RiskScore, QualityIndex, PerformanceIndex,
        
        -- Volume metrics
        TransactionCount, OrderCount, ProductCount, ServiceCount, UserCount,
        SessionCount, ClickCount, ViewCount, DownloadCount, ShareCount,
        CommentCount, LikeCount, FollowCount, ReferralCount, ComplaintCount,
        
        -- Text fields
        ClientName, CompanyName, Industry, Sector, BusinessType,
        ContactName, EmailAddress, PhoneNumber, Address1, Address2,
        City, StateProvince, PostalCode, Website, SocialMediaHandle,
        PreferredLanguage, TimeZone, Currency, PaymentMethod,
        
        -- Boolean flags
        IsActive, IsVip, IsPremium, IsVerified, IsBlocked, IsDeleted,
        HasDiscount, HasLoyaltyCard, AcceptsMarketing, AcceptsEmails,
        AcceptsSms, AcceptsCalls, RequiresApproval, IsTestAccount,
        IsInternalAccount, HasApiAccess, HasMobileApp, HasWebAccess,
        RequiresTwoFactor, IsCompliant,
        
        -- Dates
        CreatedDate, ModifiedDate, LastLoginDate, LastPurchaseDate,
        LastContactDate, RegistrationDate, ExpiryDate, RenewalDate,
        SuspensionDate, ActivationDate,
        
        -- Rates and percentages
        DiscountRate, TaxRate, CommissionRate, InterestRate, InflationRate,
        ExchangeRate, GrowthRate, RetentionRate, MarginPercent, CompletionPercent,
        
        -- Additional codes
        PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode
    )
    SELECT 
        @NextSystemCalendarID,  -- Use next day's SystemCalendarID
        NEWID(),
        -- Generate different ClientID distribution for next day
        ABS(CHECKSUM(NEWID())) % 1000000 + 500000,  -- Shift range for variety
        'NEXT' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6),
        'NXT' + RIGHT('0000000' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR), 7),
        'EXTD' + CAST(ABS(CHECKSUM(NEWID())) % 9999999 AS VARCHAR),
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN NULL ELSE ABS(CHECKSUM(NEWID())) % 100000 END,
        ABS(CHECKSUM(NEWID())) % 50 + 1,
        CASE ABS(CHECKSUM(NEWID())) % 5 
            WHEN 0 THEN 'NAM' WHEN 1 THEN 'EUR' WHEN 2 THEN 'APJ' 
            WHEN 3 THEN 'LAM' ELSE 'MEA' END,
        CASE ABS(CHECKSUM(NEWID())) % 10
            WHEN 0 THEN 'US' WHEN 1 THEN 'GB' WHEN 2 THEN 'DE' WHEN 3 THEN 'FR'
            WHEN 4 THEN 'CA' WHEN 5 THEN 'AU' WHEN 6 THEN 'JP' WHEN 7 THEN 'BR'
            WHEN 8 THEN 'IN' ELSE 'CN' END,
        'NEXT' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Enterprise' WHEN 1 THEN 'SMB' WHEN 2 THEN 'Consumer'
            WHEN 3 THEN 'Government' ELSE 'Education' END,
            
        -- Financial amounts (slightly higher for next day trend)
        CAST((ABS(CHECKSUM(NEWID())) % 12000000) / 100.0 AS MONEY),  -- Revenue (+20%)
        CAST((ABS(CHECKSUM(NEWID())) % 9000000) / 100.0 AS MONEY),   -- Cost  
        CAST((ABS(CHECKSUM(NEWID())) % 3000000) / 100.0 AS MONEY),   -- Profit
        CAST((ABS(CHECKSUM(NEWID())) % 600000) / 100.0 AS MONEY),    -- Margin
        CAST((ABS(CHECKSUM(NEWID())) % 1200000) / 100.0 AS MONEY),   -- Tax
        CAST((ABS(CHECKSUM(NEWID())) % 240000) / 100.0 AS MONEY),    -- Discount
        CAST((ABS(CHECKSUM(NEWID())) % 360000) / 100.0 AS MONEY),    -- Commission
        CAST((ABS(CHECKSUM(NEWID())) % 120000) / 100.0 AS MONEY),    -- Bonus
        CAST((ABS(CHECKSUM(NEWID())) % 60000) / 100.0 AS MONEY),     -- Penalty
        CAST((ABS(CHECKSUM(NEWID())) % 30000) / 100.0 AS MONEY),     -- Adjustment
        
        -- High precision decimals
        CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
        CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
        CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
        CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
        CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
        
        -- Performance metrics (FLOAT)
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 100) - 50 AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 1000) AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
        CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
        
        -- Volume counts (higher for next day)
        ABS(CHECKSUM(NEWID())) % 1200,      -- TransactionCount (+20%)
        ABS(CHECKSUM(NEWID())) % 600,       -- OrderCount
        ABS(CHECKSUM(NEWID())) % 120,       -- ProductCount
        ABS(CHECKSUM(NEWID())) % 60,        -- ServiceCount
        ABS(CHECKSUM(NEWID())) % 12000,     -- UserCount
        ABS(CHECKSUM(NEWID())) % 60000,     -- SessionCount
        ABS(CHECKSUM(NEWID())) % 120000,    -- ClickCount
        ABS(CHECKSUM(NEWID())) % 1200000,   -- ViewCount
        ABS(CHECKSUM(NEWID())) % 12000,     -- DownloadCount
        ABS(CHECKSUM(NEWID())) % 6000,      -- ShareCount
        ABS(CHECKSUM(NEWID())) % 1200,      -- CommentCount
        ABS(CHECKSUM(NEWID())) % 12000,     -- LikeCount
        ABS(CHECKSUM(NEWID())) % 2400,      -- FollowCount
        ABS(CHECKSUM(NEWID())) % 600,       -- ReferralCount
        ABS(CHECKSUM(NEWID())) % 120,       -- ComplaintCount
        
        -- Text fields with "Next Day" markers
        'Next Day Client ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
        'Next Business ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
        CASE ABS(CHECKSUM(NEWID())) % 10
            WHEN 0 THEN 'Technology' WHEN 1 THEN 'Healthcare' WHEN 2 THEN 'Finance'
            WHEN 3 THEN 'Manufacturing' WHEN 4 THEN 'Retail' WHEN 5 THEN 'Education'
            WHEN 6 THEN 'Government' WHEN 7 THEN 'Energy' WHEN 8 THEN 'Media'
            ELSE 'Consulting' END,
        CASE ABS(CHECKSUM(NEWID())) % 8
            WHEN 0 THEN 'Software' WHEN 1 THEN 'Hardware' WHEN 2 THEN 'Services'
            WHEN 3 THEN 'Products' WHEN 4 THEN 'Consulting' WHEN 5 THEN 'Support'
            WHEN 6 THEN 'Training' ELSE 'Research' END,
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'B2B' WHEN 1 THEN 'B2C' WHEN 2 THEN 'B2G'
            WHEN 3 THEN 'Marketplace' ELSE 'Platform' END,
        'Next Contact ' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR),
        'nextuser' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR) + '@nextcompany' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + '.com',
        '+1-' + CAST(ABS(CHECKSUM(NEWID())) % 900 + 100 AS VARCHAR) + '-' + CAST(ABS(CHECKSUM(NEWID())) % 900 + 100 AS VARCHAR) + '-' + CAST(ABS(CHECKSUM(NEWID())) % 9000 + 1000 AS VARCHAR),
        CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + ' Next Street',
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN 'Floor ' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR) ELSE NULL END,
        CASE ABS(CHECKSUM(NEWID())) % 10
            WHEN 0 THEN 'New York' WHEN 1 THEN 'Los Angeles' WHEN 2 THEN 'Chicago'
            WHEN 3 THEN 'Houston' WHEN 4 THEN 'Phoenix' WHEN 5 THEN 'Philadelphia'
            WHEN 6 THEN 'San Antonio' WHEN 7 THEN 'San Diego' WHEN 8 THEN 'Dallas'
            ELSE 'San Jose' END,
        CASE ABS(CHECKSUM(NEWID())) % 10
            WHEN 0 THEN 'NY' WHEN 1 THEN 'CA' WHEN 2 THEN 'IL' WHEN 3 THEN 'TX'
            WHEN 4 THEN 'AZ' WHEN 5 THEN 'PA' WHEN 6 THEN 'TX' WHEN 7 THEN 'CA'
            WHEN 8 THEN 'TX' ELSE 'CA' END,
        RIGHT('00000' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR), 5),
        'https://www.nextcompany' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + '.com',
        '@nextcompany' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR),
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'English' WHEN 1 THEN 'Spanish' WHEN 2 THEN 'French'
            WHEN 3 THEN 'German' ELSE 'Mandarin' END,
        CASE ABS(CHECKSUM(NEWID())) % 8
            WHEN 0 THEN 'UTC-8' WHEN 1 THEN 'UTC-5' WHEN 2 THEN 'UTC-0'
            WHEN 3 THEN 'UTC+1' WHEN 4 THEN 'UTC+8' WHEN 5 THEN 'UTC+9'
            WHEN 6 THEN 'UTC-3' ELSE 'UTC+10' END,
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'USD' WHEN 1 THEN 'EUR' WHEN 2 THEN 'GBP'
            WHEN 3 THEN 'JPY' ELSE 'CAD' END,
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Credit Card' WHEN 1 THEN 'Bank Transfer' WHEN 2 THEN 'PayPal'
            WHEN 3 THEN 'Check' ELSE 'Cash' END,
        
        -- Boolean flags (similar distributions)
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 85 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 15 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 25 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 70 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 5 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 3 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 40 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 60 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 75 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 80 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 30 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 20 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 10 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 2 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 1 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 35 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 65 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 90 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 45 THEN 1 ELSE 0 END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 95 THEN 1 ELSE 0 END,
        
        -- Timestamps (current day for next day data)
        GETUTCDATE(),  -- CreatedDate (current time for next day)
        GETUTCDATE(),  -- ModifiedDate
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 8 THEN DATEADD(HOUR, -(ABS(CHECKSUM(NEWID())) % 24), GETUTCDATE()) ELSE NULL END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 6 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 30), GETUTCDATE()) ELSE NULL END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 7 THEN DATEADD(HOUR, -(ABS(CHECKSUM(NEWID())) % 48), GETUTCDATE()) ELSE NULL END,
        DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()),
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN DATEADD(DAY, (ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()) ELSE NULL END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 4 THEN DATEADD(DAY, (ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()) ELSE NULL END,
        CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 5 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 180), GETUTCDATE()) ELSE NULL END,
        DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()),
        
        -- Rates and percentages
        CAST((ABS(CHECKSUM(NEWID())) % 5000) / 10000.0 AS DECIMAL(10,4)),
        CAST((ABS(CHECKSUM(NEWID())) % 2500) / 10000.0 AS DECIMAL(10,4)),
        CAST((ABS(CHECKSUM(NEWID())) % 1500) / 10000.0 AS DECIMAL(10,4)),
        CAST((ABS(CHECKSUM(NEWID())) % 1000) / 10000.0 AS DECIMAL(10,4)),
        CAST((ABS(CHECKSUM(NEWID())) % 500) / 10000.0 AS DECIMAL(10,4)),
        CAST(0.5 + (ABS(CHECKSUM(NEWID())) % 200000) / 100000.0 AS DECIMAL(15,6)),
        CAST((ABS(CHECKSUM(NEWID())) % 5000 - 2500) / 10000.0 AS DECIMAL(8,4)),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),
        CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),
        
        -- Additional categorization
        CASE ABS(CHECKSUM(NEWID())) % 5
            WHEN 0 THEN 'Critical' WHEN 1 THEN 'High' WHEN 2 THEN 'Medium'
            WHEN 3 THEN 'Low' ELSE 'Info' END,
        CASE ABS(CHECKSUM(NEWID())) % 6
            WHEN 0 THEN 'Active' WHEN 1 THEN 'Pending' WHEN 2 THEN 'Suspended'
            WHEN 3 THEN 'Closed' WHEN 4 THEN 'Review' ELSE 'Expired' END,
        'NCAT' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
        'NSUB' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
        'NCLASS' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR)
        
    FROM master.dbo.spt_values v1
    CROSS JOIN master.dbo.spt_values v2
    WHERE v1.type = 'P' AND v2.type = 'P'
    AND v1.number BETWEEN 1 AND @BatchSize;
    
    SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
    
    -- Progress update every 50 batches
    IF @CurrentBatch % 50 = 0
    BEGIN
        PRINT '  Batch ' + CAST(@CurrentBatch AS VARCHAR(10)) + '/' + CAST(@BatchesNeeded AS VARCHAR(10)) + 
              ' completed. Records inserted: ' + CAST(@RecordsInserted AS VARCHAR(20));
    END
    
    SET @CurrentBatch = @CurrentBatch + 1;
END

PRINT '';
PRINT 'Next day data addition completed!';
PRINT 'Records added: ' + CAST(@RecordsInserted AS VARCHAR(20));

-- Show updated statistics
PRINT '';
PRINT 'Updated data statistics:';

SELECT 
    SystemCalendarID,
    COUNT(*) AS RecordCount,
    MIN(CreatedDate) AS EarliestRecord,
    MAX(CreatedDate) AS LatestRecord,
    FORMAT(COUNT(*), 'N0') AS FormattedCount
FROM dbo.Reporting_Client
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID;

SELECT 
    'Total Records After Addition' AS Metric,
    COUNT(*) AS Value,
    FORMAT(COUNT(*), 'N0') AS FormattedValue
FROM dbo.Reporting_Client;

PRINT 'Ready for incremental sync testing!';