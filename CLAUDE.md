# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data migration project that transfers StackOverflow database tables from a source MSSQL database to a destination MSSQL database using the DLT (Data Loading Tool) framework with PyArrow backend. The project uses Docker containers to set up the entire environment including source database, destination database, and the DLT runner.

## Architecture

- **Source Database**: MSSQL Server container with StackOverflowMini sample database (restored from backup)
- **Destination Database**: MSSQL Server container with TargetDB database
- **DLT Runner**: Python container that runs the data migration scripts using DLT framework
- **Migration Script**: `dlt_scripts/copy_stackoverflow.py` - Main script handling table copying with configurable options

## Common Commands

### Environment Management
- `make up` - Start all Docker containers
- `make down` - Stop all Docker containers  
- `make setup` - Setup databases and restore StackOverflow backup
- `make clean` - Stop and remove all containers and volumes

### Data Migration Commands
- `make test-copy` - Run full copy of all StackOverflow tables
- `make test-users` - Copy only the Users table (useful for testing)
- `make test-incremental` - Test incremental loading on Posts table
- `make verify` - Verify data copy by comparing row counts between source and destination

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

### Direct Script Usage
Execute the Python script directly in the DLT runner container:
```bash
docker exec dlt-runner python /app/copy_stackoverflow.py [options]
```

Options:
- `--tables [table1 table2 ...]` - Specify tables to copy
- `--incremental` - Use incremental loading
- `--verify` - Verify copy after completion
- `--disposition [replace|append|merge]` - Write disposition (default: replace)

## Data Pipeline Details

The DLT pipeline is configured with:
- **Backend**: PyArrow for efficient data processing
- **File Format**: Parquet for optimized storage
- **Chunk Size**: 10,000 rows per chunk
- **Default Tables**: Users, Posts, Comments, Votes, Badges, PostTags, Tags
- **Connection Strings**: Configured via environment variables in docker-compose.yaml

## Testing Architecture

The project includes comprehensive testing with both unit and integration tests:

### Unit Tests (`tests/unit/`)
- Mock external dependencies (databases, DLT framework)
- Test individual function logic and error handling
- Fast execution, no external dependencies required
- Located in `tests/unit/test_copy_stackoverflow.py`

### Integration Tests (`tests/integration/`)
- Use real SQL Server containers via testcontainers library
- Test complete data migration workflows
- Verify data integrity and pipeline functionality
- Located in `tests/integration/test_full_pipeline.py`

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
- Both databases use SA password: `Strong!Passw0rd`
- DLT configuration files are in `dlt_scripts/.dlt/`
- Connection strings include necessary MSSQL ODBC driver parameters for SSL/encryption