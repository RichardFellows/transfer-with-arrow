# SCD2 Table Configuration Guide

This document explains how to configure and use SCD2 (Slowly Changing Dimension Type 2) tables with the DLT pipeline.

## Overview

SCD2 tables track historical changes to dimension data by maintaining multiple versions of each business entity. Each change creates a new record with temporal validity periods, preserving the complete history of how data evolves over time.

## SCD2 Table Structure

### Core SCD2 Framework Columns

| Column | Type | Purpose |
|--------|------|---------|
| `Key` | BIGINT IDENTITY | Surrogate key (unique identifier for each version) |
| `ClientBusinessKey` | VARCHAR(50) | Natural business key (e.g., CLIENT_0001) |
| `EffectiveFromDate` | DATETIME2 | When this version became active |
| `EffectiveToDate` | DATETIME2 | When this version expired (NULL = current) |
| `IsLatest` | BIT | Flag indicating current/latest version (1 = current, 0 = historical) |

### Incremental Loading Support

| Column | Type | Purpose |
|--------|------|---------|
| `SystemCalendarID` | INT | YYYYMMDD format for incremental loading watermark |
| `LoadDateTime` | DATETIME2 | When this record was loaded into the data warehouse |

### Change Tracking

| Column | Type | Purpose |
|--------|------|---------|
| `ChangeType` | VARCHAR(20) | Type of change: INSERT, UPDATE, DELETE |
| `ChangeReason` | VARCHAR(255) | Business reason for the change |
| `BatchID` | UNIQUEIDENTIFIER | Unique identifier for the ETL batch |

## DLT Configuration

### Basic SCD2 Configuration

```yaml
tables:
  Reporting_Client_SCD2:
    source_table: "dbo.Reporting_Client_SCD2"
    destination_table: "reporting_client_scd2"
    disposition: "append"  # Always use append for SCD2
    incremental:
      enabled: true
      strategy: "sequence"  # Use sequence for SystemCalendarID
      watermark_column: "SystemCalendarID"
      initial_value: 0
    enabled: true
    primary_key: ["Key"]  # SCD2 surrogate key
```

### Key Configuration Points

1. **Disposition**: Always use `"append"` for SCD2 tables to preserve historical records
2. **Primary Key**: Use the SCD2 surrogate key (`Key`) as the primary key
3. **Watermark Column**: Use `SystemCalendarID` for date-based incremental loading
4. **Strategy**: Use `"sequence"` for integer-based watermarks

## Column Name Preservation

With the `naming_convention: "direct"` setting, all SCD2 column names are preserved exactly as defined:

**Source Columns (SQL Server):**
```sql
Key, ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest
```

**Destination Columns (Preserved):**
```sql
Key, ClientBusinessKey, EffectiveFromDate, EffectiveToDate, IsLatest
```

## SCD2 Data Examples

### Current Version Lookup
```sql
-- Get current client information
SELECT ClientBusinessKey, ClientName, CompanyName, SegmentCode
FROM reporting_client_scd2 
WHERE IsLatest = 1
```

### Historical Timeline
```sql
-- View complete history for a client
SELECT 
    ClientBusinessKey,
    EffectiveFromDate,
    EffectiveToDate,
    IsLatest,
    ClientName,
    SegmentCode,
    ChangeType,
    ChangeReason
FROM reporting_client_scd2 
WHERE ClientBusinessKey = 'CLIENT_0001'
ORDER BY EffectiveFromDate
```

### Point-in-Time Query
```sql
-- Get client data as it was on a specific date
DECLARE @AsOfDate DATETIME2 = '2025-08-15'

SELECT ClientBusinessKey, ClientName, SegmentCode
FROM reporting_client_scd2 
WHERE ClientBusinessKey = 'CLIENT_0001'
  AND EffectiveFromDate <= @AsOfDate
  AND (EffectiveToDate IS NULL OR EffectiveToDate > @AsOfDate)
```

## Incremental Loading Behavior

### Initial Load
- Loads all historical records from the source
- Preserves complete SCD2 history
- Sets watermark to the latest `SystemCalendarID`

### Incremental Updates
- Loads only new records since last watermark
- Maintains SCD2 integrity
- Preserves both current and historical versions

### Example Incremental Progression

**Day 1 (Initial Load):**
```
SystemCalendarID: 20250813
Records loaded: 500 (all historical data)
Watermark set to: 20250813
```

**Day 2 (Incremental):**
```
SystemCalendarID: 20250814  
Records loaded: 125 (new changes only)
Watermark updated to: 20250814
```

## Performance Considerations

### Indexes
The SCD2 table includes optimized indexes:

```sql
-- Business key lookup
IX_Reporting_Client_SCD2_BusinessKey (ClientBusinessKey)

-- Temporal range queries
IX_Reporting_Client_SCD2_EffectiveDates (EffectiveFromDate, EffectiveToDate)

-- Current records only (filtered index)
IX_Reporting_Client_SCD2_IsLatest (IsLatest, ClientBusinessKey) WHERE IsLatest = 1

-- Incremental loading
IX_Reporting_Client_SCD2_SystemCalendarID (SystemCalendarID)

-- SCD2 compound lookup
IX_Reporting_Client_SCD2_Lookup (ClientBusinessKey, EffectiveFromDate, EffectiveToDate)
```

### Query Patterns

