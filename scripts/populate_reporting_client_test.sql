-- Reduced test version of unified script for quick validation
-- Tests the logic with small amounts of data (1000 records per day instead of 2M)

USE StackOverflowMini;
SET NOCOUNT ON;

DECLARE @BatchSize INT = 100;  -- Much smaller for testing
DECLARE @RecordsPerDay INT = 1000;  -- 1K instead of 2M for quick test
DECLARE @DaysToAdd INT;
DECLARE @StartingCalendarID INT;
DECLARE @CurrentDay INT = 1;
DECLARE @RecordsInserted INT = 0;
DECLARE @BatchesPerDay INT;
DECLARE @CurrentBatch INT;
DECLARE @IsInitialLoad BIT = 0;

SET @BatchesPerDay = @RecordsPerDay / @BatchSize;

PRINT 'QUICK TEST: Unified Reporting_Client Data Population';
PRINT '==================================================';

-- Check current state and determine what to do
IF NOT EXISTS (SELECT 1 FROM dbo.Reporting_Client)
BEGIN
    SET @IsInitialLoad = 1;
    SET @DaysToAdd = 3;
    SET @StartingCalendarID = CAST(FORMAT(DATEADD(DAY, -2, GETDATE()), 'yyyyMMdd') AS INT);
    PRINT 'INITIAL LOAD MODE: Table is empty, loading 3 days of test data (1K records each)';
END
ELSE
BEGIN
    SET @IsInitialLoad = 0;
    SET @DaysToAdd = 1;
    SELECT @StartingCalendarID = MAX(SystemCalendarID) + 1 FROM dbo.Reporting_Client;
    PRINT 'INCREMENTAL LOAD MODE: Adding next day test data (1K records)';
END

PRINT 'Configuration:';
PRINT '  - Mode: ' + CASE WHEN @IsInitialLoad = 1 THEN 'Initial Load' ELSE 'Incremental Load' END;
PRINT '  - Starting SystemCalendarID: ' + CAST(@StartingCalendarID AS VARCHAR(10));
PRINT '  - Days to add: ' + CAST(@DaysToAdd AS VARCHAR(10));
PRINT '  - Records per day: ' + CAST(@RecordsPerDay AS VARCHAR(20));

