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
- **Command Line Tools** (choose one):
  - 🐧 **Make** (Linux/macOS/WSL) - Standard Unix build tool
  - 🟦 **PowerShell** (Windows) - Use included `scripts.ps1`
  - ⬛ **CMD** (Windows) - Use included `scripts.cmd`

### 1. Setup Environment

**Linux/macOS/WSL (Make):**
```bash
# Start all containers and setup databases
make setup
```

**Windows PowerShell:**
```powershell
# Import PowerShell functions
. .\scripts.ps1

# Start all containers and setup databases
Setup-Environment
```

**Windows CMD:**
```cmd
# Start all containers and setup databases
scripts setup
```

### 2. Run Data Migration

**Linux/macOS/WSL (Make):**
```bash
# Run pipeline with default configuration
make pipeline-run

# Run with development environment settings
make pipeline-run-dev

# Run specific tables only
make reporting-client-sync
```

**Windows PowerShell:**
```powershell
# Run pipeline with default configuration
Run-Pipeline

# Run with development environment settings
Run-PipelineDev

# Run specific tables only
Sync-ReportingClient
```

**Windows CMD:**
```cmd
# Run pipeline with default configuration
scripts pipeline-run

# Run with development environment settings
scripts pipeline-run-dev

# Run specific tables only
scripts reporting-client-sync
```

### 3. Validate and Monitor

**Linux/macOS/WSL (Make):**
```bash
# Validate configuration
make pipeline-validate

# Show pipeline statistics
make pipeline-stats

# View detailed logs
make logs
```

**Windows PowerShell:**
```powershell
# Validate configuration
Validate-Pipeline

# Show pipeline statistics
Show-PipelineStats

# View detailed logs
Show-Logs
```

**Windows CMD:**
```cmd
# Validate configuration
scripts pipeline-validate

# Show pipeline statistics
scripts pipeline-stats

# View detailed logs
scripts logs
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

## 🪟 Windows Scripts (Alternative to Make)

For Windows developers who don't have Make installed, we provide PowerShell and CMD equivalents for all Makefile commands.

### PowerShell Scripts (`scripts.ps1`)

**Setup:**
```powershell
# Import the PowerShell functions (run once per session)
. .\scripts.ps1

# Show all available commands
Show-Help
```

**Key PowerShell Functions:**
```powershell
# Environment Management
Setup-Environment         # Start and configure Docker environment
Start-Environment         # Start Docker containers
Stop-Environment          # Stop Docker containers
Clean-Environment         # Remove containers and volumes

# Pipeline Operations  
Run-Pipeline              # Run default pipeline
Run-PipelineDev          # Run with dev environment
Sync-ReportingClient     # Sync specific table
Validate-Pipeline        # Validate configuration
Show-PipelineStats       # Show statistics

# Two-Stage Operations
Extract-Data -Tables @("Reporting_Client") -Environment "dev"
Load-Data -Batch "latest" -Environment "dev"
Show-ArchiveList -Last 10
Show-ArchiveStats
Clean-Archive -OlderThan "7d"

# Local Development
Setup-LocalEnvironment   # Setup local Python environment
Run-LocalPipeline -Environment "local" -Mode "two-stage"
Extract-LocalData -Environment "local"
Load-LocalData -Environment "local" -Batch "latest"
Test-LocalConnection     # Test ODBC drivers

# Development Tools
Show-Logs               # View container logs
Enter-Shell            # Access container shell
Connect-SourceDB       # Connect to source database
Connect-DestDB         # Connect to destination database
```

### CMD Batch Scripts (`scripts.cmd`)

**Usage:**
```cmd
# Show all available commands
scripts help

# Basic operations
scripts setup              # Setup environment
scripts pipeline-run       # Run pipeline
scripts pipeline-validate  # Validate config

# Two-stage operations
scripts extract            # Extract with default environment
scripts extract dev       # Extract with dev environment
scripts load              # Load latest batch
scripts load 20240818_120000  # Load specific batch

# Archive management
scripts archive-list       # List last 10 batches
scripts archive-list 20   # List last 20 batches
scripts archive-stats      # Show archive statistics
scripts archive-cleanup    # Clean with default retention (30d)
scripts archive-cleanup 7d # Clean batches older than 7 days

