# Configuration-Driven Data Migration Pipeline

This directory contains a configuration-driven data migration pipeline built with DLT (Data Loading Tool) that provides flexible, reusable data migration capabilities.

## 🎯 Key Features

- **📋 YAML Configuration**: Complete pipeline configuration via YAML files
- **🔄 Environment Support**: Environment-specific configurations (dev/staging/prod)
- **⚡ Advanced Incremental Loading**: Multiple strategies with custom watermark columns
- **🔧 Table-Specific Settings**: Per-table disposition, filters, and transformations  
- **✅ Comprehensive Verification**: Data validation with custom checks
- **📊 Detailed Logging**: Structured logging with progress tracking
- **🔍 Schema Validation**: Pydantic-based configuration validation

## 📁 Directory Structure

```
dlt_scripts/
├── config/                      # Configuration files
│   ├── pipeline_config.yaml     # Main configuration
│   └── environments/            # Environment-specific configs
│       ├── dev.yaml
│       ├── prod.yaml
│       └── test.yaml
├── src/                         # Source code
│   ├── pipeline/               # Pipeline components
│   │   ├── config_models.py    # Pydantic configuration models
│   │   ├── config_loader.py    # Configuration loading with env substitution
│   │   ├── pipeline_runner.py  # Main pipeline orchestrator
│   │   ├── table_processor.py  # Table-specific processing logic
│   │   └── verification.py     # Data verification system
│   └── utils/                  # Utility modules
│       ├── logging_setup.py    # Logging configuration
│       └── cli_utils.py        # CLI utilities
├── run_pipeline.py             # Main CLI entry point
├── pipeline                    # Executable CLI wrapper
└── copy_stackoverflow.py      # Legacy script (for backward compatibility)
```

## 🚀 Quick Start

### 1. Basic Usage

```bash
# Run pipeline with default configuration
make pipeline-run

# Run with specific environment
make pipeline-run-dev

# Validate configuration
make pipeline-validate

# Show pipeline statistics
make pipeline-stats
```

### 2. Advanced Usage

```bash
# Run specific tables only
docker exec dlt-runner python /app/run_pipeline.py run --tables Users Posts

# Run with custom config and save results
docker exec dlt-runner python /app/run_pipeline.py run --config my_config.yaml --output results.json

# Validate specific environment
docker exec dlt-runner python /app/run_pipeline.py validate --environment prod
```

## 📝 Configuration Guide

### Basic Configuration Structure

```yaml
# config/pipeline_config.yaml
pipeline:
  name: "my_migration"
  dataset_name: "target_data"
  chunk_size: 10000
  backend: "pyarrow"

connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema: "dbo"
  destination:
    connection_string: "${DEST_CONNECTION_STRING}"
    schema: "target_schema"

tables:
  Users:
    source_table: "dbo.Users"
    disposition: "replace"
    incremental:
      enabled: false
    enabled: true

verification:
  enabled: true
  tolerance: 0

logging:
  level: "INFO"
```

### Table Configuration Options

Each table can be configured with:

```yaml
tables:
  MyTable:
    # Required
    source_table: "dbo.MyTable"               # Source table (with schema)
    
    # Optional settings
    destination_table: "my_table"             # Destination name (defaults to lowercase source)
    disposition: "merge"                      # replace|append|merge
    enabled: true                             # Whether to process this table
    
    # Incremental loading
    incremental:
      enabled: true
      strategy: "timestamp"                   # timestamp|sequence|custom
      watermark_column: "UpdatedDate"
      initial_value: "2020-01-01T00:00:00"
    
    # Advanced options
    primary_key: ["Id"]                       # Required for merge disposition
    where_clause: "IsActive = 1"              # Filter source data
    custom_sql: "SELECT * FROM dbo.MyTable WHERE ..." # Custom query
    column_mapping:                           # Column name mapping
      OldName: "new_name"
```

### Environment Configurations

Environment-specific settings override base configuration:

```yaml
# config/environments/dev.yaml
pipeline:
  name: "my_migration_dev"
  chunk_size: 1000                # Smaller chunks for development

tables:
  MyTable:
    where_clause: "CreatedDate >= '2023-01-01'"  # Only recent data in dev
    incremental:
      initial_value: "2023-01-01T00:00:00"

logging:
  level: "DEBUG"
  file_path: "logs/dev_pipeline.log"
```

### Environment Variables

Use environment variable substitution in configurations:

```yaml
connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    # With default value:
    connection_string: "${SOURCE_CONNECTION_STRING:sqlite:///default.db}"
```

## 🔄 Incremental Loading

The pipeline supports multiple incremental loading strategies:

