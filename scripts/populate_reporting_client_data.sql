-- Optimized script with RAISERROR for immediate, unbuffered feedback

USE StackOverflowMini;
GO

SET NOCOUNT ON;
GO

PRINT '--- Script Execution Started at ' + CONVERT(VARCHAR, GETDATE(), 120) + ' ---';

-- Configuration
DECLARE @BatchSize INT = 1000;
DECLARE @TotalRecordsPerDay INT = 20000;
DECLARE @DaysToLoad INT = 3;

-- Calculated variables
DECLARE @BatchesPerDay INT = @TotalRecordsPerDay / @BatchSize;
DECLARE @TotalRecordsToLoad INT = @TotalRecordsPerDay * @TotalRecordsToLoad;

-- Display initial configuration (PRINT is fine here as this batch is small)
PRINT '
Configuration:
  - Records per day:   ' + FORMAT(@TotalRecordsPerDay, 'N0') + '
  - Days to load:       ' + CAST(@DaysToLoad AS VARCHAR(10)) + '
  - Batch size:         ' + FORMAT(@BatchSize, 'N0') + '
  - Batches per day:    ' + FORMAT(@BatchesPerDay, 'N0') + '
  - Total records:      ' + FORMAT(@TotalRecordsToLoad, 'N0');
PRINT '----------------------------------------------------------';
GO

DECLARE @CurrentDay INT = 1;
DECLARE @StartDate DATE = DATEADD(DAY, -@DaysToLoad, GETDATE());