# Local development
scripts local-setup        # Setup local environment
scripts local-run          # Run locally
scripts local-extract      # Extract locally
scripts local-load         # Load locally
scripts local-test-connection  # Test ODBC

# Development tools
scripts logs               # View logs
scripts shell             # Access shell
scripts sql-source        # Connect to source DB
scripts sql-dest          # Connect to destination DB
```

### Comparison: Make vs PowerShell vs CMD

| Feature | Make | PowerShell | CMD |
|---------|------|------------|-----|
| **Platform** | ✅ Linux/macOS/WSL | 🟦 Windows | ⬛ Windows |
| **Syntax** | `make command` | `Function-Name` | `scripts command` |
| **Parameters** | `make cmd VAR=value` | `-Parameter value` | `scripts cmd param` |
| **Help** | `make help` | `Show-Help` | `scripts help` |
| **Tab Completion** | ✅ Yes | ✅ Yes | ❌ No |
| **Advanced Features** | ✅ Variables, conditionals | ✅ Rich parameters, objects | ⚠️ Basic scripting |

### Examples for Each Platform

**Setup and Run Pipeline:**

**Make:**
```bash
make setup && make pipeline-run
```

**PowerShell:**
```powershell
Setup-Environment
Run-Pipeline
```

**CMD:**
```cmd
scripts setup && scripts pipeline-run
```

**Two-Stage Workflow:**

**Make:**
```bash
make pipeline-extract && make pipeline-load
```

**PowerShell:**
```powershell
Extract-Data -Environment "dev"
Load-Data -Batch "latest" -Environment "dev"
```

**CMD:**
```cmd
scripts extract dev
scripts load latest
```

**Local Development Setup:**

**Make:**
```bash
cd dlt_scripts
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**PowerShell:**
```powershell
Setup-LocalEnvironment  # Handles everything automatically
```

**CMD:**
```cmd
scripts local-setup
```

### Windows-Specific Features

**PowerShell Advantages:**
- Rich parameter validation and type safety
- Object-oriented output and pipeline support
- Advanced error handling and progress indicators
- Tab completion for function names and parameters
- Colored output for better visibility

**CMD Advantages:**
- Available on all Windows systems (no PowerShell required)
- Simple syntax familiar to batch file users
- Fast execution with minimal overhead
- Compatible with legacy Windows environments

### Installation and Usage

**PowerShell (Recommended for Windows):**
```powershell
# Navigate to project directory
cd transfer-with-arrow

# Import functions (do this once per PowerShell session)
. .\scripts.ps1

# Use any function
Setup-Environment
```

**CMD (Legacy Windows Support):**
```cmd
# Navigate to project directory  
cd transfer-with-arrow

# Use any command
scripts setup
scripts pipeline-run
```

Both Windows alternatives provide the same functionality as Make, ensuring that Windows developers have a seamless experience regardless of their preferred command line environment.

## ☸️ OpenShift/Kubernetes Deployment

Deploy the two-stage pipeline in OpenShift or Kubernetes environments for production-scale data processing with enterprise features like scalability, monitoring, and security.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenShift/Kubernetes Cluster                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   ConfigMaps    │    │     Secrets     │    │ Persistent   │ │
│  │                 │    │                 │    │  Volumes     │ │
│  │ • Pipeline      │    │ • DB Credentials│    │              │ │
│  │   Config        │    │ • SSL Certs     │    │ • Archive    │ │
│  │ • Environment   │    │ • Service       │    │   Storage    │ │
│  │   Settings      │    │   Accounts      │    │ • Manifests  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                      │      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Pipeline Jobs/CronJobs                    │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │  Extract    │  │    Load     │  │    Two-Stage        │ │ │
│  │  │    Job      │  │    Job      │  │     Workflow        │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • On-demand │  │ • Scheduled │  │ • Extract → Load    │ │ │
│  │  │ • Scheduled │  │ • On-demand │  │ • Full Pipeline     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                       │                      │      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    External Services                       │ │
│  │                                                             │ │
│  │  ┌─────────────┐                           ┌─────────────┐ │ │
│  │  │   Source    │                           │ Destination │ │ │
│  │  │  Database   │◄──────────────────────────┤  Database   │ │ │
│  │  │             │                           │             │ │ │
│  │  │ • SQL Server│                           │ • SQL Server│ │ │
│  │  │ • Oracle    │                           │ • PostgreSQL│ │ │
│  │  │ • PostgreSQL│                           │ • BigQuery  │ │ │
│  │  └─────────────┘                           └─────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Prerequisites

