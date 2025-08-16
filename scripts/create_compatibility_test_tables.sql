-- Systematic DLT Compatibility Test Tables
-- This script creates multiple test tables to identify exact compatibility limits
-- for different column types, counts, and row volumes

USE StackOverflowMini;
GO

PRINT 'Creating DLT compatibility test tables...';

-- =========================================================================
-- Test 1: Individual Data Types (5 columns, varying row counts)
-- =========================================================================

-- Test 1A: DECIMAL(38,18) only
IF OBJECT_ID('dbo.Test_Decimal_Only', 'U') IS NOT NULL DROP TABLE dbo.Test_Decimal_Only;
CREATE TABLE dbo.Test_Decimal_Only (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Amount1 DECIMAL(38,18),
    Amount2 DECIMAL(38,18),
    Amount3 DECIMAL(38,18),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 1B: MONEY only
IF OBJECT_ID('dbo.Test_Money_Only', 'U') IS NOT NULL DROP TABLE dbo.Test_Money_Only;
CREATE TABLE dbo.Test_Money_Only (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Price1 MONEY,
    Price2 MONEY,
    Price3 MONEY,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 1C: VARCHAR(MAX) only
IF OBJECT_ID('dbo.Test_VarcharMax_Only', 'U') IS NOT NULL DROP TABLE dbo.Test_VarcharMax_Only;
CREATE TABLE dbo.Test_VarcharMax_Only (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    LargeText1 VARCHAR(MAX),
    LargeText2 VARCHAR(MAX),
    LargeText3 VARCHAR(MAX),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 1D: Mixed problematic types
IF OBJECT_ID('dbo.Test_Mixed_Problematic', 'U') IS NOT NULL DROP TABLE dbo.Test_Mixed_Problematic;
CREATE TABLE dbo.Test_Mixed_Problematic (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Amount DECIMAL(38,18),
    Price MONEY,
    LargeText VARCHAR(MAX),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- =========================================================================
-- Test 2: Column Count Variations (standard types)
-- =========================================================================

-- Test 2A: 10 columns
IF OBJECT_ID('dbo.Test_10_Columns', 'U') IS NOT NULL DROP TABLE dbo.Test_10_Columns;
CREATE TABLE dbo.Test_10_Columns (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Col1 VARCHAR(255), Col2 VARCHAR(255), Col3 VARCHAR(255), Col4 VARCHAR(255), Col5 VARCHAR(255),
    Val1 INT, Val2 INT, Val3 INT, Val4 INT,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 2B: 25 columns
IF OBJECT_ID('dbo.Test_25_Columns', 'U') IS NOT NULL DROP TABLE dbo.Test_25_Columns;
CREATE TABLE dbo.Test_25_Columns (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Col01 VARCHAR(255), Col02 VARCHAR(255), Col03 VARCHAR(255), Col04 VARCHAR(255), Col05 VARCHAR(255),
    Col06 VARCHAR(255), Col07 VARCHAR(255), Col08 VARCHAR(255), Col09 VARCHAR(255), Col10 VARCHAR(255),
    Col11 VARCHAR(255), Col12 VARCHAR(255), Col13 VARCHAR(255), Col14 VARCHAR(255), Col15 VARCHAR(255),
    Val01 INT, Val02 INT, Val03 INT, Val04 INT, Val05 INT,
    Flag1 BIT, Flag2 BIT, Flag3 BIT,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 2C: 50 columns
IF OBJECT_ID('dbo.Test_50_Columns', 'U') IS NOT NULL DROP TABLE dbo.Test_50_Columns;
CREATE TABLE dbo.Test_50_Columns (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    -- 20 VARCHAR columns
    C01 VARCHAR(255), C02 VARCHAR(255), C03 VARCHAR(255), C04 VARCHAR(255), C05 VARCHAR(255),
    C06 VARCHAR(255), C07 VARCHAR(255), C08 VARCHAR(255), C09 VARCHAR(255), C10 VARCHAR(255),
    C11 VARCHAR(255), C12 VARCHAR(255), C13 VARCHAR(255), C14 VARCHAR(255), C15 VARCHAR(255),
    C16 VARCHAR(255), C17 VARCHAR(255), C18 VARCHAR(255), C19 VARCHAR(255), C20 VARCHAR(255),
    -- 15 INT columns
    V01 INT, V02 INT, V03 INT, V04 INT, V05 INT, V06 INT, V07 INT, V08 INT, V09 INT, V10 INT,
    V11 INT, V12 INT, V13 INT, V14 INT, V15 INT,
    -- 10 BIT columns
    F01 BIT, F02 BIT, F03 BIT, F04 BIT, F05 BIT, F06 BIT, F07 BIT, F08 BIT, F09 BIT, F10 BIT,
    -- 3 DATETIME columns
    Date1 DATETIME2, Date2 DATETIME2, Date3 DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 2D: 75 columns
IF OBJECT_ID('dbo.Test_75_Columns', 'U') IS NOT NULL DROP TABLE dbo.Test_75_Columns;
CREATE TABLE dbo.Test_75_Columns (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    -- 30 VARCHAR columns
    C01 VARCHAR(255), C02 VARCHAR(255), C03 VARCHAR(255), C04 VARCHAR(255), C05 VARCHAR(255),
    C06 VARCHAR(255), C07 VARCHAR(255), C08 VARCHAR(255), C09 VARCHAR(255), C10 VARCHAR(255),
    C11 VARCHAR(255), C12 VARCHAR(255), C13 VARCHAR(255), C14 VARCHAR(255), C15 VARCHAR(255),
    C16 VARCHAR(255), C17 VARCHAR(255), C18 VARCHAR(255), C19 VARCHAR(255), C20 VARCHAR(255),
    C21 VARCHAR(255), C22 VARCHAR(255), C23 VARCHAR(255), C24 VARCHAR(255), C25 VARCHAR(255),
    C26 VARCHAR(255), C27 VARCHAR(255), C28 VARCHAR(255), C29 VARCHAR(255), C30 VARCHAR(255),
    -- 25 INT columns
    V01 INT, V02 INT, V03 INT, V04 INT, V05 INT, V06 INT, V07 INT, V08 INT, V09 INT, V10 INT,
    V11 INT, V12 INT, V13 INT, V14 INT, V15 INT, V16 INT, V17 INT, V18 INT, V19 INT, V20 INT,
    V21 INT, V22 INT, V23 INT, V24 INT, V25 INT,
    -- 15 BIT columns
    F01 BIT, F02 BIT, F03 BIT, F04 BIT, F05 BIT, F06 BIT, F07 BIT, F08 BIT, F09 BIT, F10 BIT,
    F11 BIT, F12 BIT, F13 BIT, F14 BIT, F15 BIT,
    -- 3 DATETIME columns
    Date1 DATETIME2, Date2 DATETIME2, Date3 DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- =========================================================================
-- Test 3: Complex Data Type Combinations
-- =========================================================================

-- Test 3A: 10 columns with complex types
IF OBJECT_ID('dbo.Test_10_Complex', 'U') IS NOT NULL DROP TABLE dbo.Test_10_Complex;
CREATE TABLE dbo.Test_10_Complex (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Amount1 DECIMAL(38,18),
    Amount2 DECIMAL(38,18),
    Price1 MONEY,
    Price2 MONEY,
    LargeText VARCHAR(MAX),
    StandardText VARCHAR(255),
    Counter INT,
    Flag BIT,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 3B: 25 columns with complex types
IF OBJECT_ID('dbo.Test_25_Complex', 'U') IS NOT NULL DROP TABLE dbo.Test_25_Complex;
CREATE TABLE dbo.Test_25_Complex (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    -- 5 DECIMAL(38,18) columns
    Amount1 DECIMAL(38,18), Amount2 DECIMAL(38,18), Amount3 DECIMAL(38,18), Amount4 DECIMAL(38,18), Amount5 DECIMAL(38,18),
    -- 5 MONEY columns
    Price1 MONEY, Price2 MONEY, Price3 MONEY, Price4 MONEY, Price5 MONEY,
    -- 5 VARCHAR(MAX) columns
    Text1 VARCHAR(MAX), Text2 VARCHAR(MAX), Text3 VARCHAR(MAX), Text4 VARCHAR(MAX), Text5 VARCHAR(MAX),
    -- 5 VARCHAR(255) columns
    Code1 VARCHAR(255), Code2 VARCHAR(255), Code3 VARCHAR(255), Code4 VARCHAR(255), Code5 VARCHAR(255),
    -- 3 INT columns
    Counter1 INT, Counter2 INT, Counter3 INT,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 3C: 50 columns with complex types
IF OBJECT_ID('dbo.Test_50_Complex', 'U') IS NOT NULL DROP TABLE dbo.Test_50_Complex;
CREATE TABLE dbo.Test_50_Complex (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    -- 10 DECIMAL(38,18) columns
    Amount01 DECIMAL(38,18), Amount02 DECIMAL(38,18), Amount03 DECIMAL(38,18), Amount04 DECIMAL(38,18), Amount05 DECIMAL(38,18),
    Amount06 DECIMAL(38,18), Amount07 DECIMAL(38,18), Amount08 DECIMAL(38,18), Amount09 DECIMAL(38,18), Amount10 DECIMAL(38,18),
    -- 5 MONEY columns
    Price1 MONEY, Price2 MONEY, Price3 MONEY, Price4 MONEY, Price5 MONEY,
    -- 10 VARCHAR(MAX) columns
    Text01 VARCHAR(MAX), Text02 VARCHAR(MAX), Text03 VARCHAR(MAX), Text04 VARCHAR(MAX), Text05 VARCHAR(MAX),
    Text06 VARCHAR(MAX), Text07 VARCHAR(MAX), Text08 VARCHAR(MAX), Text09 VARCHAR(MAX), Text10 VARCHAR(MAX),
    -- 15 VARCHAR(255) columns
    Code01 VARCHAR(255), Code02 VARCHAR(255), Code03 VARCHAR(255), Code04 VARCHAR(255), Code05 VARCHAR(255),
    Code06 VARCHAR(255), Code07 VARCHAR(255), Code08 VARCHAR(255), Code09 VARCHAR(255), Code10 VARCHAR(255),
    Code11 VARCHAR(255), Code12 VARCHAR(255), Code13 VARCHAR(255), Code14 VARCHAR(255), Code15 VARCHAR(255),
    -- 5 INT columns
    Counter1 INT, Counter2 INT, Counter3 INT, Counter4 INT, Counter5 INT,
    -- 5 BIT columns
    Flag1 BIT, Flag2 BIT, Flag3 BIT, Flag4 BIT, Flag5 BIT,
    -- 2 DATETIME columns
    Date1 DATETIME2, Date2 DATETIME2,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- =========================================================================
-- Test 4: Specific Problem Data Types
-- =========================================================================

-- Test 4A: Only VARCHAR(MAX) columns (potential memory issue)
IF OBJECT_ID('dbo.Test_VarcharMax_Heavy', 'U') IS NOT NULL DROP TABLE dbo.Test_VarcharMax_Heavy;
CREATE TABLE dbo.Test_VarcharMax_Heavy (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Text01 VARCHAR(MAX), Text02 VARCHAR(MAX), Text03 VARCHAR(MAX), Text04 VARCHAR(MAX), Text05 VARCHAR(MAX),
    Text06 VARCHAR(MAX), Text07 VARCHAR(MAX), Text08 VARCHAR(MAX), Text09 VARCHAR(MAX), Text10 VARCHAR(MAX),
    Text11 VARCHAR(MAX), Text12 VARCHAR(MAX), Text13 VARCHAR(MAX), Text14 VARCHAR(MAX), Text15 VARCHAR(MAX),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 4B: Only DECIMAL(38,18) columns (precision issue)
IF OBJECT_ID('dbo.Test_Decimal_Heavy', 'U') IS NOT NULL DROP TABLE dbo.Test_Decimal_Heavy;
CREATE TABLE dbo.Test_Decimal_Heavy (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Amount01 DECIMAL(38,18), Amount02 DECIMAL(38,18), Amount03 DECIMAL(38,18), Amount04 DECIMAL(38,18), Amount05 DECIMAL(38,18),
    Amount06 DECIMAL(38,18), Amount07 DECIMAL(38,18), Amount08 DECIMAL(38,18), Amount09 DECIMAL(38,18), Amount10 DECIMAL(38,18),
    Amount11 DECIMAL(38,18), Amount12 DECIMAL(38,18), Amount13 DECIMAL(38,18), Amount14 DECIMAL(38,18), Amount15 DECIMAL(38,18),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- Test 4C: Only MONEY columns
IF OBJECT_ID('dbo.Test_Money_Heavy', 'U') IS NOT NULL DROP TABLE dbo.Test_Money_Heavy;
CREATE TABLE dbo.Test_Money_Heavy (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Price01 MONEY, Price02 MONEY, Price03 MONEY, Price04 MONEY, Price05 MONEY,
    Price06 MONEY, Price07 MONEY, Price08 MONEY, Price09 MONEY, Price10 MONEY,
    Price11 MONEY, Price12 MONEY, Price13 MONEY, Price14 MONEY, Price15 MONEY,
    CreatedDate DATETIME2 DEFAULT GETDATE()
);

-- =========================================================================
-- Test 5: Edge Cases
-- =========================================================================

-- Test 5A: Minimal table (2 columns)
IF OBJECT_ID('dbo.Test_Minimal', 'U') IS NOT NULL DROP TABLE dbo.Test_Minimal;
CREATE TABLE dbo.Test_Minimal (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    SimpleText VARCHAR(255)
);

-- Test 5B: Wide table with simple types (100 columns)
IF OBJECT_ID('dbo.Test_100_Simple', 'U') IS NOT NULL DROP TABLE dbo.Test_100_Simple;
CREATE TABLE dbo.Test_100_Simple (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    -- 50 VARCHAR(255) columns
    S01 VARCHAR(255), S02 VARCHAR(255), S03 VARCHAR(255), S04 VARCHAR(255), S05 VARCHAR(255),
    S06 VARCHAR(255), S07 VARCHAR(255), S08 VARCHAR(255), S09 VARCHAR(255), S10 VARCHAR(255),
    S11 VARCHAR(255), S12 VARCHAR(255), S13 VARCHAR(255), S14 VARCHAR(255), S15 VARCHAR(255),
    S16 VARCHAR(255), S17 VARCHAR(255), S18 VARCHAR(255), S19 VARCHAR(255), S20 VARCHAR(255),
    S21 VARCHAR(255), S22 VARCHAR(255), S23 VARCHAR(255), S24 VARCHAR(255), S25 VARCHAR(255),
    S26 VARCHAR(255), S27 VARCHAR(255), S28 VARCHAR(255), S29 VARCHAR(255), S30 VARCHAR(255),
    S31 VARCHAR(255), S32 VARCHAR(255), S33 VARCHAR(255), S34 VARCHAR(255), S35 VARCHAR(255),
    S36 VARCHAR(255), S37 VARCHAR(255), S38 VARCHAR(255), S39 VARCHAR(255), S40 VARCHAR(255),
    S41 VARCHAR(255), S42 VARCHAR(255), S43 VARCHAR(255), S44 VARCHAR(255), S45 VARCHAR(255),
    S46 VARCHAR(255), S47 VARCHAR(255), S48 VARCHAR(255), S49 VARCHAR(255), S50 VARCHAR(255),
    -- 49 INT columns
    I01 INT, I02 INT, I03 INT, I04 INT, I05 INT, I06 INT, I07 INT, I08 INT, I09 INT, I10 INT,
    I11 INT, I12 INT, I13 INT, I14 INT, I15 INT, I16 INT, I17 INT, I18 INT, I19 INT, I20 INT,
    I21 INT, I22 INT, I23 INT, I24 INT, I25 INT, I26 INT, I27 INT, I28 INT, I29 INT, I30 INT,
    I31 INT, I32 INT, I33 INT, I34 INT, I35 INT, I36 INT, I37 INT, I38 INT, I39 INT, I40 INT,
    I41 INT, I42 INT, I43 INT, I44 INT, I45 INT, I46 INT, I47 INT, I48 INT, I49 INT
);

PRINT 'DLT compatibility test tables created successfully!';

-- Show table summary
SELECT 'Test table creation completed' as Status;
GO