-- Loop through each day to load data
WHILE @CurrentDay <= @DaysToLoad
BEGIN
    DECLARE @SystemCalendarID INT = CAST(FORMAT(DATEADD(DAY, @CurrentDay - 1, @StartDate), 'yyyyMMdd') AS INT);
    DECLARE @DayStartTime DATETIME2 = GETUTCDATE();
    DECLARE @Msg NVARCHAR(500); -- Variable for our message

    SET @Msg = FORMATMESSAGE('
--- Loading Day %d of %d ---
  - SystemCalendarID: %d
  - Day processing started at: %s', 
  @CurrentDay, @DaysToLoad, @SystemCalendarID, CONVERT(VARCHAR, @DayStartTime, 120));
    RAISERROR(@Msg, 10, 1) WITH NOWAIT;
    
    DECLARE @CurrentBatch INT = 1;

    -- Loop through batches for the current day
    WHILE @CurrentBatch <= @BatchesPerDay
    BEGIN
        -- The main INSERT statement remains the same...
        INSERT INTO dbo.Reporting_Client WITH (TABLOCK) (
            -- (Column list is omitted for brevity but is identical to the previous script)
            SystemCalendarID, ClientID, AccountNumber, ClientCode, ExternalClientID, ParentClientID, 
            ClientTypeID, RegionCode, CountryCode, TerritoryCode, SegmentCode, Revenue, Cost, Profit, 
            MarginAmount, TaxAmount, DiscountAmount, CommissionAmount, BonusAmount, PenaltyAmount, 
            AdjustmentAmount, NetAmount, GrossAmount, CumulativeAmount, YearToDateAmount, LifetimeValue, 
            ConversionRate, ClickThroughRate, BounceRate, EngagementScore, SatisfactionScore, NpsScore, 
            ChurnProbability, RiskScore, QualityIndex, PerformanceIndex, TransactionCount, OrderCount, 
            ProductCount, ServiceCount, UserCount, SessionCount, ClickCount, ViewCount, DownloadCount, 
            ShareCount, CommentCount, LikeCount, FollowCount, ReferralCount, ComplaintCount, 
            ClientName, CompanyName, Industry, Sector, BusinessType, ContactName, EmailAddress, 
            PhoneNumber, Address1, Address2, City, StateProvince, PostalCode, Website, SocialMediaHandle, 
            PreferredLanguage, TimeZone, Currency, PaymentMethod, Notes, IsActive, IsVip, IsPremium, 
            IsVerified, IsBlocked, IsDeleted, HasDiscount, HasLoyaltyCard, AcceptsMarketing, AcceptsEmails, 
            AcceptsSms, AcceptsCalls, RequiresApproval, IsTestAccount, IsInternalAccount, HasApiAccess, 
            HasMobileApp, HasWebAccess, RequiresTwoFactor, IsCompliant, CreatedDate, ModifiedDate, 
            LastLoginDate, LastPurchaseDate, LastContactDate, RegistrationDate, ExpiryDate, RenewalDate, 
            SuspensionDate, ActivationDate, DiscountRate, TaxRate, CommissionRate, InterestRate, 
            InflationRate, ExchangeRate, GrowthRate, RetentionRate, MarginPercent, CompletionPercent, 
            PriorityLevel, StatusCode, CategoryCode, SubCategoryCode, ClassificationCode
        )
        SELECT
            @SystemCalendarID,
            -- (The SELECT statement logic is also omitted for brevity)
            ABS(CHECKSUM(NEWID())) % 1000000 + 1, 'ACC' + RIGHT('000000' + CAST(ABS(CHECKSUM(NEWID())) % 999999 AS VARCHAR), 6),
            'CLI' + RIGHT('0000000' + CAST(v.number AS VARCHAR), 7), 'EXT' + CAST(ABS(CHECKSUM(NEWID())) % 9999999 AS VARCHAR),
            CASE WHEN v.number % 10 < 3 THEN NULL ELSE ABS(CHECKSUM(NEWID())) % 100000 END, v.number % 50 + 1,
            CASE v.number % 5 WHEN 0 THEN 'NAM' WHEN 1 THEN 'EUR' WHEN 2 THEN 'APJ' WHEN 3 THEN 'LAM' ELSE 'MEA' END,
            CASE v.number % 10 WHEN 0 THEN 'US' WHEN 1 THEN 'GB' WHEN 2 THEN 'DE' WHEN 3 THEN 'FR' WHEN 4 THEN 'CA' WHEN 5 THEN 'AU' WHEN 6 THEN 'JP' WHEN 7 THEN 'BR' WHEN 8 THEN 'IN' ELSE 'CN' END,
            'TERR' + CAST(v.number % 999 AS VARCHAR), CASE v.number % 5 WHEN 0 THEN 'Enterprise' WHEN 1 THEN 'SMB' WHEN 2 THEN 'Consumer' WHEN 3 THEN 'Government' ELSE 'Education' END,
            CAST((v.number * 1.23) AS MONEY), CAST((v.number * 0.89) AS MONEY), CAST((v.number * 0.34) AS MONEY),
            CAST((v.number % 5000) / 100.0 AS MONEY), CAST((v.number % 1000) / 100.0 AS MONEY), CAST((v.number % 200) / 100.0 AS MONEY), CAST((v.number % 300) / 100.0 AS MONEY), CAST((v.number % 100) / 100.0 AS MONEY), CAST((v.number % 50) / 100.0 AS MONEY), CAST((v.number % 25) / 100.0 AS MONEY),
            CAST(RAND(CHECKSUM(NEWID())) * 10000000 AS DECIMAL(38,18)), CAST(RAND(CHECKSUM(NEWID())) * 12000000 AS DECIMAL(38,18)), CAST(RAND(CHECKSUM(NEWID())) * 50000000 AS DECIMAL(38,18)), CAST(RAND(CHECKSUM(NEWID())) * 25000000 AS DECIMAL(38,18)), CAST(RAND(CHECKSUM(NEWID())) * 1000000 AS DECIMAL(38,18)),
            RAND(CHECKSUM(NEWID())), RAND(CHECKSUM(NEWID())) * 0.1, RAND(CHECKSUM(NEWID())) * 0.5, v.number % 100, v.number % 100, (v.number % 201) - 100, RAND(CHECKSUM(NEWID())), v.number % 1000, v.number % 100, v.number % 100,
            v.number % 1000, v.number % 500, v.number % 100, v.number % 50, v.number % 10000, v.number % 50000, v.number % 100000, v.number % 1000000, v.number % 10000, v.number % 5000, v.number % 1000, v.number % 10000, v.number % 2000, v.number % 500, v.number % 100,
            'Client ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR), 'Company ' + CAST(ABS(CHECKSUM(NEWID())) % 99999 AS VARCHAR),
            CASE v.number % 10 WHEN 0 THEN 'Technology' WHEN 1 THEN 'Healthcare' WHEN 2 THEN 'Finance' WHEN 3 THEN 'Manufacturing' WHEN 4 THEN 'Retail' WHEN 5 THEN 'Education' WHEN 6 THEN 'Government' WHEN 7 THEN 'Energy' WHEN 8 THEN 'Media' ELSE 'Consulting' END,
            CASE v.number % 8 WHEN 0 THEN 'Software' WHEN 1 THEN 'Hardware' WHEN 2 THEN 'Services' WHEN 3 THEN 'Products' WHEN 4 THEN 'Consulting' WHEN 5 THEN 'Support' WHEN 6 THEN 'Training' ELSE 'Research' END,
            CASE v.number % 4 WHEN 0 THEN 'B2B' WHEN 1 THEN 'B2C' WHEN 2 THEN 'B2G' ELSE 'Platform' END,
            'Contact ' + CAST(v.number AS VARCHAR), 'user' + CAST(ABS(CHECKSUM(NEWID())) AS VARCHAR) + '@example.com', '+1-555-' + FORMAT(v.number % 999, '000') + '-' + FORMAT(v.number % 9999, '0000'),
            CAST(v.number AS VARCHAR) + ' Optimus Way', CASE WHEN v.number % 10 < 3 THEN 'Suite ' + CAST(v.number % 999 AS VARCHAR) ELSE NULL END,
            CASE v.number % 5 WHEN 0 THEN 'New York' WHEN 1 THEN 'Los Angeles' WHEN 2 THEN 'Chicago' WHEN 3 THEN 'Houston' ELSE 'Phoenix' END,
            CASE v.number % 5 WHEN 0 THEN 'NY' WHEN 1 THEN 'CA' WHEN 2 THEN 'IL' WHEN 3 THEN 'TX' ELSE 'AZ' END, FORMAT(v.number % 99999, '00000'), 'https://www.company' + CAST(ABS(CHECKSUM(NEWID())) AS VARCHAR) + '.com', '@handle' + CAST(ABS(CHECKSUM(NEWID())) AS VARCHAR),
            CASE v.number % 4 WHEN 0 THEN 'English' WHEN 1 THEN 'Spanish' WHEN 2 THEN 'French' ELSE 'German' END, 'UTC' + CAST((v.number % 12) - 6 AS VARCHAR), CASE v.number % 4 WHEN 0 THEN 'USD' WHEN 1 THEN 'EUR' WHEN 2 THEN 'GBP' ELSE 'JPY' END, CASE v.number % 4 WHEN 0 THEN 'Credit Card' WHEN 1 THEN 'Bank Transfer' WHEN 2 THEN 'PayPal' ELSE 'Check' END, NULL,
            CASE WHEN v.number % 100 < 85 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 15 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 25 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 70 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 5 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 3 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 40 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 60 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 75 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 80 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 30 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 20 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 10 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 2 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 1 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 35 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 65 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 90 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 45 THEN 1 ELSE 0 END, CASE WHEN v.number % 100 < 95 THEN 1 ELSE 0 END,
            DATEADD(DAY, -(v.number % 1095), GETUTCDATE()), DATEADD(DAY, -(v.number % 30), GETUTCDATE()), DATEADD(DAY, -(v.number % 30), GETUTCDATE()), DATEADD(DAY, -(v.number % 90), GETUTCDATE()), DATEADD(DAY, -(v.number % 60), GETUTCDATE()), DATEADD(DAY, -(v.number % 1095), GETUTCDATE()), DATEADD(DAY, (v.number % 365), GETUTCDATE()), DATEADD(DAY, (v.number % 365), GETUTCDATE()), DATEADD(DAY, -(v.number % 180), GETUTCDATE()), DATEADD(DAY, -(v.number % 1095), GETUTCDATE()),
            CAST(RAND(v.number) * 0.5 AS DECIMAL(10,4)), CAST(RAND(v.number * 2) * 0.25 AS DECIMAL(10,4)), CAST(RAND(v.number * 3) * 0.15 AS DECIMAL(10,4)), CAST(RAND(v.number * 4) * 0.10 AS DECIMAL(10,4)), CAST(RAND(v.number * 5) * 0.05 AS DECIMAL(10,4)), CAST(1 + RAND(v.number) AS DECIMAL(15,6)), CAST((RAND(v.number) - 0.5) * 0.5 AS DECIMAL(8,4)), CAST(RAND(v.number) * 100 AS DECIMAL(5,2)), CAST(RAND(v.number * 2) * 100 AS DECIMAL(5,2)), CAST(RAND(v.number * 3) * 100 AS DECIMAL(5,2)),
            CASE v.number % 5 WHEN 0 THEN 'Critical' WHEN 1 THEN 'High' WHEN 2 THEN 'Medium' WHEN 3 THEN 'Low' ELSE 'Info' END, CASE v.number % 6 WHEN 0 THEN 'Active' WHEN 1 THEN 'Pending' WHEN 2 THEN 'Suspended' WHEN 3 THEN 'Closed' WHEN 4 THEN 'Review' ELSE 'Expired' END, 'CAT' + CAST(v.number % 999 AS VARCHAR), 'SUB' + CAST(v.number % 999 AS VARCHAR), 'CLASS' + CAST(v.number % 99 AS VARCHAR)
        FROM master.dbo.spt_values AS v
        WHERE v.type = 'P' AND v.number BETWEEN 1 AND @BatchSize;
        
        -- ⭐ REPLACEMENT: Use RAISERROR for immediate, unbuffered feedback
        SET @Msg = FORMATMESSAGE('> Batch %s/%s completed. (%s rows so far today)', 
                                FORMAT(@CurrentBatch, '000'), 
                                FORMAT(@BatchesPerDay, '000'), 
                                FORMAT(@CurrentBatch * @BatchSize, 'N0'));
        RAISERROR(@Msg, 10, 1) WITH NOWAIT;
        
        SET @CurrentBatch = @CurrentBatch + 1;
    END

    DECLARE @DayDuration INT = DATEDIFF(SECOND, @DayStartTime, GETUTCDATE());
    SET @Msg = FORMATMESSAGE('  - Day %d completed in %d seconds.', @CurrentDay, @DayDuration);
    RAISERROR(@Msg, 10, 1) WITH NOWAIT;
    
    SET @CurrentDay = @CurrentDay + 1;
END
GO

PRINT '
----------------------------------------------------------';
PRINT '--- Data population completed successfully! ---';
GO

-- Final validation statistics
SELECT
    SystemCalendarID,
    FORMAT(COUNT(*), 'N0') AS RecordCount,
    MIN(CreatedDate) AS EarliestRecord,
    MAX(CreatedDate) AS LatestRecord
FROM dbo.Reporting_Client
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID;
GO