1. **OpenShift/Kubernetes Cluster**: Access to cluster with appropriate permissions
2. **CLI Tools**: `oc` (OpenShift) or `kubectl` (Kubernetes)
3. **Container Registry**: Access to push custom images (optional)
4. **Storage**: Persistent storage for archive and manifest data
5. **Database Access**: Network connectivity to source and destination databases

### Deployment Methods

#### Method 1: Using the Pre-built Container Image

**Create Namespace/Project:**
```bash
# OpenShift
oc new-project data-pipeline

# Kubernetes  
kubectl create namespace data-pipeline
kubectl config set-context --current --namespace=data-pipeline
```

**Deploy Base Resources:**
```yaml
# File: k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: data-pipeline
  labels:
    name: data-pipeline
---
# File: k8s/storage.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-archive-pvc
  namespace: data-pipeline
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd  # Adjust for your cluster
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-manifests-pvc
  namespace: data-pipeline
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

**Create Configuration:**
```yaml
# File: k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-config
  namespace: data-pipeline
data:
  pipeline_config.yaml: |
    pipeline:
      name: "k8s_data_pipeline"
      dataset_name: "DestinationDB"
      chunk_size: 10000
      pipeline_mode: "two-stage"
      backend: "pyarrow"
      loader_file_format: "parquet"
      naming_convention: "direct"

    archive:
      storage_path: "/data/archive"
      manifest_path: "/data/manifests"
      retention_days: 30
      compression: "snappy"

    connections:
      source:
        connection_string: "${SOURCE_CONNECTION_STRING}"
        schema: "dbo"
        timeout: 300
      destination:
        connection_string: "${DEST_CONNECTION_STRING}"
        schema: "dbo"
        timeout: 300

    tables:
      Reporting_Client:
        source_table: "dbo.Reporting_Client"
        destination_table: "Reporting_Client"
        disposition: "append"
        incremental:
          enabled: true
          strategy: "sequence"
          watermark_column: "SystemCalendarID"
          initial_value: 0
        enabled: true
        primary_key: ["RecordID"]

    verification:
      enabled: true
      tolerance: 0

    logging:
      level: "INFO"
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      file_path: "/data/logs/pipeline.log"
```

**Create Secrets:**
```yaml
# File: k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: data-pipeline
type: Opaque
stringData:
  SOURCE_CONNECTION_STRING: "DRIVER={ODBC Driver 18 for SQL Server};SERVER=source-server;DATABASE=SourceDB;UID=username;PWD=password;TrustServerCertificate=yes;Encrypt=yes"
  DEST_CONNECTION_STRING: "DRIVER={ODBC Driver 18 for SQL Server};SERVER=dest-server;DATABASE=DestDB;UID=username;PWD=password;TrustServerCertificate=yes;Encrypt=yes"
```

**Deploy Pipeline Jobs:**
```yaml
# File: k8s/extract-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pipeline-extract
  namespace: data-pipeline
spec:
  template:
    metadata:
      labels:
        app: pipeline-extract
    spec:
      containers:
      - name: dlt-runner
        image: your-registry/transfer-with-arrow:latest
        command: ["python", "/app/run_pipeline.py"]
        args: ["extract", "--environment", "k8s"]
        envFrom:
        - secretRef:
            name: database-credentials
        volumeMounts:
        - name: config-volume
          mountPath: /app/config/environments
          readOnly: true
        - name: archive-storage
          mountPath: /data/archive
        - name: manifest-storage
          mountPath: /data/manifests
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: config-volume
        configMap:
          name: pipeline-config
      - name: archive-storage
        persistentVolumeClaim:
          claimName: pipeline-archive-pvc
      - name: manifest-storage
        persistentVolumeClaim:
          claimName: pipeline-manifests-pvc
      restartPolicy: OnFailure
      backoffLimit: 3
---
# File: k8s/load-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pipeline-load
  namespace: data-pipeline