**✅ Efficient Patterns:**
```sql
-- Current records only
WHERE IsLatest = 1

-- Specific business key
WHERE ClientBusinessKey = 'CLIENT_0001'

-- Date range queries
WHERE EffectiveFromDate >= '2025-08-01' 
  AND (EffectiveToDate IS NULL OR EffectiveToDate <= '2025-08-31')
```

**❌ Avoid These Patterns:**
```sql
-- Full table scan
SELECT * FROM reporting_client_scd2

-- Functions on indexed columns
WHERE YEAR(EffectiveFromDate) = 2025

-- OR conditions on different columns
WHERE IsLatest = 1 OR EffectiveToDate IS NULL
```

## Data Quality Checks

### SCD2 Integrity Validation

```sql
-- 1. Each business key should have exactly one current version
SELECT ClientBusinessKey, COUNT(*) as CurrentVersions
FROM reporting_client_scd2 
WHERE IsLatest = 1
GROUP BY ClientBusinessKey
HAVING COUNT(*) > 1

-- 2. No overlapping effective date ranges
WITH Overlaps AS (
    SELECT a.ClientBusinessKey, a.Key as Key1, b.Key as Key2
    FROM reporting_client_scd2 a
    JOIN reporting_client_scd2 b ON a.ClientBusinessKey = b.ClientBusinessKey
    WHERE a.Key != b.Key
      AND a.EffectiveFromDate < ISNULL(b.EffectiveToDate, '9999-12-31')
      AND ISNULL(a.EffectiveToDate, '9999-12-31') > b.EffectiveFromDate
)
SELECT * FROM Overlaps

-- 3. Verify temporal continuity
SELECT ClientBusinessKey,
       COUNT(*) as VersionCount,
       MIN(EffectiveFromDate) as EarliestVersion,
       MAX(CASE WHEN IsLatest = 1 THEN EffectiveFromDate END) as LatestVersion
FROM reporting_client_scd2
GROUP BY ClientBusinessKey
```

## Testing and Validation

### Sample Data Structure

Our test data demonstrates real SCD2 scenarios:

- **1,018 unique business keys** (clients)
- **2,500 total records** (including historical versions)
- **2,000 current versions** (IsLatest = 1)
- **500 historical versions** (IsLatest = 0)
- **5 days of change history** (20250813-20250817)

### Change Types Demonstrated

1. **INSERT**: New client onboarding
2. **UPDATE**: Contact information changes, segment upgrades, status changes
3. **Business Logic**: Credit limit adjustments, priority changes, VIP upgrades

### Verification Queries

```sql
-- Overall statistics
SELECT 
    COUNT(*) as TotalRecords,
    COUNT(DISTINCT ClientBusinessKey) as UniqueClients,
    COUNT(CASE WHEN IsLatest = 1 THEN 1 END) as CurrentVersions,
    COUNT(CASE WHEN IsLatest = 0 THEN 1 END) as HistoricalVersions
FROM reporting_client_scd2

-- Daily loading summary
SELECT 
    SystemCalendarID,
    COUNT(*) as RecordsLoaded,
    COUNT(DISTINCT ClientBusinessKey) as ClientsAffected,
    COUNT(CASE WHEN ChangeType = 'INSERT' THEN 1 END) as NewClients,
    COUNT(CASE WHEN ChangeType = 'UPDATE' THEN 1 END) as UpdatedClients
FROM reporting_client_scd2
GROUP BY SystemCalendarID
ORDER BY SystemCalendarID
```

## Best Practices

### 1. Column Name Consistency
- Use PascalCase for SCD2 framework columns
- Maintain consistent naming with source systems
- Preserve business terminology in dimension attributes

### 2. Temporal Design
- Always use `NULL` for current record end dates
- Ensure proper temporal ordering
- Use microsecond precision for close temporal boundaries

### 3. Change Tracking
- Document change reasons for business users
- Track ETL batch information for debugging
- Implement proper change type classification

### 4. Performance Optimization
- Create filtered indexes for current records
- Partition large SCD2 tables by date ranges
- Consider archiving very old historical versions

### 5. Data Quality
- Implement SCD2 integrity constraints
- Validate temporal consistency
- Monitor for orphaned historical records

## Integration with Analytics

### Fact Table Joins
```sql
-- Join facts to current dimension
SELECT f.*, d.ClientName, d.SegmentCode
FROM fact_table f
JOIN reporting_client_scd2 d ON f.ClientBusinessKey = d.ClientBusinessKey
WHERE d.IsLatest = 1

-- Point-in-time fact-dimension join
SELECT f.*, d.ClientName, d.SegmentCode  
FROM fact_table f
JOIN reporting_client_scd2 d ON f.ClientBusinessKey = d.ClientBusinessKey
WHERE f.TransactionDate >= d.EffectiveFromDate
  AND f.TransactionDate < ISNULL(d.EffectiveToDate, '9999-12-31')
```

### Trend Analysis
```sql
-- Track segment migrations over time
SELECT 
    ClientBusinessKey,
    EffectiveFromDate,
    SegmentCode,
    LAG(SegmentCode) OVER (PARTITION BY ClientBusinessKey ORDER BY EffectiveFromDate) as PreviousSegment
FROM reporting_client_scd2
WHERE ChangeType = 'UPDATE'
```

This SCD2 implementation provides a robust foundation for tracking dimensional changes while maintaining high performance and data quality.