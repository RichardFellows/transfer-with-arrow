# Production-Scale Incremental Loading Testing

This document describes the comprehensive incremental loading test framework for production-scale data scenarios.

## Overview

The incremental testing framework simulates real-world production data loading with:

- **100+ column table** with mixed data types (MONEY, DECIMAL(38,18), FLOAT, INT, BIT, VARCHAR, etc.)
- **High-volume data** (6M initial records + 2M incremental)
- **Daily batch processing** using SystemCalendarID watermark (YYYYMMDD format)
- **Schema optimization** with automatic MONEY column coercion
- **Comprehensive verification** of data integrity and schema consistency

## Test Scenario Architecture

### 📊 Table Structure: `Reporting_Client`

- **130+ columns** with production-realistic data types
- **SystemCalendarID** (INT): Primary watermark column in YYYYMMDD format
- **Mixed data types**:
  - MONEY columns (automatically mapped to DECIMAL(19,4))
  - DECIMAL(38,18) high-precision financial data
  - FLOAT performance metrics
  - VARCHAR(MAX) large text fields
  - 20+ BIT flags
  - DATETIME2 timestamps

### 📈 Data Volume Profile

| Scenario | Records | SystemCalendarID | Purpose |
|----------|---------|------------------|---------|
| **Initial Load** | 6M records | 3 consecutive days | Baseline full sync |
| **Incremental Load** | 2M records | Next day | Daily batch simulation |
| **Total** | 8M records | 4 days | Production scale test |

### 🔄 Incremental Loading Strategy

- **Watermark Column**: `SystemCalendarID` (INT, YYYYMMDD format)
- **Strategy**: DLT sequence strategy for integer-based watermarks
- **Mode**: `append` disposition for incremental records
- **Detection**: Automatic detection of new calendar IDs

## Quick Start

### 1. Complete End-to-End Test

Run the full scenario with all verification:

```bash
make reporting-scenario
```

This executes:
1. Table creation (130+ columns)
2. Initial data load (6M records, 3 days)
3. Full synchronization
4. Verification of initial sync
5. Add next day data (2M records)
6. Incremental synchronization (new records only)
7. Final verification (8M total records)

### 2. Step-by-Step Testing

For more control, run individual steps:

```bash
# Step 1: Setup table and load initial data
make reporting-setup

# Step 2: Run initial full sync  
make reporting-full-sync

# Step 3: Verify initial sync results
make reporting-verify

# Step 4: Add next day's data
make reporting-add-day

# Step 5: Run incremental sync
make reporting-incremental

# Step 6: Final verification
make reporting-verify
```

### 3. Workflow Shortcuts

```bash
# Full initial workflow (setup + sync + verify)
make reporting-full-workflow

# Incremental workflow (add data + sync + verify)
make reporting-incremental-workflow
```

## Schema Optimization Features

### Automatic MONEY Column Handling

The enhanced TableProcessor automatically detects and optimizes MONEY columns:

```sql
-- Source: MONEY columns
Price1 MONEY,
Price2 MONEY,
-- ... more MONEY columns

-- Automatically mapped to consistent DECIMAL(19,4) in destination
-- Eliminates schema evolution conflicts
```

### High-Precision Decimal Preservation

```sql
-- Source: High-precision decimals
NetAmount DECIMAL(38,18),
GrossAmount DECIMAL(38,18),

-- Destination: Exact precision preserved
-- No precision loss during transfer
```

### Large Text Field Optimization

```sql
-- Source: VARCHAR(MAX) fields
Notes VARCHAR(MAX),
Description VARCHAR(MAX),

-- Destination: Optimized TEXT mapping
-- Efficient memory usage and performance
```

## Verification Components

### 1. Record Count Verification

Validates exact record counts by SystemCalendarID:

```
✅ SystemCalendarID 20241214: 2,000,000 → 2,000,000  
✅ SystemCalendarID 20241215: 2,000,000 → 2,000,000
✅ SystemCalendarID 20241216: 2,000,000 → 2,000,000
✅ SystemCalendarID 20241217: 2,000,000 → 2,000,000
📊 Total: 8,000,000 records synchronized
```

### 2. Schema Consistency Check

Compares source and destination table schemas:

- Column count matching
- Data type consistency  
- Precision/scale alignment
- Nullable constraints

### 3. Data Integrity Sampling

Random sampling verification of:

- Primary key consistency
- Critical field values
- Data type conversion accuracy
- Null value handling

## Performance Benchmarks

Based on testing with 8M records and 130+ columns:

