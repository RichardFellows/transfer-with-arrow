# Transfer with Arrow

A configuration-driven data migration project that transfers reporting database tables from a source MSSQL database to a destination MSSQL database using the DLT (Data Loading Tool) framework with PyArrow backend and flexible YAML configuration.

## Overview

This project demonstrates a complete, enterprise-ready data pipeline solution using modern tools:
- **🎯 Configuration-Driven Architecture** with YAML-based pipeline definitions
- **🔧 Environment Support** for dev/staging/prod deployments
- **⚡ Advanced Features** including incremental loading, data verification, and monitoring
- **🗂️ Two-Stage Pipeline Architecture** with parquet intermediate layer for extract → load workflows
- **DLT (Data Loading Tool)** for efficient data extraction and loading
- **PyArrow** backend for high-performance data processing with parquet file format
- **Docker** for containerized, reproducible environments
- **MSSQL Server** as both source and destination databases
- **Comprehensive testing** with both unit and integration tests

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source DB     │    │   DLT Runner    │    │ Destination DB  │
│                 │    │                 │    │                 │
│ ReportingDB     │───▶│ Configuration-  │───▶│   TargetDB      │
│ Database        │    │ Driven Pipeline │    │                 │
│ (Port 1433)     │    │ PyArrow Backend │    │ (Port 1434)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### 1. Setup Environment
```bash
# Start all containers and setup databases
make setup
```

### 2. Run Data Migration
```bash
# Run pipeline with default configuration
make pipeline-run

# Run with development environment settings
make pipeline-run-dev

# Run specific tables only
make reporting-client-sync
```

### 3. Validate and Monitor
```bash
# Validate configuration
make pipeline-validate

# Show pipeline statistics
make pipeline-stats

# View detailed logs
make logs
```

## Commands Reference

### Environment Management
- `make up` - Start all Docker containers
- `make down` - Stop all Docker containers  
- `make setup` - Setup databases and create reporting tables
- `make clean` - Stop and remove all containers and volumes

### Data Pipeline
- `make pipeline-run` - Run pipeline with default configuration
- `make pipeline-run-dev` - Run pipeline with development environment settings
- `make reporting-client-sync` - Run Reporting_Client pipeline
- `make pipeline-validate` - Validate pipeline configuration
- `make pipeline-stats` - Show pipeline statistics and table information
- `make pipeline-help` - Show detailed CLI help

### Two-Stage Pipeline Operations
- **Extract Phase**: `docker exec dlt-runner python /app/run_pipeline.py extract [options]`
- **Load Phase**: `docker exec dlt-runner python /app/run_pipeline.py load [options]`
- **Archive Management**: `docker exec dlt-runner python /app/run_pipeline.py archive [action] [options]`
- **Pipeline Modes**: `docker exec dlt-runner python /app/run_pipeline.py run --mode [direct|extract-only|load-only|two-stage]`

### Common Aliases
- `make test-copy` - Run full pipeline (alias for pipeline-run)
- `make reporting-scd2-sync` - Run Reporting_Client_SCD2 pipeline
- `make test-incremental` - Run incremental loading example
- `make verify` - Run pipeline with verification (alias for pipeline-run)

### Development
- `make logs` - Show container logs
- `make shell` - Access DLT runner container shell
- `make sql-source` - Connect to source database CLI
- `make sql-dest` - Connect to destination database CLI

### Testing
- `make test` - Run all tests (unit + integration)
- `make test-unit` - Run only unit tests (fast, no database required)
- `make test-integration` - Run only integration tests (requires test databases)
- `make test-coverage` - Run tests with coverage report
- `make test-clean` - Clean test containers and volumes
- `make test-shell` - Start test container shell for debugging

## Configuration-Driven Pipeline

The pipeline system provides advanced configuration capabilities through YAML files:

