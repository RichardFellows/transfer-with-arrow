-- Quick version of unified script with small batch sizes for testing
-- Intelligently adds 3 days of data on first run, then adds next day's data on subsequent runs

USE ReportingDB;
SET NOCOUNT ON;

-- Configuration parameters (reduced for quick testing)
DECLARE @BatchSize INT = 100;        -- Small batches for quick test
DECLARE @RecordsPerDay INT = 1000;   -- 1K records per day instead of 2M
DECLARE @DaysToAdd INT;
DECLARE @StartingCalendarID INT;
DECLARE @CurrentDay INT = 1;
DECLARE @RecordsInserted INT = 0;
DECLARE @BatchesPerDay INT;
DECLARE @CurrentBatch INT;
DECLARE @IsInitialLoad BIT = 0;

-- Calculate batches needed per day
SET @BatchesPerDay = @RecordsPerDay / @BatchSize;

PRINT 'QUICK TEST: Unified Reporting_Client Data Population Script';
PRINT '========================================================';

-- Check current state and determine what to do
IF NOT EXISTS (SELECT 1 FROM dbo.Reporting_Client)
BEGIN
    -- Table is empty - initial load (3 days)
    SET @IsInitialLoad = 1;
    SET @DaysToAdd = 3;
    SET @StartingCalendarID = CAST(FORMAT(DATEADD(DAY, -2, GETDATE()), 'yyyyMMdd') AS INT); -- Start 2 days ago
    PRINT 'INITIAL LOAD MODE: Table is empty, loading 3 days of test data';
END
ELSE
BEGIN
    -- Table has data - incremental load (1 day)
    SET @IsInitialLoad = 0;
    SET @DaysToAdd = 1;
    SELECT @StartingCalendarID = MAX(SystemCalendarID) + 1 FROM dbo.Reporting_Client;
    PRINT 'INCREMENTAL LOAD MODE: Adding next day''s data';
END

-- Display current state
SELECT 
    'Current Data State' AS Info,
    ISNULL(COUNT(*), 0) AS TotalRecords,
    ISNULL(COUNT(DISTINCT SystemCalendarID), 0) AS UniqueDays,
    ISNULL(MIN(SystemCalendarID), 0) AS EarliestDay,
    ISNULL(MAX(SystemCalendarID), 0) AS LatestDay
FROM dbo.Reporting_Client;

PRINT '';
PRINT 'Configuration:';
PRINT '  - Mode: ' + CASE WHEN @IsInitialLoad = 1 THEN 'Initial Load' ELSE 'Incremental Load' END;
PRINT '  - Starting SystemCalendarID: ' + CAST(@StartingCalendarID AS VARCHAR(10));
PRINT '  - Days to add: ' + CAST(@DaysToAdd AS VARCHAR(10));
PRINT '  - Records per day: ' + CAST(@RecordsPerDay AS VARCHAR(20));
PRINT '  - Batch size: ' + CAST(@BatchSize AS VARCHAR(20));
PRINT '  - Batches per day: ' + CAST(@BatchesPerDay AS VARCHAR(20));
PRINT '  - Total records to add: ' + CAST(@RecordsPerDay * @DaysToAdd AS VARCHAR(20));

