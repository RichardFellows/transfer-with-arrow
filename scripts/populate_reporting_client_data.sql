-- Populate Reporting_Client table with 3 days of production-scale data
-- Each day = ~2M records, 3 days = ~6M total records

USE StackOverflowMini;

-- Enable performance optimizations for bulk insert
SET NOCOUNT ON;

DECLARE @BatchSize INT = 10000;  -- Insert in batches for performance
DECLARE @TotalRecordsPerDay INT = 2000000;  -- 2M records per day
DECLARE @DaysToLoad INT = 3;
DECLARE @CurrentDay INT = 1;
DECLARE @SystemCalendarID INT;
DECLARE @RecordsInserted INT = 0;
DECLARE @BatchesPerDay INT;
DECLARE @CurrentBatch INT;

-- Calculate batches needed per day
SET @BatchesPerDay = @TotalRecordsPerDay / @BatchSize;

PRINT 'Starting data population for Reporting_Client table';
PRINT 'Configuration:';
PRINT '  - Records per day: ' + CAST(@TotalRecordsPerDay AS VARCHAR(20));
PRINT '  - Days to load: ' + CAST(@DaysToLoad AS VARCHAR(10));
PRINT '  - Batch size: ' + CAST(@BatchSize AS VARCHAR(20));
PRINT '  - Batches per day: ' + CAST(@BatchesPerDay AS VARCHAR(20));
PRINT '  - Total records: ' + CAST(@TotalRecordsPerDay * @DaysToLoad AS VARCHAR(20));

-- Generate SystemCalendarID values for 3 consecutive days
-- Starting from yesterday to simulate recent data
DECLARE @StartDate DATE = DATEADD(DAY, -3, GETDATE());

