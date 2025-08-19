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

**Choose your development approach:**
- 🐳 **[Docker Setup](#quick-start)** - Containerized environment (recommended for production)
- 🖥️ **[Local Development](#-local-development-setup-alternative-to-docker)** - Direct Python execution with `uv`

### Prerequisites (Docker)
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

## 🚀 Developer Quick Start: Two-Stage Pipeline

This section provides step-by-step instructions for developers to quickly set up and test the two-stage pipeline with SQL Server Windows Authentication.

### Prerequisites

1. **SQL Server Access**: Ensure you have access to both source and destination SQL Server instances
2. **ODBC Driver**: Install [Microsoft ODBC Driver 18 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
3. **Windows Authentication**: Ensure your Windows account has access to both SQL Server instances
4. **Docker**: Docker Desktop installed and running

### Step 1: Environment Setup

Create environment variables for your SQL Server connections:

**Windows (PowerShell):**
```powershell
# Set environment variables for SQL Server connections
$env:SOURCE_CONNECTION_STRING = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\MAIN_INSTANCE;DATABASE=SourceDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
$env:DEST_CONNECTION_STRING = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=DESTDB\VIRT_INSTANCE;DATABASE=DestDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
```

**Linux/macOS (Bash):**
```bash
export SOURCE_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\\MAIN_INSTANCE;DATABASE=SourceDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
export DEST_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=DESTDB\\VIRT_INSTANCE;DATABASE=DestDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
```

### Step 2: Create Developer Configuration

Create a new configuration file `dlt_scripts/config/environments/developer.yaml`:

```yaml
# Developer environment configuration for two-stage pipeline testing
# File: dlt_scripts/config/environments/developer.yaml

pipeline:
  name: "developer_two_stage_test"
  dataset_name: "DestDatabase"  # Your destination database name
  chunk_size: 1000              # Smaller chunks for testing
  pipeline_mode: "two-stage"    # Enable two-stage functionality
  backend: "pyarrow"
  loader_file_format: "parquet"
  naming_convention: "direct"   # Preserve original column names

# Archive configuration for two-stage workflow
archive:
  storage_path: "/app/data/archive"           # Docker container path
  manifest_path: "/app/data/manifests"       # Manifest storage
  retention_days: 7                          # Short retention for testing
  compression: "snappy"                      # Fast compression

connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema: "dbo"
    timeout: 60
  destination:
    connection_string: "${DEST_CONNECTION_STRING}"
    schema: "dbo"
    timeout: 60

tables:
  # Single table configuration for testing
  Reporting_Client:
    source_table: "dbo.Reporting_Client"
    destination_table: "Reporting_Client"    # Keep original name
    disposition: "append"
    incremental:
      enabled: true
      strategy: "sequence"
      watermark_column: "SystemCalendarID"
      initial_value: 0
    enabled: true
    primary_key: ["RecordID"]

# Disable verification for faster testing (optional)
verification:
  enabled: false

logging:
  level: "DEBUG"                             # Verbose logging for development
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Step 3: Start Environment

```bash
# Start the Docker environment
make up

# Verify containers are running
docker ps
```

### Step 4: Test Two-Stage Pipeline

#### Option A: Complete Two-Stage Workflow
```bash
# Run complete extract → load workflow
docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage --environment developer

# Alternative: Use environment config that sets mode automatically
docker exec dlt-runner python /app/run_pipeline.py run --environment developer
```

#### Option B: Separate Extract and Load Steps
```bash
# Step 1: Extract data to parquet archive
docker exec dlt-runner python /app/run_pipeline.py extract --environment developer

# Step 2: View archived data
docker exec dlt-runner python /app/run_pipeline.py archive list

# Step 3: Load from archive
docker exec dlt-runner python /app/run_pipeline.py load --batch latest --environment developer
```

### Step 5: Monitor and Verify

```bash
# Check archive statistics
docker exec dlt-runner python /app/run_pipeline.py archive stats --environment developer

# View detailed batch information
docker exec dlt-runner python /app/run_pipeline.py archive info BATCH_ID --environment developer

# Check container logs
docker logs dlt-runner

# Access container shell for debugging
docker exec -it dlt-runner bash
```

### Connection String Reference

For different authentication methods:

**Windows Authentication (Recommended):**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\MAIN_INSTANCE;DATABASE=SourceDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes
```

**SQL Server Authentication:**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\MAIN_INSTANCE;DATABASE=SourceDatabase;UID=username;PWD=password;TrustServerCertificate=yes;Encrypt=yes
```

**Connection String Parameters:**
- `TrustServerCertificate=yes` - Accepts self-signed certificates
- `Encrypt=yes` - Enables encryption (required for ODBC Driver 18)
- `Trusted_Connection=yes` - Uses Windows Authentication
- `ConnectRetryCount=3` - Connection retry attempts (optional)
- `ConnectRetryInterval=10` - Retry interval in seconds (optional)

### Troubleshooting

**Common Issues:**

1. **Connection Timeout:**
   ```bash
   # Increase timeout in configuration
   timeout: 120
   ```

2. **Archive Permission Issues:**
   ```bash
   # Check archive directory permissions
   docker exec dlt-runner ls -la /app/data/
   ```

3. **ODBC Driver Issues:**
   ```bash
   # Verify ODBC driver in container
   docker exec dlt-runner odbcinst -q -d
   ```

4. **Windows Authentication Issues:**
   - Ensure Docker Desktop is running with Windows authentication enabled
   - Verify your Windows account has SQL Server access
   - Test connection outside Docker first

### Performance Tuning

For large tables, adjust these settings in your developer config:

```yaml
pipeline:
  chunk_size: 5000              # Increase for better performance

archive:
  compression: "lz4"            # Faster compression for testing
  
connections:
  source:
    timeout: 300                # Longer timeout for large queries
```

This setup provides a complete testing environment for the two-stage pipeline with your specific SQL Server configuration.

## 🖥️ Local Development Setup (Alternative to Docker)

For developers who prefer to run locally without Docker, you can use `uv` for fast Python environment management.

### Prerequisites for Local Development

1. **Python 3.11+**: Ensure Python 3.11 or later is installed
2. **uv**: Install [uv](https://docs.astral.sh/uv/) for fast package management
3. **ODBC Driver**: Install [Microsoft ODBC Driver 18 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
4. **SQL Server Access**: Ensure your Windows account has access to both SQL Server instances

### Step 1: Local Environment Setup

```bash
# Navigate to the dlt_scripts directory
cd dlt_scripts

# Create virtual environment with uv
uv venv --python 3.11

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Optional: Install test dependencies if you want to run tests
uv pip install -r requirements-test.txt
```

### Step 2: Set Environment Variables

**Windows (PowerShell):**
```powershell
# Set environment variables for SQL Server connections
$env:SOURCE_CONNECTION_STRING = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\MAIN_INSTANCE;DATABASE=SourceDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
$env:DEST_CONNECTION_STRING = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=DESTDB\VIRT_INSTANCE;DATABASE=DestDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
```

**Linux/macOS (Bash):**
```bash
export SOURCE_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=SOURCEDB\\MAIN_INSTANCE;DATABASE=SourceDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
export DEST_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=DESTDB\\VIRT_INSTANCE;DATABASE=DestDatabase;Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=yes"
```

### Step 3: Create Local Developer Configuration

Create `config/environments/local.yaml`:

```yaml
# Local development environment configuration
# File: dlt_scripts/config/environments/local.yaml

pipeline:
  name: "local_two_stage_test"
  dataset_name: "DestDatabase"  # Your destination database name
  chunk_size: 1000              # Smaller chunks for testing
  pipeline_mode: "two-stage"    # Enable two-stage functionality
  backend: "pyarrow"
  loader_file_format: "parquet"
  naming_convention: "direct"   # Preserve original column names

# Archive configuration for local two-stage workflow
archive:
  storage_path: "./data/archive"              # Local directory path
  manifest_path: "./data/manifests"          # Local manifest storage
  retention_days: 7                          # Short retention for testing
  compression: "snappy"                      # Fast compression

connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema: "dbo"
    timeout: 60
  destination:
    connection_string: "${DEST_CONNECTION_STRING}"
    schema: "dbo"
    timeout: 60

tables:
  # Single table configuration for testing
  Reporting_Client:
    source_table: "dbo.Reporting_Client"
    destination_table: "Reporting_Client"    # Keep original name
    disposition: "append"
    incremental:
      enabled: true
      strategy: "sequence"
      watermark_column: "SystemCalendarID"
      initial_value: 0
    enabled: true
    primary_key: ["RecordID"]

# Disable verification for faster testing (optional)
verification:
  enabled: false

logging:
  level: "DEBUG"                             # Verbose logging for development
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "./logs/local_pipeline.log"    # Local log file
```

### Step 4: Create Local Directories

```bash
# Create necessary directories for local development
mkdir -p data/archive
mkdir -p data/manifests  
mkdir -p logs

# Verify directory structure
ls -la data/
```

### Step 5: Run Pipeline Locally

Now you can run the pipeline directly without Docker:

```bash
# Navigate to dlt_scripts directory (if not already there)
cd dlt_scripts

# Activate virtual environment (if not already active)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Run complete two-stage workflow
python run_pipeline.py run --environment local

# Or run separate steps:
# Extract data to parquet archive
python run_pipeline.py extract --environment local

# View archived data
python run_pipeline.py archive list

# Load from archive
python run_pipeline.py load --batch latest --environment local
```

### Step 6: Local Development Commands

```bash
# Check archive statistics
python run_pipeline.py archive stats --environment local

# View detailed batch information
python run_pipeline.py archive info BATCH_ID --environment local

# Validate configuration
python run_pipeline.py validate --environment local

# Show pipeline statistics
python run_pipeline.py stats --environment local

# Run with specific tables only
python run_pipeline.py run --environment local --tables Reporting_Client

# Save results to JSON file
python run_pipeline.py run --environment local --output results.json
```

### Local vs Docker Comparison

| Aspect | Local Development | Docker Development |
|--------|-------------------|-------------------|
| **Setup Time** | ⚡ Fast with `uv` | 🐌 Docker image build/pull |
| **Resource Usage** | 💚 Lower memory/CPU | 📈 Higher overhead |
| **Debugging** | 🛠️ Direct IDE integration | 🔍 Container debugging |
| **File Access** | 📁 Direct filesystem | 🗂️ Volume mounts |
| **Isolation** | ⚠️ Uses system resources | 🔒 Full isolation |
| **Dependencies** | 📦 Manual ODBC setup | ✅ Pre-configured |

### Local Development Tips

1. **Performance**: Local execution is typically faster due to no containerization overhead
2. **Debugging**: Use your favorite IDE/debugger directly on the code
3. **File Paths**: Archive and manifest paths use local filesystem (`./data/`)
4. **Logs**: Log files are written to `./logs/` for easy access
5. **Hot Reloading**: Make code changes and test immediately without rebuilds

### Troubleshooting Local Setup

**ODBC Driver Issues:**
```bash
# Test ODBC driver installation
python -c "import pyodbc; print(pyodbc.drivers())"
```

**Connection Testing:**
```bash
# Test connections before running pipeline
python run_pipeline.py validate --environment local
```

**Virtual Environment Issues:**
```bash
# Recreate environment if needed
rm -rf .venv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

This local setup provides the same functionality as Docker but with faster iteration cycles for development.

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