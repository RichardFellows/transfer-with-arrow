# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a configuration-driven data migration project that transfers StackOverflow database tables from a source MSSQL database to a destination MSSQL database using the DLT (Data Loading Tool) framework with PyArrow backend. The project uses Docker containers to set up the entire environment and provides a flexible YAML-based configuration system for defining migration workflows.

## Architecture

- **Source Database**: MSSQL Server container with StackOverflowMini sample database (restored from backup)
- **Destination Database**: MSSQL Server container with TargetDB database
- **DLT Runner**: Python container that runs the configuration-driven migration pipeline
- **Configuration System**: YAML-based pipeline configuration with environment support and advanced features

## Common Commands

### Environment Management
- `make up` - Start all Docker containers
- `make down` - Stop all Docker containers  
- `make setup` - Setup databases and restore StackOverflow backup
- `make clean` - Stop and remove all containers and volumes

### Data Pipeline Commands
- `make pipeline-run` - Run pipeline with default configuration
- `make pipeline-run-dev` - Run pipeline with development environment settings
- `make pipeline-run-users` - Run pipeline for Users table only
- `make pipeline-validate` - Validate pipeline configuration
- `make pipeline-stats` - Show pipeline statistics and table information
- `make pipeline-help` - Show detailed CLI help

### Development Commands
- `make logs` - Show container logs
- `make shell` - Access DLT runner container shell
- `make sql-source` - Connect to source database CLI
- `make sql-dest` - Connect to destination database CLI

### Testing Commands
- `make test` - Run all tests (unit + integration)
- `make test-unit` - Run only unit tests (fast, no database required)
- `make test-integration` - Run only integration tests (requires test databases)
- `make test-coverage` - Run tests with coverage report
- `make test-clean` - Clean test containers and volumes
- `make test-shell` - Start test container shell for debugging

### Direct Pipeline Usage
Execute the pipeline directly in the DLT runner container:
```bash
docker exec dlt-runner python /app/run_pipeline.py [command] [options]
```

Commands:
- `run` - Execute the data migration pipeline
- `validate` - Validate configuration without running
- `stats` - Show configuration overview and statistics

Global Options:
- `--config, -c` - Configuration file (default: pipeline_config.yaml)
- `--environment, -e` - Environment configuration (dev, staging, prod, etc.)
- `--config-dir` - Configuration directory (default: config/)

Run Command Options:
- `--tables, -t` - Specific tables to process
- `--output, -o` - Save results to JSON file

Examples:
```bash
# Run with default configuration
docker exec dlt-runner python /app/run_pipeline.py run

# Run with development environment
docker exec dlt-runner python /app/run_pipeline.py run --environment dev

# Run specific tables only
docker exec dlt-runner python /app/run_pipeline.py run --tables Users Posts

# Validate configuration
docker exec dlt-runner python /app/run_pipeline.py validate --environment prod
```

## Data Pipeline Architecture

The pipeline system provides enhanced flexibility through YAML-based configuration:

### Core Features
- **🎯 YAML Configuration**: Complete pipeline definition in `dlt_scripts/config/pipeline_config.yaml`
- **🔧 Environment Support**: Environment-specific configurations (dev/staging/prod) with overrides
- **⚡ Advanced Incremental Loading**: Multiple strategies (timestamp, sequence, custom) per table
- **✅ Data Verification**: Built-in verification with custom checks and tolerance settings
- **📊 Comprehensive Logging**: Structured logging with progress tracking and monitoring
- **🔍 Schema Validation**: Pydantic-based configuration validation with detailed error reporting

### Pipeline Configuration
- **Backend**: PyArrow for efficient data processing
- **File Format**: Parquet for optimized storage and compression
- **Chunk Size**: 10,000 rows per chunk (configurable per environment)
- **Default Tables**: Users, Posts, Comments, Votes, Badges, PostTags, Tags
- **Connection Management**: Environment variable substitution with secure credential handling
- **Error Handling**: Graceful error handling with detailed logging and recovery options

### Configuration Structure
```
dlt_scripts/
├── config/
│   ├── pipeline_config.yaml      # Main configuration
│   └── environments/             # Environment-specific overrides
│       ├── dev.yaml              # Development settings
│       ├── prod.yaml             # Production settings  
│       └── test.yaml             # Test environment settings
├── src/pipeline/                 # Core pipeline components
├── run_pipeline.py               # Main CLI entry point
└── README.md                     # Detailed documentation
```

See `dlt_scripts/README.md` for comprehensive configuration options and examples.

## Testing Architecture

The project includes comprehensive testing with both unit and integration tests:

### Unit Tests (`tests/unit/`)
- Mock external dependencies (databases, DLT framework)
- Test individual function logic and error handling
- Fast execution, no external dependencies required
- Configuration system tests: `tests/unit/test_config_system.py`
- Pipeline compatibility tests: `tests/unit/test_pipeline_compatibility.py`

### Integration Tests (`tests/integration/`)
- Use real SQL Server containers via testcontainers library
- Test complete data migration workflows
- Verify data integrity and pipeline functionality
- Configuration-driven pipeline tests: `tests/integration/test_config_pipeline.py`
- Full pipeline integration tests: `tests/integration/test_full_pipeline_new.py`

### Test Dependencies
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `testcontainers` - Docker container management for tests
- `pytest-sqlalchemy-mock` - SQLAlchemy testing utilities
- Coverage reporting with `pytest-cov`

### Test Configuration
- `pytest.ini` - Test configuration and markers
- `requirements-test.txt` - Test-specific dependencies
- `docker-compose.test.yaml` - Test environment setup
- `Dockerfile.test` - Test container configuration

## Key Configuration

- Source database runs on port 1433
- Destination database runs on port 1434 
- Both databases use SA password: `SecurePass123`
- DLT configuration files are in `dlt_scripts/.dlt/`
- Connection strings include necessary MSSQL ODBC driver parameters for SSL/encryption