### Core Features
- **🎯 YAML Configuration**: Complete pipeline definition in `dlt_scripts/config/pipeline_config.yaml`
- **🔧 Environment Support**: Environment-specific configurations (dev/staging/prod) with overrides
- **⚡ Advanced Incremental Loading**: Multiple strategies (timestamp, sequence, custom) per table
- **✅ Data Verification**: Built-in verification with custom checks and tolerance settings
- **📊 Comprehensive Logging**: Structured logging with progress tracking and monitoring
- **🔍 Schema Validation**: Pydantic-based configuration validation with detailed error reporting
- **🗂️ Two-Stage Architecture**: Extract → Parquet Archive → Load workflow with batch management

### Pipeline Modes
The system supports four execution modes:

1. **DIRECT** (Default): Traditional direct database-to-database transfer
2. **EXTRACT_ONLY**: Extract data to parquet files in archive directory
3. **LOAD_ONLY**: Load data from existing parquet files to destination
4. **TWO_STAGE**: Complete extract → load workflow with intermediate parquet storage

### Default Configuration
- **Backend**: PyArrow for efficient data processing
- **File Format**: Parquet for optimized storage and compression
- **Chunk Size**: 10,000 rows per chunk (configurable per environment)
- **Default Tables**: Reporting_Client, Reporting_Client_SCD2
- **Write Modes**: Replace, Append, Merge (configurable per table)
- **Connection Management**: Environment variable substitution with secure credential handling
- **Archive Directory**: `/app/data/archive/` for parquet files in two-stage workflows
- **Batch Management**: Automatic timestamped batch organization with cleanup capabilities

### Direct Pipeline Usage
You can run the pipeline directly with advanced options:

```bash
docker exec dlt-runner python /app/run_pipeline.py [command] [options]
```

**Commands:**
- `run` - Execute the data migration pipeline
- `validate` - Validate configuration without running
- `stats` - Show configuration overview and statistics

**Options:**
- `--config, -c` - Configuration file (default: pipeline_config.yaml)
- `--environment, -e` - Environment configuration (dev, staging, prod, etc.)
- `--tables, -t` - Specific tables to process
- `--output, -o` - Save results to JSON file

**Examples:**
```bash
# Run with default configuration (direct mode)
docker exec dlt-runner python /app/run_pipeline.py run

# Run in two-stage mode (extract → load)
docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage

# Extract-only operation
docker exec dlt-runner python /app/run_pipeline.py extract --tables Reporting_Client
docker exec dlt-runner python /app/run_pipeline.py run --mode extract-only

# Load from latest archived data
docker exec dlt-runner python /app/run_pipeline.py load --batch latest
docker exec dlt-runner python /app/run_pipeline.py run --mode load-only

# Load specific batch
docker exec dlt-runner python /app/run_pipeline.py load --batch 20250818_120000

# Load batches from date range
docker exec dlt-runner python /app/run_pipeline.py load --date-range 20250815-20250817

# Archive management
docker exec dlt-runner python /app/run_pipeline.py archive list --last 10
docker exec dlt-runner python /app/run_pipeline.py archive stats
docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than 30d

# Run with development environment
docker exec dlt-runner python /app/run_pipeline.py run --environment dev

# Validate production configuration
docker exec dlt-runner python /app/run_pipeline.py validate --environment prod

# Save results to file
docker exec dlt-runner python /app/run_pipeline.py run --output results.json
```

## Configuration Guide

### Basic Configuration Structure
```yaml
pipeline:
  name: "my_migration"
  dataset_name: "target_data"
  chunk_size: 10000
  pipeline_mode: "two-stage"  # direct, extract-only, load-only, two-stage
  backend: "pyarrow"
  loader_file_format: "parquet"

# Archive configuration for two-stage workflows
archive:
  storage_path: "/data/parquet_archive"
  manifest_path: "/data/parquet_archive/manifest.json"
  retention_days: 90
  compression: "snappy"

connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
  destination:
    connection_string: "${DEST_CONNECTION_STRING}"

tables:
  Reporting_Client:
    source_table: "dbo.Reporting_Client"
    disposition: "append"
    incremental:
      enabled: true
      strategy: "sequence"
      watermark_column: "SystemCalendarID"
    enabled: true

verification:
  enabled: true
  tolerance: 0

logging:
  level: "INFO"
```