-- Main data generation loop
WHILE @CurrentDay <= @DaysToAdd
BEGIN
    DECLARE @CurrentCalendarID INT = @StartingCalendarID + (@CurrentDay - 1);
    
    PRINT '';
    PRINT 'Processing Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' - SystemCalendarID: ' + CAST(@CurrentCalendarID AS VARCHAR(10));
    PRINT 'Target records for this day: ' + CAST(@RecordsPerDay AS VARCHAR(20));
    
    SET @CurrentBatch = 1;
    SET @RecordsInserted = 0;
    
    -- Insert data in batches for this day
    WHILE @CurrentBatch <= @BatchesPerDay
    BEGIN
        INSERT INTO dbo.Reporting_Client (
            SystemCalendarID, BatchProcessID, ClientID, AccountNumber, ClientCode,
            ExternalClientID, ParentClientID, ClientTypeID, RegionCode, CountryCode,
            TerritoryCode, SegmentCode,
            
            -- Financial metrics (subset for quick test)
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
            
            -- Text fields (simplified)
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
            @CurrentCalendarID,
            NEWID(),
            ABS(CHECKSUM(NEWID())) % 1000000 + (@CurrentDay * 1000000),
            
            -- Account numbers with day prefix
            CASE @CurrentDay 
                WHEN 1 THEN 'DAY1-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                WHEN 2 THEN 'DAY2-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                WHEN 3 THEN 'DAY3-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
                ELSE 'NEXT-' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6)
            END,
            
            -- Client codes (fixed length for CHAR(10) constraint)
            'CLI' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6),
            'EXT' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6),
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN NULL ELSE ABS(CHECKSUM(NEWID())) % 100000 END,
            ABS(CHECKSUM(NEWID())) % 50 + 1,
            
            -- Geographic distribution
            'NAM', 'US', 'TERR001', 'Enterprise',
                
            -- Financial amounts with day-based scaling for trend simulation
            CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 AS MONEY),  -- Revenue
            CAST((ABS(CHECKSUM(NEWID())) % 80000) / 100.0 AS MONEY),   -- Cost
            CAST((ABS(CHECKSUM(NEWID())) % 20000) / 100.0 AS MONEY),   -- Profit
            CAST((ABS(CHECKSUM(NEWID())) % 5000) / 100.0 AS MONEY),    -- Margin
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS MONEY),   -- Tax
            CAST((ABS(CHECKSUM(NEWID())) % 2000) / 100.0 AS MONEY),    -- Discount
            CAST((ABS(CHECKSUM(NEWID())) % 3000) / 100.0 AS MONEY),    -- Commission
            CAST((ABS(CHECKSUM(NEWID())) % 1000) / 100.0 AS MONEY),    -- Bonus
            CAST((ABS(CHECKSUM(NEWID())) % 500) / 100.0 AS MONEY),     -- Penalty
            CAST((ABS(CHECKSUM(NEWID())) % 250) / 100.0 AS MONEY),     -- Adjustment
            
            -- High precision decimals
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.123456789012345678 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.234567890123456789 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.345678901234567890 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.456789012345678901 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999) + 0.567890123456789012 AS DECIMAL(38,18)),
            
            -- Performance metrics (FLOAT)
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),   -- ConversionRate
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),   -- ClickThroughRate  
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),   -- BounceRate
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),               -- EngagementScore
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),               -- SatisfactionScore
            CAST((ABS(CHECKSUM(NEWID())) % 100) - 50 AS FLOAT),          -- NpsScore (-50 to 50)
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 10000.0 AS FLOAT),   -- ChurnProbability
            CAST((ABS(CHECKSUM(NEWID())) % 1000) AS FLOAT),              -- RiskScore
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),               -- QualityIndex
            CAST((ABS(CHECKSUM(NEWID())) % 100) AS FLOAT),               -- PerformanceIndex
            
            -- Volume counts
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 50,
            ABS(CHECKSUM(NEWID())) % 10, ABS(CHECKSUM(NEWID())) % 5,
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 500,
            ABS(CHECKSUM(NEWID())) % 1000, ABS(CHECKSUM(NEWID())) % 10000,
            ABS(CHECKSUM(NEWID())) % 100, ABS(CHECKSUM(NEWID())) % 50,
            ABS(CHECKSUM(NEWID())) % 10, ABS(CHECKSUM(NEWID())) % 100,
            ABS(CHECKSUM(NEWID())) % 20, ABS(CHECKSUM(NEWID())) % 5,
            ABS(CHECKSUM(NEWID())) % 10,
            
            -- Text fields with day-specific prefixes
            CASE @CurrentDay 
                WHEN 1 THEN 'Day1 Client ' WHEN 2 THEN 'Day2 Client ' WHEN 3 THEN 'Day3 Client '
                ELSE 'Incremental Client ' END + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            CASE @CurrentDay 
                WHEN 1 THEN 'Day1 Business ' WHEN 2 THEN 'Day2 Business ' WHEN 3 THEN 'Day3 Business '
                ELSE 'Next Business ' END + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
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
            CAST((ABS(CHECKSUM(NEWID())) % 5000) / 10000.0 AS DECIMAL(10,4)),  
            CAST((ABS(CHECKSUM(NEWID())) % 2500) / 10000.0 AS DECIMAL(10,4)),  
            CAST((ABS(CHECKSUM(NEWID())) % 1500) / 10000.0 AS DECIMAL(10,4)),  
            CAST((ABS(CHECKSUM(NEWID())) % 1000) / 10000.0 AS DECIMAL(10,4)),  
            CAST((ABS(CHECKSUM(NEWID())) % 500) / 10000.0 AS DECIMAL(10,4)),   
            CAST(0.5 + (ABS(CHECKSUM(NEWID())) % 20000) / 10000.0 AS DECIMAL(15,6)), 
            CAST((ABS(CHECKSUM(NEWID())) % 500 - 250) / 1000.0 AS DECIMAL(8,4)),    
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   
            
            -- Codes (fixed length)
            'High', 'Active',
            'CAT' + RIGHT('000' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR), 3),
            'SUB' + RIGHT('000' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR), 3), 
            'CLS' + RIGHT('00' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR), 2)
            
        FROM master.dbo.spt_values v1
        WHERE v1.type = 'P' AND v1.number BETWEEN 1 AND @BatchSize;
        
        SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
        
        -- Progress update every 5 batches
        IF @CurrentBatch % 5 = 0
        BEGIN
            PRINT '  Batch ' + CAST(@CurrentBatch AS VARCHAR(10)) + '/' + CAST(@BatchesPerDay AS VARCHAR(10)) + 
                  ' completed. Records so far today: ' + CAST(@CurrentBatch * @BatchSize AS VARCHAR(20));
        END
        
        SET @CurrentBatch = @CurrentBatch + 1;
    END
    
    PRINT 'Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' completed. Records inserted: ' + CAST(@RecordsInserted AS VARCHAR(20));
    SET @CurrentDay = @CurrentDay + 1;