WHILE @CurrentDay <= @DaysToLoad
BEGIN
    -- Calculate SystemCalendarID in YYYYMMDD format
    SET @SystemCalendarID = CAST(FORMAT(DATEADD(DAY, @CurrentDay - 1, @StartDate), 'yyyyMMdd') AS INT);
    
    PRINT '';
    PRINT 'Loading Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' - SystemCalendarID: ' + CAST(@SystemCalendarID AS VARCHAR(10));
    PRINT 'Target records: ' + CAST(@TotalRecordsPerDay AS VARCHAR(20));
    
    SET @CurrentBatch = 1;
    
    -- Insert data in batches for this day
    WHILE @CurrentBatch <= @BatchesPerDay
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
            @SystemCalendarID,
            NEWID(),
            -- Generate realistic ClientID distribution
            ABS(CHECKSUM(NEWID())) % 1000000 + 1,
            'ACC' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6),
            'CLI' + RIGHT('0000000' + CAST(ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS VARCHAR), 7),
            'EXT' + CAST(ABS(CHECKSUM(NEWID())) % 9999999 AS VARCHAR),
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN NULL ELSE ABS(CHECKSUM(NEWID())) % 100000 END,
            ABS(CHECKSUM(NEWID())) % 50 + 1,
            CASE ABS(CHECKSUM(NEWID())) % 5 
                WHEN 0 THEN 'NAM' WHEN 1 THEN 'EUR' WHEN 2 THEN 'APJ' 
                WHEN 3 THEN 'LAM' ELSE 'MEA' END,
            CASE ABS(CHECKSUM(NEWID())) % 10
                WHEN 0 THEN 'US' WHEN 1 THEN 'GB' WHEN 2 THEN 'DE' WHEN 3 THEN 'FR'
                WHEN 4 THEN 'CA' WHEN 5 THEN 'AU' WHEN 6 THEN 'JP' WHEN 7 THEN 'BR'
                WHEN 8 THEN 'IN' ELSE 'CN' END,
            'TERR' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            CASE ABS(CHECKSUM(NEWID())) % 5
                WHEN 0 THEN 'Enterprise' WHEN 1 THEN 'SMB' WHEN 2 THEN 'Consumer'
                WHEN 3 THEN 'Government' ELSE 'Education' END,
                
            -- Financial amounts with realistic distributions
            CAST((ABS(CHECKSUM(NEWID())) % 10000000) / 100.0 AS MONEY),  -- Revenue
            CAST((ABS(CHECKSUM(NEWID())) % 8000000) / 100.0 AS MONEY),   -- Cost  
            CAST((ABS(CHECKSUM(NEWID())) % 2000000) / 100.0 AS MONEY),   -- Profit
            CAST((ABS(CHECKSUM(NEWID())) % 500000) / 100.0 AS MONEY),    -- Margin
            CAST((ABS(CHECKSUM(NEWID())) % 1000000) / 100.0 AS MONEY),   -- Tax
            CAST((ABS(CHECKSUM(NEWID())) % 200000) / 100.0 AS MONEY),    -- Discount
            CAST((ABS(CHECKSUM(NEWID())) % 300000) / 100.0 AS MONEY),    -- Commission
            CAST((ABS(CHECKSUM(NEWID())) % 100000) / 100.0 AS MONEY),    -- Bonus
            CAST((ABS(CHECKSUM(NEWID())) % 50000) / 100.0 AS MONEY),     -- Penalty
            CAST((ABS(CHECKSUM(NEWID())) % 25000) / 100.0 AS MONEY),     -- Adjustment
            
            -- High precision decimals
            CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
            CAST((ABS(CHECKSUM(NEWID())) % 999999999) + (ABS(CHECKSUM(NEWID())) % 1000000) / 1000000.0 AS DECIMAL(38,18)),
            
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
            ABS(CHECKSUM(NEWID())) % 1000,      -- TransactionCount
            ABS(CHECKSUM(NEWID())) % 500,       -- OrderCount
            ABS(CHECKSUM(NEWID())) % 100,       -- ProductCount
            ABS(CHECKSUM(NEWID())) % 50,        -- ServiceCount
            ABS(CHECKSUM(NEWID())) % 10000,     -- UserCount
            ABS(CHECKSUM(NEWID())) % 50000,     -- SessionCount
            ABS(CHECKSUM(NEWID())) % 100000,    -- ClickCount
            ABS(CHECKSUM(NEWID())) % 1000000,   -- ViewCount
            ABS(CHECKSUM(NEWID())) % 10000,     -- DownloadCount
            ABS(CHECKSUM(NEWID())) % 5000,      -- ShareCount
            ABS(CHECKSUM(NEWID())) % 1000,      -- CommentCount
            ABS(CHECKSUM(NEWID())) % 10000,     -- LikeCount
            ABS(CHECKSUM(NEWID())) % 2000,      -- FollowCount
            ABS(CHECKSUM(NEWID())) % 500,       -- ReferralCount
            ABS(CHECKSUM(NEWID())) % 100,       -- ComplaintCount
            
            -- Text fields with realistic data
            'Client Company ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
            'Business Corp ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
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
            'Contact Person ' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR),
            'user' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR) + '@company' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + '.com',
            '+1-' + CAST(ABS(CHECKSUM(NEWID())) % 900 + 100 AS VARCHAR) + '-' + CAST(ABS(CHECKSUM(NEWID())) % 900 + 100 AS VARCHAR) + '-' + CAST(ABS(CHECKSUM(NEWID())) % 9000 + 1000 AS VARCHAR),
            CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + ' Main Street',
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN 'Suite ' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR) ELSE NULL END,
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
            'https://www.company' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR) + '.com',
            '@company' + CAST(ABS(CHECKSUM(NEWID())) % 9999 AS VARCHAR),
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
            
            -- Boolean flags (realistic distributions)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 85 THEN 1 ELSE 0 END,  -- IsActive (85%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 15 THEN 1 ELSE 0 END,  -- IsVip (15%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 25 THEN 1 ELSE 0 END,  -- IsPremium (25%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 70 THEN 1 ELSE 0 END,  -- IsVerified (70%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 5 THEN 1 ELSE 0 END,   -- IsBlocked (5%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 3 THEN 1 ELSE 0 END,   -- IsDeleted (3%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 40 THEN 1 ELSE 0 END,  -- HasDiscount (40%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 60 THEN 1 ELSE 0 END,  -- HasLoyaltyCard (60%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 75 THEN 1 ELSE 0 END,  -- AcceptsMarketing (75%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 80 THEN 1 ELSE 0 END,  -- AcceptsEmails (80%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 30 THEN 1 ELSE 0 END,  -- AcceptsSms (30%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 20 THEN 1 ELSE 0 END,  -- AcceptsCalls (20%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 10 THEN 1 ELSE 0 END,  -- RequiresApproval (10%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 2 THEN 1 ELSE 0 END,   -- IsTestAccount (2%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 1 THEN 1 ELSE 0 END,   -- IsInternalAccount (1%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 35 THEN 1 ELSE 0 END,  -- HasApiAccess (35%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 65 THEN 1 ELSE 0 END,  -- HasMobileApp (65%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 90 THEN 1 ELSE 0 END,  -- HasWebAccess (90%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 45 THEN 1 ELSE 0 END,  -- RequiresTwoFactor (45%)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 95 THEN 1 ELSE 0 END,  -- IsCompliant (95%)
            
            -- Timestamps (with realistic date ranges)
            DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 1095), GETUTCDATE()),   -- CreatedDate (last 3 years)
            DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 30), GETUTCDATE()),     -- ModifiedDate (last 30 days)
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 8 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 30), GETUTCDATE()) ELSE NULL END,  -- LastLoginDate
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 6 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 90), GETUTCDATE()) ELSE NULL END,  -- LastPurchaseDate
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 7 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 60), GETUTCDATE()) ELSE NULL END,  -- LastContactDate
            DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 1095), GETUTCDATE()),   -- RegistrationDate
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 3 THEN DATEADD(DAY, (ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()) ELSE NULL END,  -- ExpiryDate
            CASE WHEN ABS(CHECKSUM(NEWID())) % 10 < 4 THEN DATEADD(DAY, (ABS(CHECKSUM(NEWID())) % 365), GETUTCDATE()) ELSE NULL END,  -- RenewalDate
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 5 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 180), GETUTCDATE()) ELSE NULL END, -- SuspensionDate
            DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 1095), GETUTCDATE()),   -- ActivationDate
            
            -- Rates and percentages
            CAST((ABS(CHECKSUM(NEWID())) % 5000) / 10000.0 AS DECIMAL(10,4)),  -- DiscountRate (0-50%)
            CAST((ABS(CHECKSUM(NEWID())) % 2500) / 10000.0 AS DECIMAL(10,4)),  -- TaxRate (0-25%)
            CAST((ABS(CHECKSUM(NEWID())) % 1500) / 10000.0 AS DECIMAL(10,4)),  -- CommissionRate (0-15%)
            CAST((ABS(CHECKSUM(NEWID())) % 1000) / 10000.0 AS DECIMAL(10,4)),  -- InterestRate (0-10%)
            CAST((ABS(CHECKSUM(NEWID())) % 500) / 10000.0 AS DECIMAL(10,4)),   -- InflationRate (0-5%)
            CAST(0.5 + (ABS(CHECKSUM(NEWID())) % 200000) / 100000.0 AS DECIMAL(15,6)), -- ExchangeRate
            CAST((ABS(CHECKSUM(NEWID())) % 5000 - 2500) / 10000.0 AS DECIMAL(8,4)),    -- GrowthRate (-25% to +25%)
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   -- RetentionRate (0-100%)
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   -- MarginPercent (0-100%)
            CAST((ABS(CHECKSUM(NEWID())) % 10000) / 100.0 AS DECIMAL(5,2)),   -- CompletionPercent (0-100%)
            
            -- Additional categorization
            CASE ABS(CHECKSUM(NEWID())) % 5
                WHEN 0 THEN 'Critical' WHEN 1 THEN 'High' WHEN 2 THEN 'Medium'
                WHEN 3 THEN 'Low' ELSE 'Info' END,
            CASE ABS(CHECKSUM(NEWID())) % 6
                WHEN 0 THEN 'Active' WHEN 1 THEN 'Pending' WHEN 2 THEN 'Suspended'
                WHEN 3 THEN 'Closed' WHEN 4 THEN 'Review' ELSE 'Expired' END,
            'CAT' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            'SUB' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR),
            'CLASS' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR)
            
        FROM master.dbo.spt_values v1
        CROSS JOIN master.dbo.spt_values v2
        WHERE v1.type = 'P' AND v2.type = 'P'
        AND v1.number BETWEEN 1 AND @BatchSize;
        
        SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
        
        -- Progress update every 100 batches
        IF @CurrentBatch % 100 = 0
        BEGIN
            PRINT '  Batch ' + CAST(@CurrentBatch AS VARCHAR(10)) + '/' + CAST(@BatchesPerDay AS VARCHAR(10)) + 
                  ' completed. Records so far today: ' + CAST(@CurrentBatch * @BatchSize AS VARCHAR(20));
        END
        
        SET @CurrentBatch = @CurrentBatch + 1;
    END
    
    PRINT 'Day ' + CAST(@CurrentDay AS VARCHAR(5)) + ' completed. Records inserted: ' + CAST(@RecordsInserted AS VARCHAR(20));
    SET @CurrentDay = @CurrentDay + 1;
    SET @RecordsInserted = 0;
END

-- Final statistics
PRINT '';
PRINT 'Data population completed successfully!';
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
    'Total Records' AS Metric,
    COUNT(*) AS Value,
    FORMAT(COUNT(*), 'N0') AS FormattedValue
FROM dbo.Reporting_Client;

PRINT 'Ready for incremental loading tests!';