spec:
  template:
    metadata:
      labels:
        app: pipeline-load
    spec:
      containers:
      - name: dlt-runner
        image: your-registry/transfer-with-arrow:latest
        command: ["python", "/app/run_pipeline.py"]
        args: ["load", "--batch", "latest", "--environment", "k8s"]
        envFrom:
        - secretRef:
            name: database-credentials
        volumeMounts:
        - name: config-volume
          mountPath: /app/config/environments
          readOnly: true
        - name: archive-storage
          mountPath: /data/archive
        - name: manifest-storage
          mountPath: /data/manifests
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: config-volume
        configMap:
          name: pipeline-config
      - name: archive-storage
        persistentVolumeClaim:
          claimName: pipeline-archive-pvc
      - name: manifest-storage
        persistentVolumeClaim:
          claimName: pipeline-manifests-pvc
      restartPolicy: OnFailure
      backoffLimit: 3
```

**Create Scheduled CronJobs:**
```yaml
# File: k8s/cronjobs.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pipeline-extract-daily
  namespace: data-pipeline
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: dlt-runner
            image: your-registry/transfer-with-arrow:latest
            command: ["python", "/app/run_pipeline.py"]
            args: ["extract", "--environment", "k8s"]
            envFrom:
            - secretRef:
                name: database-credentials
            volumeMounts:
            - name: config-volume
              mountPath: /app/config/environments
              readOnly: true
            - name: archive-storage
              mountPath: /data/archive
            - name: manifest-storage
              mountPath: /data/manifests
            resources:
              requests:
                memory: "2Gi"
                cpu: "1000m"
              limits:
                memory: "4Gi"
                cpu: "2000m"
          volumes:
          - name: config-volume
            configMap:
              name: pipeline-config
          - name: archive-storage
            persistentVolumeClaim:
              claimName: pipeline-archive-pvc
          - name: manifest-storage
            persistentVolumeClaim:
              claimName: pipeline-manifests-pvc
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pipeline-load-daily
  namespace: data-pipeline
spec:
  schedule: "0 3 * * *"  # Daily at 3 AM (after extract)
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: dlt-runner
            image: your-registry/transfer-with-arrow:latest
            command: ["python", "/app/run_pipeline.py"]
            args: ["load", "--batch", "latest", "--environment", "k8s"]
            envFrom:
            - secretRef:
                name: database-credentials
            volumeMounts:
            - name: config-volume
              mountPath: /app/config/environments
              readOnly: true
            - name: archive-storage
              mountPath: /data/archive
            - name: manifest-storage
              mountPath: /data/manifests
            resources:
              requests:
                memory: "2Gi"
                cpu: "1000m"
              limits:
                memory: "4Gi"
                cpu: "2000m"
          volumes:
          - name: config-volume
            configMap:
              name: pipeline-config
          - name: archive-storage
            persistentVolumeClaim:
              claimName: pipeline-archive-pvc
          - name: manifest-storage
            persistentVolumeClaim:
              claimName: pipeline-manifests-pvc
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pipeline-archive-cleanup
  namespace: data-pipeline
spec:
  schedule: "0 1 * * 0"  # Weekly on Sunday at 1 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: dlt-runner
            image: your-registry/transfer-with-arrow:latest
            command: ["python", "/app/run_pipeline.py"]
            args: ["archive", "cleanup", "--older-than", "30d"]
            envFrom:
            - secretRef:
                name: database-credentials
            volumeMounts:
            - name: config-volume
              mountPath: /app/config/environments
              readOnly: true
            - name: archive-storage
              mountPath: /data/archive
            - name: manifest-storage
              mountPath: /data/manifests
            resources:
              requests:
                memory: "1Gi"
                cpu: "500m"
              limits:
                memory: "2Gi"
                cpu: "1000m"
          volumes:
          - name: config-volume
            configMap:
              name: pipeline-config
          - name: archive-storage
            persistentVolumeClaim:
              claimName: pipeline-archive-pvc
          - name: manifest-storage
            persistentVolumeClaim:
              claimName: pipeline-manifests-pvc
          restartPolicy: OnFailure
```

#### Method 2: Building Custom Container Image

**Create Dockerfile for Kubernetes:**
```dockerfile
# File: Dockerfile.k8s
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY dlt_scripts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY dlt_scripts/ .

# Create data directories
RUN mkdir -p /data/archive /data/manifests /data/logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DLT_PROJECT_DIR=/app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app /data
USER appuser

