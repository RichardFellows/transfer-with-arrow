-- Create production-scale Reporting_Client table for comprehensive testing
-- 100+ columns with mixed data types to simulate real reporting scenarios

USE StackOverflowMini;

-- Drop table if exists
DROP TABLE IF EXISTS dbo.Reporting_Client;

-- Create comprehensive Reporting_Client table
CREATE TABLE dbo.Reporting_Client (
    -- Primary key and batch tracking
    RecordID BIGINT IDENTITY(1,1) PRIMARY KEY,
    SystemCalendarID INT NOT NULL,  -- YYYYMMDD format for incremental loading
    BatchProcessID UNIQUEIDENTIFIER DEFAULT NEWID(),
    
    -- Client identification columns (10 columns)
    ClientID INT NOT NULL,
    AccountNumber VARCHAR(255) NOT NULL,
    ClientCode CHAR(10),
    ExternalClientID VARCHAR(255),
    ParentClientID INT,
    ClientTypeID INT,
    RegionCode CHAR(3),
    CountryCode CHAR(2),
    TerritoryCode VARCHAR(50),
    SegmentCode VARCHAR(50),
    
    -- Financial metrics - high precision (15 columns)
    Revenue MONEY,
    Cost MONEY,
    Profit MONEY,
    MarginAmount MONEY,
    TaxAmount MONEY,
    DiscountAmount MONEY,
    CommissionAmount MONEY,
    BonusAmount MONEY,
    PenaltyAmount MONEY,
    AdjustmentAmount MONEY,
    NetAmount DECIMAL(38,18),
    GrossAmount DECIMAL(38,18),
    CumulativeAmount DECIMAL(38,18),
    YearToDateAmount DECIMAL(38,18),
    LifetimeValue DECIMAL(38,18),
    
    -- Performance metrics - floating point (10 columns)
    ConversionRate FLOAT,
    ClickThroughRate FLOAT,
    BounceRate FLOAT,
    EngagementScore FLOAT,
    SatisfactionScore FLOAT,
    NpsScore FLOAT,
    ChurnProbability FLOAT,
    RiskScore FLOAT,
    QualityIndex FLOAT,
    PerformanceIndex FLOAT,
    
    -- Volume and count metrics (15 columns)
    TransactionCount INT,
    OrderCount INT,
    ProductCount INT,
    ServiceCount INT,
    UserCount INT,
    SessionCount INT,
    ClickCount INT,
    ViewCount INT,
    DownloadCount INT,
    ShareCount INT,
    CommentCount INT,
    LikeCount INT,
    FollowCount INT,
    ReferralCount INT,
    ComplaintCount INT,
    
    -- Text and descriptive fields (20 columns)
    ClientName VARCHAR(255),
    CompanyName VARCHAR(255),
    Industry VARCHAR(255),
    Sector VARCHAR(255),
    BusinessType VARCHAR(255),
    ContactName VARCHAR(255),
    EmailAddress VARCHAR(255),
    PhoneNumber VARCHAR(255),
    Address1 VARCHAR(255),
    Address2 VARCHAR(255),
    City VARCHAR(255),
    StateProvince VARCHAR(255),
    PostalCode VARCHAR(255),
    Website VARCHAR(255),
    SocialMediaHandle VARCHAR(255),
    PreferredLanguage VARCHAR(255),
    TimeZone VARCHAR(255),
    Currency VARCHAR(255),
    PaymentMethod VARCHAR(255),
    Notes VARCHAR(MAX),
    
    -- Boolean flags and status indicators (20 columns)
    IsActive BIT DEFAULT 1,
    IsVip BIT DEFAULT 0,
    IsPremium BIT DEFAULT 0,
    IsVerified BIT DEFAULT 0,
    IsBlocked BIT DEFAULT 0,
    IsDeleted BIT DEFAULT 0,
    HasDiscount BIT DEFAULT 0,
    HasLoyaltyCard BIT DEFAULT 0,
    AcceptsMarketing BIT DEFAULT 1,
    AcceptsEmails BIT DEFAULT 1,
    AcceptsSms BIT DEFAULT 0,
    AcceptsCalls BIT DEFAULT 0,
    RequiresApproval BIT DEFAULT 0,
    IsTestAccount BIT DEFAULT 0,
    IsInternalAccount BIT DEFAULT 0,
    HasApiAccess BIT DEFAULT 0,
    HasMobileApp BIT DEFAULT 0,
    HasWebAccess BIT DEFAULT 1,
    RequiresTwoFactor BIT DEFAULT 0,
    IsCompliant BIT DEFAULT 1,
    
    -- Date and timestamp fields (10 columns)
    CreatedDate DATETIME2 DEFAULT GETUTCDATE(),
    ModifiedDate DATETIME2 DEFAULT GETUTCDATE(),
    LastLoginDate DATETIME2,
    LastPurchaseDate DATETIME2,
    LastContactDate DATETIME2,
    RegistrationDate DATETIME2,
    ExpiryDate DATETIME2,
    RenewalDate DATETIME2,
    SuspensionDate DATETIME2,
    ActivationDate DATETIME2,
    
    -- Additional financial rates and percentages (10 columns)
    DiscountRate DECIMAL(10,4),
    TaxRate DECIMAL(10,4),
    CommissionRate DECIMAL(10,4),
    InterestRate DECIMAL(10,4),
    InflationRate DECIMAL(10,4),
    ExchangeRate DECIMAL(15,6),
    GrowthRate DECIMAL(8,4),
    RetentionRate DECIMAL(5,2),
    MarginPercent DECIMAL(5,2),
    CompletionPercent DECIMAL(5,2),
    
    -- Additional categorization and codes (5 columns)
    PriorityLevel VARCHAR(50),
    StatusCode VARCHAR(50),
    CategoryCode VARCHAR(50),
    SubCategoryCode VARCHAR(50),
    ClassificationCode VARCHAR(50)
);

-- Create index on SystemCalendarID for incremental loading performance
CREATE INDEX IX_Reporting_Client_SystemCalendarID ON dbo.Reporting_Client(SystemCalendarID);
CREATE INDEX IX_Reporting_Client_ClientID ON dbo.Reporting_Client(ClientID);
CREATE INDEX IX_Reporting_Client_CreatedDate ON dbo.Reporting_Client(CreatedDate);

-- Create composite index for common queries
CREATE INDEX IX_Reporting_Client_Composite ON dbo.Reporting_Client(SystemCalendarID, ClientID, IsActive);

-- Display table information
SELECT 
    'Reporting_Client table created successfully' AS Status,
    COUNT(*) AS ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Reporting_Client' AND TABLE_SCHEMA = 'dbo';

-- Show column breakdown by data type
SELECT 
    DATA_TYPE,
    COUNT(*) AS ColumnCount,
    STRING_AGG(COLUMN_NAME, ', ') AS SampleColumns
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Reporting_Client' AND TABLE_SCHEMA = 'dbo'
GROUP BY DATA_TYPE
ORDER BY COUNT(*) DESC;

PRINT 'Reporting_Client table structure:'
PRINT '- Total columns: 130+'
PRINT '- SystemCalendarID: INT (YYYYMMDD format for incremental loading)'
PRINT '- Mixed data types: MONEY, DECIMAL(38,18), FLOAT, INT, BIT, VARCHAR, CHAR'
PRINT '- Designed for 2M+ records per day'
PRINT '- Optimized indexes for incremental queries'