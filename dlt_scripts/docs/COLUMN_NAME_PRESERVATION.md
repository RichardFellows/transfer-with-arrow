# Column Name Preservation Feature

## Overview

This feature allows you to preserve original column names from the source database, preventing DLT's automatic snake_case transformation.

## Configuration

Add the `preserve_column_names` setting to your pipeline configuration:

```yaml
pipeline:
  name: "my_pipeline"
  dataset_name: "my_data"
  backend: "pyarrow"
  preserve_column_names: true  # NEW: Preserve original column names
```

## How It Works

When `preserve_column_names: true` is set:

1. **Schema Analysis**: The system queries the source database to get the exact column names (case-sensitive)
2. **Hint Generation**: For each column, it generates a DLT column hint with `name: "OriginalColumnName"`
3. **Schema Application**: These hints are applied to the DLT resource to override default naming

## Example Configuration Files

### Basic Usage
```yaml
# reporting_client_config_preserve_names.yaml
pipeline:
  preserve_column_names: true
  
tables:
  Reporting_Client:
    watermark_column: "SystemCalendarID"  # Original PascalCase name
    primary_key: ["RecordID"]             # Original PascalCase name
```

### Expected Behavior

**Without `preserve_column_names` (default):**
```sql
-- Source columns (PascalCase)
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName

-- Destination columns (snake_case)  
system_calendar_id, client_id, account_number, client_code, client_name
```

**With `preserve_column_names: true`:**
```sql
-- Source columns (PascalCase)
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName

-- Destination columns (preserved)
SystemCalendarID, ClientID, AccountNumber, ClientCode, ClientName
```

## Implementation Details

### Code Changes

1. **Config Model** (`config_models.py`):
   ```python
   class PipelineConfig(BaseModel):
       preserve_column_names: bool = Field(
           default=False, 
           description="Preserve original column names (disable snake_case transformation)"
       )
   ```

2. **Table Processor** (`table_processor.py`):
   ```python
   def _add_column_name_preservation_hints(self, source_table_name, schema_name, existing_hints):
       # Query source database for original column names
       # Generate DLT column hints with name preservation
       for original_col_name in original_columns:
           column_hints[original_col_name]["name"] = original_col_name
   ```

### Log Output

When the feature is enabled, you'll see these log messages:
```
🔒 Added name preservation hints for 118 columns
🎯 Generated 118 optimization hints for Reporting_Client
🔧 Applying 118 schema optimizations...
```

## Current Status and Limitations

### ⚠️ Known Issue

**Current State**: While the implementation correctly generates column name preservation hints, DLT's PyArrow backend appears to apply its snake_case transformation at a lower level that overrides these hints.

**Evidence**: 
- Code successfully generates 118 name preservation hints
- Hints are applied to DLT resources  
- But destination still shows snake_case column names

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
  preserve_column_names: true
```

### Example 2: Default Behavior
```yaml
# Use DLT default snake_case transformation
pipeline:
  name: "modern_analytics_pipeline"
  preserve_column_names: false  # or omit (default)
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