# Default command
CMD ["python", "run_pipeline.py", "--help"]
```

**Build and Push Image:**
```bash
# Build image
docker build -f Dockerfile.k8s -t your-registry/transfer-with-arrow:latest .

# Push to registry (adjust for your registry)
docker push your-registry/transfer-with-arrow:latest
```

### Deployment Commands

**Deploy all resources:**
```bash
# Apply all configurations
kubectl apply -f k8s/

# Or for OpenShift
oc apply -f k8s/
```

**Manual job execution:**
```bash
# Run extract job manually
kubectl create job --from=cronjob/pipeline-extract-daily manual-extract-$(date +%Y%m%d%H%M%S)

# Run load job manually  
kubectl create job --from=cronjob/pipeline-load-daily manual-load-$(date +%Y%m%d%H%M%S)
```

### Monitoring and Management

**View job status:**
```bash
# List all jobs
kubectl get jobs

# Get job logs
kubectl logs job/pipeline-extract

# Get pod logs
kubectl logs -l app=pipeline-extract

# View CronJob status
kubectl get cronjobs
```

**Archive management:**
```bash
# Check archive statistics
kubectl exec -it $(kubectl get pods -l app=pipeline-extract -o jsonpath='{.items[0].metadata.name}') -- python run_pipeline.py archive stats

# List recent batches
kubectl exec -it deployment/pipeline-runner -- python run_pipeline.py archive list --last 10
```

### Security Best Practices

**1. Service Accounts and RBAC:**
```yaml
# File: k8s/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pipeline-service-account
  namespace: data-pipeline
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pipeline-role
  namespace: data-pipeline
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pipeline-role-binding
  namespace: data-pipeline
subjects:
- kind: ServiceAccount
  name: pipeline-service-account
  namespace: data-pipeline
roleRef:
  kind: Role
  name: pipeline-role
  apiGroup: rbac.authorization.k8s.io
```

**2. Network Policies:**
```yaml
# File: k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pipeline-network-policy
  namespace: data-pipeline
spec:
  podSelector:
    matchLabels:
      app: pipeline
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to: []  # Allow all outbound (for database connections)
  ingress: []  # No inbound connections needed
```

**3. Pod Security Standards:**
```yaml
# File: k8s/pod-security.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pipeline-pod
  namespace: data-pipeline
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: dlt-runner
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

### Scaling and Performance

**Horizontal Pod Autoscaler:**
```yaml
# File: k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pipeline-hpa
  namespace: data-pipeline
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pipeline-runner
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Production Considerations

**1. Resource Planning:**
- **CPU**: 1-2 cores per pipeline job
- **Memory**: 2-4GB per job (depending on chunk size)
- **Storage**: Plan for 2-3x data size for archive storage
- **Network**: Consider database connection limits

**2. High Availability:**
- Use ReadWriteMany storage for shared archive access
- Deploy across multiple availability zones
- Configure pod disruption budgets
- Implement health checks and readiness probes

**3. Backup and Recovery:**
- Regular backup of archive and manifest storage
- Database backup coordination with pipeline schedules
- Disaster recovery procedures
- Archive data retention policies

**4. Monitoring and Alerting:**
- Job completion/failure alerts
- Resource utilization monitoring
- Archive storage capacity monitoring
- Database connection health checks

### OpenShift-Specific Features

**1. Routes for Management Interface:**
```yaml
# File: openshift/route.yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: pipeline-management
  namespace: data-pipeline
spec:
  to:
    kind: Service
    name: pipeline-management-service
  port:
    targetPort: 8080
  tls:
    termination: edge
```

**2. Security Context Constraints:**
```yaml
# File: openshift/scc.yaml
apiVersion: security.openshift.io/v1
kind: SecurityContextConstraints
metadata:
  name: pipeline-scc
allowHostDirVolumePlugin: false
allowHostIPC: false
allowHostNetwork: false
allowHostPID: false
allowHostPorts: false
allowPrivilegedContainer: false
allowedCapabilities: []
defaultAddCapabilities: []
requiredDropCapabilities:
- ALL
runAsUser:
  type: MustRunAsNonRoot
```

This comprehensive OpenShift/Kubernetes deployment guide provides enterprise-ready deployment options with security, scalability, and operational best practices for production environments.

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