### Timestamp-based Incremental
```yaml
incremental:
  enabled: true
  strategy: "timestamp"
  watermark_column: "UpdatedDate"
  initial_value: "2020-01-01T00:00:00"
```

### Sequence-based Incremental
```yaml
incremental:
  enabled: true
  strategy: "sequence"
  watermark_column: "Id"
  initial_value: 0
```

### Custom Incremental
```yaml
incremental:
  enabled: true
  strategy: "custom"
  watermark_column: "CustomField"
  initial_value: "custom_value"
```

## ✅ Data Verification

Configure comprehensive data verification:

```yaml
verification:
  enabled: true
  tolerance: 0                    # Allowed row count difference
  tables: ["Users", "Orders"]     # Tables to verify (optional)
  
  # Custom verification queries
  custom_checks:
    no_negative_amounts: "SELECT COUNT(*) FROM orders WHERE amount < 0"
    valid_email_format: "SELECT COUNT(*) FROM users WHERE email NOT LIKE '%@%'"
```

## 📊 Logging and Monitoring

Configure structured logging:

```yaml
logging:
  level: "INFO"                           # DEBUG|INFO|WARNING|ERROR|CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/pipeline.log"          # File logging (optional)
  max_file_size: 10485760                 # 10MB
  backup_count: 5                         # Rotate log files
```

## 🛠️ CLI Reference

### Main Commands

```bash
# Run pipeline
python run_pipeline.py run [options]

# Validate configuration
python run_pipeline.py validate [options]

# Show statistics
python run_pipeline.py stats [options]
```

### Global Options

- `--config, -c`: Configuration file (default: pipeline_config.yaml)
- `--config-dir`: Configuration directory (default: config/)
- `--environment, -e`: Environment configuration (dev, prod, etc.)

### Run Command Options

- `--tables, -t`: Specific tables to process
- `--output, -o`: Save results to JSON file

### Examples

```bash
# Basic usage
python run_pipeline.py run

# With environment
python run_pipeline.py run --environment dev

# Specific tables
python run_pipeline.py run --tables Users Orders

# Save results
python run_pipeline.py run --output results.json

# Custom config
python run_pipeline.py run --config custom.yaml --environment prod
```

## 🧪 Testing

The configuration system integrates with the existing test framework:

```bash
# Run tests with new configuration
make test

# Test with specific environment
make pipeline-run-test

# Validate test configuration
docker exec dlt-runner python /app/run_pipeline.py validate --environment test
```

## 🔧 Development

### Adding New Features

1. **Configuration**: Add new settings to `config_models.py`
2. **Processing**: Implement logic in appropriate processor
3. **Validation**: Add validation rules to Pydantic models
4. **Testing**: Add tests for new functionality

### Debugging

```bash
# Access container shell
make shell

# Check configuration
python /app/run_pipeline.py validate --environment dev

# View logs with debug level
python /app/run_pipeline.py run --environment dev  # (if dev config has DEBUG level)

# Test single table
python /app/run_pipeline.py run --tables MyTable --environment dev
```

## 📚 Migration from Legacy Script

The new configuration system is backward compatible. To migrate:

1. **Create Configuration**: Convert command-line arguments to YAML config
2. **Environment Variables**: Use same connection string environment variables
3. **Test**: Validate with `make pipeline-validate`
4. **Run**: Use new commands instead of legacy ones

### Legacy vs New Commands

| Legacy | New Configuration-Driven |
|--------|--------------------------|
| `make test-copy` | `make pipeline-run` |
| `make test-users` | `make pipeline-run-users` |
| `make verify` | Built into pipeline with `verification.enabled: true` |

## 🆘 Troubleshooting

### Common Issues

1. **Configuration Validation Errors**
   ```bash
   python /app/run_pipeline.py validate
   ```

2. **Environment Variable Issues**
   ```bash
   # Check if variables are set
   docker exec dlt-runner env | grep CONNECTION_STRING
   ```

3. **Table Not Found Errors**
   ```bash
   # Check table configuration
   python /app/run_pipeline.py stats
   ```

4. **Incremental Loading Issues**
   - Verify watermark column exists
   - Check initial_value format
   - Ensure column has appropriate index

### Debug Mode

Enable debug logging in your environment configuration:

```yaml
logging:
  level: "DEBUG"
  file_path: "logs/debug.log"
```

## 🔮 Future Enhancements

Planned improvements include:

- **Data Quality Rules**: Built-in data validation rules
- **Performance Optimization**: Automatic chunking optimization
- **State Management**: Persistent state for resumable operations
- **Parallel Processing**: Multi-table parallel execution
- **Schema Evolution**: Automatic schema change detection
- **Notification System**: Alert integration for pipeline status