-- Unified Reporting_Client data population script
-- Intelligently adds 3 days of data on first run, then adds next day's data on subsequent runs
-- Eliminates duplication between populate_reporting_client_data.sql and add_next_day_data.sql

USE StackOverflowMini;

SET NOCOUNT ON;

-- Configuration parameters
DECLARE @BatchSize INT = 10000;
DECLARE @RecordsPerDay INT = 2000000;  -- 2M records per day
DECLARE @DaysToAdd INT;
DECLARE @StartingCalendarID INT;
DECLARE @CurrentDay INT = 1;
DECLARE @RecordsInserted INT = 0;
DECLARE @BatchesPerDay INT;
DECLARE @CurrentBatch INT;
DECLARE @IsInitialLoad BIT = 0;

-- Calculate batches needed per day
SET @BatchesPerDay = @RecordsPerDay / @BatchSize;

PRINT 'Unified Reporting_Client Data Population Script';
PRINT '===============================================';

-- Check current state and determine what to do
IF NOT EXISTS (SELECT 1 FROM dbo.Reporting_Client)
BEGIN
    -- Table is empty - initial load (3 days)
    SET @IsInitialLoad = 1;
    SET @DaysToAdd = 3;
    SET @StartingCalendarID = CAST(FORMAT(DATEADD(DAY, -2, GETDATE()), 'yyyyMMdd') AS INT); -- Start 2 days ago
    PRINT 'INITIAL LOAD MODE: Table is empty, loading 3 days of historical data';
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
            @CurrentCalendarID,
            NEWID(),
            
            -- Generate ClientID with day-specific ranges to ensure uniqueness
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
                
            -- Financial amounts with day-based scaling for trend simulation
            CAST((ABS(CHECKSUM(NEWID())) % 10000000 * (1.0 + @CurrentDay * 0.05)) / 100.0 AS MONEY),  -- Revenue grows 5% per day
            CAST((ABS(CHECKSUM(NEWID())) % 8000000 * (1.0 + @CurrentDay * 0.03)) / 100.0 AS MONEY),   -- Cost grows 3% per day
            CAST((ABS(CHECKSUM(NEWID())) % 2000000 * (1.0 + @CurrentDay * 0.08)) / 100.0 AS MONEY),   -- Profit grows 8% per day
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
            
            -- Volume counts with day-based scaling
            ABS(CHECKSUM(NEWID())) % (1000 * @CurrentDay),      -- TransactionCount
            ABS(CHECKSUM(NEWID())) % (500 * @CurrentDay),       -- OrderCount
            ABS(CHECKSUM(NEWID())) % 100,       -- ProductCount
            ABS(CHECKSUM(NEWID())) % 50,        -- ServiceCount
            ABS(CHECKSUM(NEWID())) % (10000 + @CurrentDay * 1000), -- UserCount
            ABS(CHECKSUM(NEWID())) % (50000 + @CurrentDay * 5000), -- SessionCount
            ABS(CHECKSUM(NEWID())) % (100000 + @CurrentDay * 10000), -- ClickCount
            ABS(CHECKSUM(NEWID())) % (1000000 + @CurrentDay * 100000), -- ViewCount
            ABS(CHECKSUM(NEWID())) % 10000,     -- DownloadCount
            ABS(CHECKSUM(NEWID())) % 5000,      -- ShareCount
            ABS(CHECKSUM(NEWID())) % 1000,      -- CommentCount
            ABS(CHECKSUM(NEWID())) % 10000,     -- LikeCount
            ABS(CHECKSUM(NEWID())) % 2000,      -- FollowCount
            ABS(CHECKSUM(NEWID())) % 500,       -- ReferralCount
            ABS(CHECKSUM(NEWID())) % 100,       -- ComplaintCount
            
            -- Text fields with day-specific prefixes for easier identification
            CASE @CurrentDay 
                WHEN 1 THEN 'Day1 Client ' WHEN 2 THEN 'Day2 Client ' WHEN 3 THEN 'Day3 Client '
                ELSE 'Incremental Client ' END + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
            CASE @CurrentDay 
                WHEN 1 THEN 'Day1 Business ' WHEN 2 THEN 'Day2 Business ' WHEN 3 THEN 'Day3 Business '
                ELSE 'Next Business ' END + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
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
            
            -- Timestamps (with day-specific logic)
            CASE 
                WHEN @IsInitialLoad = 1 THEN DATEADD(DAY, -(@DaysToAdd - @CurrentDay + 1), DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 30), GETUTCDATE()))
                ELSE GETUTCDATE() 
            END,  -- CreatedDate
            CASE 
                WHEN @IsInitialLoad = 1 THEN DATEADD(DAY, -(ABS(CHECKSUM(NEWID())) % 7), GETUTCDATE())
                ELSE GETUTCDATE() 
            END,  -- ModifiedDate
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
            'CAT' + RIGHT('000' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR), 3),
            'SUB' + RIGHT('000' + CAST(ABS(CHECKSUM(NEWID())) % 999 AS VARCHAR), 3), 
            'CLS' + RIGHT('00' + CAST(ABS(CHECKSUM(NEWID())) % 99 AS VARCHAR), 2)
            
        FROM master.dbo.spt_values v1
        CROSS JOIN master.dbo.spt_values v2
        WHERE v1.type = 'P' AND v2.type = 'P'
        AND v1.number BETWEEN 1 AND @BatchSize;
        
        SET @RecordsInserted = @RecordsInserted + @@ROWCOUNT;
        
        -- Progress update every 100 batches for initial load, 50 for incremental
        DECLARE @ProgressInterval INT = CASE WHEN @IsInitialLoad = 1 THEN 100 ELSE 50 END;
        IF @CurrentBatch % @ProgressInterval = 0
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