| Operation | Duration | Throughput | Notes |
|-----------|----------|------------|-------|
| **Table Creation** | ~30s | N/A | DDL + indexes |
| **Initial Data Load** | ~15-20 min | ~5-6K rows/sec | SQL bulk insert |
| **Full Sync (6M)** | ~10-15 min | ~6-10K rows/sec | DLT PyArrow |
| **Incremental Sync (2M)** | ~3-5 min | ~6-10K rows/sec | Watermark filtering |
| **Verification** | ~1-2 min | N/A | Schema + sampling |

## Configuration Details

### Pipeline Configuration (`pipeline_config.yaml`)

```yaml
pipeline:
  name: "reporting_client_pipeline"
  backend: "pyarrow"
  chunk_size: 10000  # Optimized for large tables

tables:
  Reporting_Client:
    source_table: "dbo.Reporting_Client"
    destination_table: "reporting_client"
    disposition: "append"  # For incremental loading
    incremental:
      enabled: true
      strategy: "sequence"  # Integer-based watermark
      watermark_column: "SystemCalendarID"
      initial_value: 0  # Updated dynamically
```

### Automatic Schema Optimization

The TableProcessor automatically applies:

```python
# MONEY columns → DECIMAL(19,4)
"price1": {"data_type": "decimal", "precision": 19, "scale": 4}

# High-precision decimals preserved  
"netamount": {"data_type": "decimal", "precision": 38, "scale": 18}

# Large text optimized
"notes": {"data_type": "text"}
```

## Troubleshooting Guide

### Common Issues

#### 1. MONEY Column Schema Conflicts

**Symptom**: 
```
ArrowInvalid: Schema at index 0 was different:
price1: decimal128(10, 4) vs decimal128(19, 4)
```

**Solution**: 
The enhanced TableProcessor automatically prevents this by forcing consistent DECIMAL(19,4) mapping.

#### 2. High Memory Usage

**Symptom**: Container memory limits exceeded

**Solutions**:
- Reduce `chunk_size` in configuration
- Increase Docker memory allocation
- Use smaller test data sets for development

#### 3. Slow Performance

**Symptom**: Sync taking longer than expected

**Investigation**:
- Check database indexes on SystemCalendarID
- Monitor container CPU/memory usage
- Verify network connectivity between containers

#### 4. Incomplete Incremental Sync

**Symptom**: Not all new records transferred

**Investigation**:
- Verify SystemCalendarID values in source
- Check DLT state management
- Ensure initial_value is set correctly

### Verification Failures

#### Record Count Mismatches

```bash
# Check source counts
make sql-source
SELECT SystemCalendarID, COUNT(*) FROM dbo.Reporting_Client GROUP BY SystemCalendarID;

# Check destination counts  
make sql-dest
SELECT systemcalendarid, COUNT(*) FROM reporting_client GROUP BY systemcalendarid;
```

#### Schema Differences

```bash
# Run detailed verification
make reporting-verify

# Check specific schema details
docker exec dlt-runner python /scripts/verify_incremental_sync.py
```

## Advanced Usage

### Custom Data Scenarios

Modify the data generation scripts to test specific scenarios:

1. **Different Volume Profiles**: Adjust record counts in `populate_reporting_client_data.sql`
2. **Custom Date Ranges**: Modify SystemCalendarID generation logic
3. **Specific Data Types**: Add/remove columns in `create_reporting_client_table.sql`
4. **Error Scenarios**: Introduce data quality issues for testing

### Monitoring and Observability

```bash
# Monitor pipeline progress
make logs

# Check container resource usage
docker stats

# View detailed DLT logs
docker exec dlt-runner cat /app/logs/pipeline.log
```

### Integration with CI/CD

The verification script returns appropriate exit codes:

```bash
# Use in automated testing
make reporting-scenario
if [ $? -eq 0 ]; then
    echo "✅ Incremental loading test passed"
else
    echo "❌ Incremental loading test failed"
    exit 1
fi
```

## Production Readiness

This testing framework validates production readiness for:

- ✅ **100+ column tables** with mixed data types
- ✅ **Multi-million record** daily batch processing  
- ✅ **MONEY column consistency** across schema evolution
- ✅ **High-precision decimal** preservation
- ✅ **Incremental loading** by date-based watermarks
- ✅ **Data integrity** and schema consistency
- ✅ **Performance** suitable for production workloads

The framework demonstrates that the enhanced DLT pipeline can handle real-world production scenarios with reliable schema optimization and data integrity guarantees.