END

-- Final statistics
PRINT '';
PRINT 'Data population completed successfully!';
PRINT 'Mode: ' + CASE WHEN @IsInitialLoad = 1 THEN 'Initial Load' ELSE 'Incremental Load' END;
PRINT 'Final statistics:';

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
    CASE WHEN @IsInitialLoad = 1 THEN 'Total Records After Initial Load' ELSE 'Total Records After Incremental Load' END AS Metric,
    COUNT(*) AS Value,
    FORMAT(COUNT(*), 'N0') AS FormattedValue
FROM dbo.Reporting_Client;

-- Show data distribution by day prefix for verification
SELECT 
    'Data Distribution by Prefix' AS Info,
    CASE 
        WHEN ClientName LIKE 'Day1%' THEN 'Day 1 Data'
        WHEN ClientName LIKE 'Day2%' THEN 'Day 2 Data'
        WHEN ClientName LIKE 'Day3%' THEN 'Day 3 Data'
        WHEN ClientName LIKE 'Incremental%' THEN 'Incremental Data'
        ELSE 'Other Data'
    END AS DataType,
    COUNT(*) AS RecordCount,
    FORMAT(COUNT(*), 'N0') AS FormattedCount
FROM dbo.Reporting_Client
GROUP BY CASE 
    WHEN ClientName LIKE 'Day1%' THEN 'Day 1 Data'
    WHEN ClientName LIKE 'Day2%' THEN 'Day 2 Data'
    WHEN ClientName LIKE 'Day3%' THEN 'Day 3 Data'
    WHEN ClientName LIKE 'Incremental%' THEN 'Incremental Data'
    ELSE 'Other Data'
END
ORDER BY DataType;

PRINT 'Ready for incremental loading tests!';