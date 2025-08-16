-- Production-scale test tables for DLT testing
-- Simulates real-world scenarios with 100+ columns and complex data types

USE StackOverflowMini;
GO

-- Large table with 100+ columns and complex data types
IF OBJECT_ID('dbo.ProductionTestTable', 'U') IS NOT NULL
    DROP TABLE dbo.ProductionTestTable;
GO

CREATE TABLE dbo.ProductionTestTable (
    -- Primary key and basic identifiers
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ExternalId UNIQUEIDENTIFIER DEFAULT NEWID(),
    RecordCode VARCHAR(255) NOT NULL,
    
    -- Financial columns with high precision
    Amount1 DECIMAL(38,18),
    Amount2 DECIMAL(38,18),
    Amount3 DECIMAL(38,18),
    Amount4 DECIMAL(38,18),
    Amount5 DECIMAL(38,18),
    Amount6 DECIMAL(38,18),
    Amount7 DECIMAL(38,18),
    Amount8 DECIMAL(38,18),
    Amount9 DECIMAL(38,18),
    Amount10 DECIMAL(38,18),
    
    -- Money columns
    Price1 MONEY,
    Price2 MONEY,
    Price3 MONEY,
    Price4 MONEY,
    Price5 MONEY,
    
    -- Large text fields
    Description1 VARCHAR(MAX),
    Description2 VARCHAR(MAX),
    Description3 VARCHAR(MAX),
    Notes1 VARCHAR(MAX),
    Notes2 VARCHAR(MAX),
    Comments1 VARCHAR(MAX),
    Comments2 VARCHAR(MAX),
    
    -- Fixed-length text fields
    Code1 VARCHAR(255),
    Code2 VARCHAR(255),
    Code3 VARCHAR(255),
    Code4 VARCHAR(255),
    Code5 VARCHAR(255),
    Name1 VARCHAR(255),
    Name2 VARCHAR(255),
    Name3 VARCHAR(255),
    Name4 VARCHAR(255),
    Name5 VARCHAR(255),
    
    -- Integer columns
    Counter1 INT,
    Counter2 INT,
    Counter3 INT,
    Counter4 INT,
    Counter5 INT,
    Quantity1 INT,
    Quantity2 INT,
    Quantity3 INT,
    Quantity4 INT,
    Quantity5 INT,
    
    -- Boolean/Bit columns
    IsActive BIT DEFAULT 1,
    IsProcessed BIT DEFAULT 0,
    IsApproved BIT DEFAULT 0,
    IsDeleted BIT DEFAULT 0,
    IsPublic BIT DEFAULT 1,
    IsVisible BIT DEFAULT 1,
    IsLocked BIT DEFAULT 0,
    IsArchived BIT DEFAULT 0,
    IsComplete BIT DEFAULT 0,
    IsValid BIT DEFAULT 1,
    
    -- Date/Time columns
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    ModifiedDate DATETIME2 DEFAULT GETDATE(),
    ProcessedDate DATETIME2,
    ApprovedDate DATETIME2,
    ExpiryDate DATETIME2,
    StartDate DATETIME2,
    EndDate DATETIME2,
    
    -- Additional numeric columns
    Rate1 DECIMAL(10,4),
    Rate2 DECIMAL(10,4),
    Rate3 DECIMAL(10,4),
    Rate4 DECIMAL(10,4),
    Rate5 DECIMAL(10,4),
    Percentage1 DECIMAL(5,2),
    Percentage2 DECIMAL(5,2),
    Percentage3 DECIMAL(5,2),
    
    -- More VARCHAR columns to reach 100+
    Field01 VARCHAR(255), Field02 VARCHAR(255), Field03 VARCHAR(255), Field04 VARCHAR(255), Field05 VARCHAR(255),
    Field06 VARCHAR(255), Field07 VARCHAR(255), Field08 VARCHAR(255), Field09 VARCHAR(255), Field10 VARCHAR(255),
    Field11 VARCHAR(255), Field12 VARCHAR(255), Field13 VARCHAR(255), Field14 VARCHAR(255), Field15 VARCHAR(255),
    Field16 VARCHAR(255), Field17 VARCHAR(255), Field18 VARCHAR(255), Field19 VARCHAR(255), Field20 VARCHAR(255),
    Field21 VARCHAR(255), Field22 VARCHAR(255), Field23 VARCHAR(255), Field24 VARCHAR(255), Field25 VARCHAR(255),
    Field26 VARCHAR(255), Field27 VARCHAR(255), Field28 VARCHAR(255), Field29 VARCHAR(255), Field30 VARCHAR(255),
    
    -- More integer columns
    Value01 INT, Value02 INT, Value03 INT, Value04 INT, Value05 INT,
    Value06 INT, Value07 INT, Value08 INT, Value09 INT, Value10 INT,
    Value11 INT, Value12 INT, Value13 INT, Value14 INT, Value15 INT,
    Value16 INT, Value17 INT, Value18 INT, Value19 INT, Value20 INT,
    
    -- Additional bit columns
    Flag01 BIT, Flag02 BIT, Flag03 BIT, Flag04 BIT, Flag05 BIT,
    Flag06 BIT, Flag07 BIT, Flag08 BIT, Flag09 BIT, Flag10 BIT
);
GO

-- Smaller production test table for faster testing
IF OBJECT_ID('dbo.ProductionTestSmall', 'U') IS NOT NULL
    DROP TABLE dbo.ProductionTestSmall;
GO

CREATE TABLE dbo.ProductionTestSmall (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ExternalId UNIQUEIDENTIFIER DEFAULT NEWID(),
    
    -- Critical production data types
    HighPrecisionAmount DECIMAL(38,18),
    MoneyValue MONEY,
    LargeText VARCHAR(MAX),
    StandardText VARCHAR(255),
    Counter INT,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    ModifiedDate DATETIME2 DEFAULT GETDATE()
);
GO

PRINT 'Production-scale test tables created successfully!'
GO