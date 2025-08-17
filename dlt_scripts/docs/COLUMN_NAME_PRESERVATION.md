# Column Name Preservation Feature

## Overview

This feature allows you to preserve original column names from the source database, preventing DLT's automatic snake_case transformation.

## Configuration

Add the `naming_convention` setting to your pipeline configuration:

```yaml
pipeline:
  name: "my_pipeline"
  dataset_name: "my_data"
  backend: "pyarrow"
  naming_convention: "direct"  # Preserve original column names
```

## How It Works

When `naming_convention: "direct"` is set:

1. **Environment Variable**: Sets `SCHEMA__NAMING=direct` for DLT
2. **Source Schema**: Applies naming convention to the source schema
3. **Pipeline Schema**: Applies naming convention to the pipeline schema
4. **Column Preservation**: DLT preserves original column names and case

## Example Configuration Files

### Basic Usage
```yaml
# reporting_client_config_preserve_names.yaml
pipeline:
  naming_convention: "direct"
  
tables:
  Reporting_Client:
    watermark_column: "SystemCalendarID"  # Original PascalCase name
    primary_key: ["RecordID"]             # Original PascalCase name
```

### Expected Behavior

**Without naming convention (default snake_case):**
```sql
-- Source columns (PascalCase)
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName

-- Destination columns (snake_case)  
system_calendar_id, client_id, account_number, client_code, client_name
```

**With `naming_convention: "direct"`:**
```sql
-- Source columns (PascalCase)
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName

-- Destination columns (preserved) ✅ WORKING
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName
```

## Implementation Details

### Code Changes

1. **Config Model** (`config_models.py`):
   ```python
   class NamingConvention(str, Enum):
       SNAKE_CASE = "snake_case"  # Default: lowercase with underscores
       DIRECT = "direct"          # Preserves original names ✅
       DUCK_CASE = "duck_case"    # Case-sensitive, Unicode support
       SQL_CS_V1 = "sql_cs_v1"    # Case-sensitive SQL-safe
       SQL_CI_V1 = "sql_ci_v1"    # Case-insensitive SQL-safe

   class PipelineConfig(BaseModel):
       naming_convention: NamingConvention = Field(
           default=NamingConvention.SNAKE_CASE,
           description="DLT naming convention for columns and tables"
       )
   ```

2. **Table Processor** (`table_processor.py`):
   ```python
   # Set environment variable for DLT
   os.environ["SCHEMA__NAMING"] = self.config.pipeline.naming_convention.value
   
   # Apply to source schema
   source.schema.naming.naming_convention = self.config.pipeline.naming_convention.value
   
   # Apply to pipeline schema  
   pipeline.default_schema.naming.naming_convention = self.config.pipeline.naming_convention.value
   ```

### Log Output

When the feature is enabled, you'll see these log messages:
```
🏷️ Set environment SCHEMA__NAMING=direct
🏷️ Setting source naming convention to: direct
✅ Source naming convention successfully set to: direct
🏷️ Applying naming convention: direct
✅ Successfully set pipeline naming convention to: direct
```

## Current Status

### ✅ **WORKING SOLUTION**

**Implementation Successfully Completed**: The column name preservation feature is now **fully functional** using DLT's built-in naming convention system.

**Working Implementation**:
- Uses DLT's `"direct"` naming convention instead of manual column hints
- Sets `SCHEMA__NAMING=direct` environment variable for DLT
- Applies naming convention at both source and pipeline levels
- Successfully preserves original PascalCase column names

**Evidence of Success**:
- **Source columns**: `SystemCalendarID`, `ClientID`, `AccountNumber`, `ClientCode`
- **Destination columns**: `SystemCalendarID`, `ClientID`, `AccountNumber`, `ClientCode` ✅ **PRESERVED**
- DLT logs show: `🏷️ Set environment SCHEMA__NAMING=direct` ✅
- DLT warning messages now show PascalCase: `Address2`, `LastLoginDate` ✅

### Possible Solutions

1. **Custom DLT Resource Decorator**: Override the resource naming at the decorator level
2. **PyArrow Schema Override**: Directly manipulate the PyArrow schema before loading
3. **Alternative Backend**: Use a different DLT backend that respects column name hints
4. **Post-Processing**: Create views or aliases in the destination with original names

### Workaround

For now, you can create database views with the original column names:

```sql
-- Create view with original column names
CREATE VIEW reporting_data_preserved.Reporting_Client AS
SELECT 
    record_id AS RecordID,
    system_calendar_id AS SystemCalendarID,
    client_id AS ClientID,
    account_number AS AccountNumber,
    client_code AS ClientCode,
    client_name AS ClientName
    -- ... etc for all columns
FROM reporting_data_preserved.reporting_client_preserved;
```

## Configuration Examples

### Example 1: Enable for Specific Pipeline
```yaml
# Use preserved names for this pipeline
pipeline:
  name: "legacy_system_migration"
  naming_convention: "direct"
```

### Example 2: Default Behavior
```yaml
# Use DLT default snake_case transformation
pipeline:
  name: "modern_analytics_pipeline"
  naming_convention: "snake_case"  # or omit (default)
```

## Benefits When Working

1. **Legacy System Compatibility**: Maintains compatibility with existing queries and applications
2. **Documentation Clarity**: Column names match source system documentation
3. **Reduced Mapping**: No need to maintain column name mappings
4. **Query Consistency**: Same column names across source and destination

## Testing

Test configurations are provided:
- `reporting_client_config.yaml` - Standard snake_case transformation
- `reporting_client_config_preserve_names.yaml` - Column name preservation (when working)

## Future Enhancements

1. **Backend Detection**: Automatically detect which backends support name preservation
2. **Selective Preservation**: Allow preserving names for specific tables only
3. **Custom Naming Rules**: Support custom transformation rules beyond just preservation
4. **Migration Tools**: Utilities to convert between naming conventions