-- Main data generation loop
WHILE @CurrentDay <= @DaysToAdd
BEGIN
    DECLARE @CurrentCalendarID INT = @StartingCalendarID + (@CurrentDay - 1);
    
    PRINT 'Processing Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' - SystemCalendarID: ' + CAST(@CurrentCalendarID AS VARCHAR(10));
    
    SET @CurrentBatch = 1;
    SET @RecordsInserted = 0;
    
    -- Insert data in batches for this day
    WHILE @CurrentBatch <= @BatchesPerDay
    BEGIN
        INSERT INTO dbo.Reporting_Client (
            SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
            ExternalClientID, ParentClientID, ClientTypeID, RegionCode, CountryCode,
            TerritoryCode, SegmentCode,
            Revenue, Cost, Profit, MarginAmount, TaxAmount, DiscountAmount,
            CommissionAmount, BonusAmount, PenaltyAmount, AdjustmentAmount,
            NetAmount, GrossAmount, CumulativeAmount, YearToDateAmount, LifetimeValue,
            ConversionRate, ClickThroughRate, BounceRate, EngagementScore, SatisfactionScore,
            NpsScore, ChurnProbability, RiskScore, QualityIndex, PerformanceIndex,
            TransactionCount, OrderCount, ProductCount, ServiceCount, UserCount,
            SessionCount, ClickCount, ViewCount, DownloadCount, ShareCount,
            CommentCount, LikeCount, FollowCount, ReferralCount, ComplaintCount,
            ClientName, CompanyName, Industry, Sector, BusinessType,
            ContactName, EmailAddress, PhoneNumber, Address1, Address2,
            City, StateProvince, PostalCode, Website, SocialMediaHandle,
            PreferredLanguage, TimeZone, Currency, PaymentMethod,
            IsActive, IsVip, IsPremium, IsVerified, IsBlocked, IsDeleted,
            HasDiscount, HasLoyaltyCard, AcceptsMarketing, AcceptsEmails,
            AcceptsSms, AcceptsCalls, RequiresApproval, IsTestAccount,
            IsInternalAccount, HasApiAccess, HasMobileApp, HasWebAccess,
            RequiresTwoFactor, IsCompliant,
            CreatedDate, ModifiedDate, LastLoginDate, LastPurchaseDate,
            LastContactDate, RegistrationDate, ExpiryDate, RenewalDate,
            SuspensionDate, ActivationDate,
            DiscountRate, TaxRate, CommissionRate, InterestRate, InflationRate,
            ExchangeRate, GrowthRate, RetentionRate, MarginPercent, CompletionPercent,
            PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode
        )
        SELECT 
            @CurrentCalendarID,
            NEWID(),
            ABS(CHECKSUM(NEWID())) % 1000000 + (@CurrentDay * 1000000),
            CASE @CurrentDay 
                WHEN 1 THEN 'DAY1-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                WHEN 2 THEN 'DAY2-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                WHEN 3 THEN 'DAY3-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                ELSE 'NEXT-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
            END,
            'CLI' + CAST(@CurrentCalendarID AS VARCHAR) + '-' + RIGHT('0000000' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR), 7),
            'EXT' + CAST(@CurrentCalendarID AS VARCHAR) + '-' + CAST(ABS(CHECKSUM(NEWID())) % 9999999 AS VARCHAR),
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN NULL ELSE ABS(CHECKSUM(NEWID())) % 100000 END,
            ABS(CHECKSUM(NEWID())) % 50 + 1,
            'NAM', 'US', 'TERR001', 'Enterprise',
            
            -- Simplified financial data
            CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 80000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 20000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 5000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 2000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 3000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 1000) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 500) / 100.0 AS MONEY),
            CAST((ABS(CHECKSUM(NEWID())) % 250) / 100.0 AS MONEY),
            
            -- Simplified decimals
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.123456 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.234567 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.345678 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.456789 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.567890 AS DECIMAL(38,18)),
            
            -- Performance metrics
            CAST((ABS(CHECKSUM(NEWID())) % 100) / 100.0 AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) / 100.0 AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) / 100.0 AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) - 50 AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) / 100.0 AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),
            
            -- Volume counts
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 50,
            ABS(CHECKSUM(NEWID())) % 10, ABS(CHECKSUM(NEWID())) % 5,
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 500,
            ABS(CHECKSUM(NEWID())) % 1000, ABS(CHECKSUM(NEWID())) % 10000,
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 50,
            ABS(CHECKSUM(NEWID())) % 10, ABS(CHECKSUM(NEWID())) % 100,
            ABS(CHECKSUM(NEWID())) % 20, ABS(CHECKSUM(NEWID())) % 5,
            ABS(CHECKSUM(NEWID())) % 10,
            
            -- Text fields
            CASE @CurrentDay 
                WHEN 1 THEN 'Day1 Client ' WHEN 2 THEN 'Day2 Client ' WHEN 3 THEN 'Day3 Client '
                ELSE 'Incremental Client ' END + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            'Test Company ' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            'Technology', 'Software', 'B2B',
            'Contact Person ' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR),
            'test@example.com', '+1-555-0199', '123 Test St', NULL,
            'Test City', 'CA', '12345', 'https://test.com', '@test',
            'English', 'UTC-8', 'USD', 'Credit Card',
            
            -- Boolean flags (simplified)
            1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
            
            -- Timestamps
            GETUTCDATE(), GETUTCDATE(), NULL, NULL, NULL,
            DATEADD(DAY, -30, GETUTCDATE()), NULL, NULL, NULL, GETUTCDATE(),
            
            -- Rates
            CAST(0.1 AS DECIMAL(10,4)), CAST(0.08 AS DECIMAL(10,4)),
            CAST(0.05 AS DECIMAL(10,4)), CAST(0.03 AS DECIMAL(10,4)),
            CAST(0.02 AS DECIMAL(10,4)), CAST(1.25 AS DECIMAL(15,6)),
            CAST(0.05 AS DECIMAL(8,4)), CAST(95.0 AS DECIMAL(5,2)),
            CAST(85.0 AS DECIMAL(5,2)), CAST(100.0 AS DECIMAL(5,2)),
            
            -- Codes
            'High', 'Active',
            'CAT' + CAST(@CurrentCalendarID AS VARCHAR) + '-001',
            'SUB' + CAST(@CurrentCalendarID AS VARCHAR) + '-001',
            'CLASS' + CAST(@CurrentCalendarID AS VARCHAR) + '-01'
            
        FROM master.dbo.spt_values v1
        WHERE v1.type = 'P' AND v1.number BETWEEN 1 AND @BatchSize;
        
        SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
        SET @CurrentBatch = @CurrentBatch + 1;
    END
    
    PRINT 'Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' completed. Records inserted: ' + CAST(@RecordsInserted AS VARCHAR(20));
    SET @CurrentDay = @CurrentDay + 1;
END

-- Show results
PRINT 'Test completed! Results:';

SELECT 
    SystemCalendarID,
    COUNT(*) AS RecordCount,
    MIN(ClientName) AS SampleClientName,
    MIN(AccountNumber) AS SampleAccount
FROM dbo.Reporting_Client
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID;

SELECT 
    'Total Test Records' AS Metric,
    COUNT(*) AS Value
FROM dbo.Reporting_Client;