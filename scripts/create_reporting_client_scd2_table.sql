-- Create SCD2 (Slowly Changing Dimension Type 2) table for client dimension data
-- This table tracks historical changes to client information over time

USE ReportingDB;

-- Drop table if exists
DROP TABLE IF EXISTS dbo.Reporting_Client_SCD2;

-- Create SCD2 dimension table for client data
CREATE TABLE dbo.Reporting_Client_SCD2 (
    -- SCD2 Framework Columns
    [Key] BIGINT IDENTITY(1,1) PRIMARY KEY,  -- Surrogate key (unique identifier)
    ClientBusinessKey VARCHAR(50) NOT NULL,   -- Natural business key (e.g., ClientCode)
    EffectiveFromDate DATETIME2 NOT NULL,     -- When this version became active
    EffectiveToDate DATETIME2 NULL,           -- When this version expired (NULL = current)
    IsLatest BIT NOT NULL DEFAULT 1,          -- Flag indicating current/latest version
    
    -- Incremental Loading Support
    SystemCalendarID INT NOT NULL,            -- YYYYMMDD format for incremental loading
    LoadDateTime DATETIME2 DEFAULT GETUTCDATE(), -- When this record was loaded
    
    -- Client Dimension Attributes (slowly changing)
    ClientID INT NOT NULL,
    ClientName VARCHAR(255),
    CompanyName VARCHAR(255),
    Industry VARCHAR(100),
    Sector VARCHAR(100),
    BusinessType VARCHAR(50),
    
    -- Contact Information (slowly changing)
    ContactName VARCHAR(255),
    EmailAddress VARCHAR(255),
    PhoneNumber VARCHAR(50),
    Address1 VARCHAR(255),
    Address2 VARCHAR(255),
    City VARCHAR(100),
    StateProvince VARCHAR(100),
    PostalCode VARCHAR(20),
    CountryCode CHAR(2),
    
    -- Business Attributes (slowly changing)
    ClientTypeID INT,
    RegionCode CHAR(3),
    TerritoryCode VARCHAR(50),
    SegmentCode VARCHAR(50),
    PriorityLevel VARCHAR(20),
    
    -- Status and Classification (slowly changing)
    StatusCode VARCHAR(20),
    CategoryCode VARCHAR(50),
    SubCategoryCode VARCHAR(50),
    ClassificationCode VARCHAR(20),
    
    -- Financial Attributes (slowly changing)
    CreditLimit MONEY,
    PaymentTerms VARCHAR(50),
    DiscountRate DECIMAL(5,4),
    TaxRate DECIMAL(5,4),
    Currency VARCHAR(3),
    
    -- Boolean Flags (slowly changing)
    IsActive BIT DEFAULT 1,
    IsVip BIT DEFAULT 0,
    IsPremium BIT DEFAULT 0,
    IsVerified BIT DEFAULT 0,
    AcceptsMarketing BIT DEFAULT 1,
    RequiresApproval BIT DEFAULT 0,
    
    -- Audit Information
    CreatedBy VARCHAR(100) DEFAULT 'ETL_PROCESS',
    ModifiedBy VARCHAR(100) DEFAULT 'ETL_PROCESS',
    SourceSystem VARCHAR(50) DEFAULT 'StackOverflow',
    
    -- Additional SCD2 Metadata
    ChangeType VARCHAR(20),  -- INSERT, UPDATE, DELETE
    ChangeReason VARCHAR(255), -- Why this version was created
    BatchID UNIQUEIDENTIFIER DEFAULT NEWID()
);

-- Create indexes for SCD2 performance
SET QUOTED_IDENTIFIER ON;

CREATE INDEX IX_Reporting_Client_SCD2_BusinessKey ON dbo.Reporting_Client_SCD2(ClientBusinessKey);
CREATE INDEX IX_Reporting_Client_SCD2_EffectiveDates ON dbo.Reporting_Client_SCD2(EffectiveFromDate, EffectiveToDate);
CREATE INDEX IX_Reporting_Client_SCD2_SystemCalendarID ON dbo.Reporting_Client_SCD2(SystemCalendarID);
CREATE INDEX IX_Reporting_Client_SCD2_ClientID ON dbo.Reporting_Client_SCD2(ClientID);

-- Create composite index for SCD2 lookups
CREATE INDEX IX_Reporting_Client_SCD2_Lookup ON dbo.Reporting_Client_SCD2(ClientBusinessKey, EffectiveFromDate, EffectiveToDate);

-- Create filtered index for current records
CREATE INDEX IX_Reporting_Client_SCD2_IsLatest ON dbo.Reporting_Client_SCD2(IsLatest, ClientBusinessKey) WHERE IsLatest = 1;

-- Display table information
SELECT 
    'Reporting_Client_SCD2 table created successfully' AS Status,
    COUNT(*) AS ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Reporting_Client_SCD2' AND TABLE_SCHEMA = 'dbo';

-- Show column breakdown by data type
SELECT 
    DATA_TYPE,
    COUNT(*) AS ColumnCount,
    STRING_AGG(COLUMN_NAME, ', ') AS SampleColumns
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Reporting_Client_SCD2' AND TABLE_SCHEMA = 'dbo'
GROUP BY DATA_TYPE
ORDER BY COUNT(*) DESC;

PRINT 'Reporting_Client_SCD2 table structure:'
PRINT '- SCD2 Framework: Key, ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest'
PRINT '- Incremental Loading: SystemCalendarID (YYYYMMDD format)'
PRINT '- Slowly Changing Attributes: Client details, contact info, business attributes'
PRINT '- Audit Trail: CreatedBy, ModifiedBy, ChangeType, ChangeReason'
PRINT '- Optimized indexes for SCD2 operations and incremental loading'