### Environment-Specific Configurations
Create environment-specific overrides in `dlt_scripts/config/environments/`:
- `dev.yaml` - Development settings
- `prod.yaml` - Production settings
- `test.yaml` - Test environment settings

See `dlt_scripts/README.md` for comprehensive configuration documentation.

## Testing Framework

### Unit Tests
Fast tests with mocked dependencies:
- Configuration system validation
- Pipeline component logic testing
- No external dependencies required
- Run with: `make test-unit`

### Integration Tests
End-to-end testing with real databases:
- Use SQL Server containers via testcontainers
- Test complete configuration-driven migration workflows
- Verify data integrity and pipeline functionality
- Run with: `make test-integration`

### Test Dependencies
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `testcontainers` - Docker container management for tests
- `pydantic` - Configuration validation testing
- Coverage reporting with `pytest-cov`

## Database Configuration

- **Source Database**: Port 1433, ReportingDB with client tables
- **Destination Database**: Port 1434, TargetDB (created automatically)
- **Authentication**: SA user with password `SecurePass123`
- **SSL/Encryption**: Configured with TrustServerCertificate for development

## Project Structure

```
transfer-with-arrow/
├── dlt_scripts/              # Pipeline system
│   ├── config/              # Configuration files
│   │   ├── pipeline_config.yaml      # Main configuration
│   │   └── environments/             # Environment-specific configs
│   │       ├── dev.yaml
│   │       ├── prod.yaml
│   │       └── test.yaml
│   ├── src/                 # Source code
│   │   ├── pipeline/        # Core pipeline components
│   │   └── utils/           # Utility modules
│   ├── run_pipeline.py      # Main CLI entry point
│   ├── requirements.txt     # Python dependencies
│   ├── requirements-test.txt # Test dependencies
│   ├── README.md           # Detailed configuration guide
│   └── .dlt/               # DLT configuration files
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures and utilities
├── scripts/                # Database setup scripts
├── docker-compose.yaml     # Main environment
├── docker-compose.test.yaml # Test environment
├── Dockerfile.runner       # DLT runner container
├── Dockerfile.test        # Test container
├── Makefile              # Convenience commands
└── README.md             # This file
```

## Development

### Local Development Setup
1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Install dependencies: `pip install -r dlt_scripts/requirements.txt`
4. Install test dependencies: `pip install -r dlt_scripts/requirements-test.txt`
5. Run tests: `pytest tests/`

### Adding New Tables
1. Update the table configuration in `dlt_scripts/config/pipeline_config.yaml`
2. Configure incremental loading, verification, and other settings as needed
3. Add corresponding test data in integration test fixtures
4. Update documentation

### Extending Pipeline
- Modify configuration files for new data sources and transformations
- Add custom verification checks in configuration
- Update environment-specific settings for different deployments
- Extend Pydantic models for new configuration options

## Troubleshooting

### Common Issues

**Container startup fails:**
```bash
# Check container logs
make logs

# Restart environment
make clean && make setup
```

**Configuration validation errors:**
```bash
# Validate current configuration
make pipeline-validate

# Check specific environment
docker exec dlt-runner python /app/run_pipeline.py validate --environment dev
```

**Database connection errors:**
```bash
# Verify databases are running
docker ps

# Check database connectivity
make sql-source
make sql-dest
```

**Test failures:**
```bash
# Run specific test category
make test-unit    # For quick feedback
make test-integration  # For full validation

# Get detailed test output
make test-shell
pytest tests/ -v --tb=long
```

**Performance issues:**
- Ensure project is on native filesystem (not mounted from Windows)
- Adjust `chunk_size` in configuration for your data size
- Monitor Docker resource allocation
- Use environment-specific configurations to optimize for different deployments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Update configuration documentation as needed
6. Submit a pull request

## License

This project is provided as-is for educational and demonstration purposes.