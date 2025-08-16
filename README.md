# Transfer with Arrow

A data migration project that transfers StackOverflow database tables from a source MSSQL database to a destination MSSQL database using the DLT (Data Loading Tool) framework with PyArrow backend.

## Overview

This project demonstrates a complete data pipeline solution using modern tools:
- **DLT (Data Loading Tool)** for efficient data extraction and loading
- **PyArrow** backend for high-performance data processing
- **Docker** for containerized, reproducible environments
- **MSSQL Server** as both source and destination databases
- **Comprehensive testing** with both unit and integration tests

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source DB     │    │   DLT Runner    │    │ Destination DB  │
│                 │    │                 │    │                 │
│ StackOverflow   │───▶│ Python + DLT    │───▶│   TargetDB      │
│ Mini Database   │    │ PyArrow Backend │    │                 │
│ (Port 1433)     │    │                 │    │ (Port 1434)     │
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
# Copy all default tables
make test-copy

# Copy specific tables
make test-users

# Test incremental loading
make test-incremental
```

### 3. Verify Migration
```bash
# Verify data was copied correctly
make verify
```

## Commands Reference

### Environment Management
- `make up` - Start all Docker containers
- `make down` - Stop all Docker containers  
- `make setup` - Setup databases and restore StackOverflow backup
- `make clean` - Stop and remove all containers and volumes

### Data Migration
- `make test-copy` - Run full copy of all StackOverflow tables
- `make test-users` - Copy only the Users table (useful for testing)
- `make test-incremental` - Test incremental loading on Posts table
- `make verify` - Verify data copy by comparing row counts between source and destination

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

## Data Pipeline Configuration

The DLT pipeline includes:
- **Backend**: PyArrow for efficient data processing
- **File Format**: Parquet for optimized storage
- **Chunk Size**: 10,000 rows per chunk for large tables
- **Default Tables**: Users, Posts, Comments, Votes, Badges, PostTags, Tags
- **Write Modes**: Replace (default), Append, Merge

### Direct Script Usage
You can also run the migration script directly:

```bash
docker exec dlt-runner python /app/copy_stackoverflow.py [options]
```

**Options:**
- `--tables [table1 table2 ...]` - Specify tables to copy
- `--incremental` - Use incremental loading
- `--verify` - Verify copy after completion
- `--disposition [replace|append|merge]` - Write disposition (default: replace)

**Examples:**
```bash
# Copy specific tables
docker exec dlt-runner python /app/copy_stackoverflow.py --tables Users Posts

# Incremental load with verification
docker exec dlt-runner python /app/copy_stackoverflow.py --tables Posts --incremental --verify

# Append mode
docker exec dlt-runner python /app/copy_stackoverflow.py --disposition append
```

## Testing Framework

### Unit Tests
Fast tests with mocked dependencies:
- Test individual function logic
- Validate configuration and error handling
- No external dependencies required
- Run with: `make test-unit`

### Integration Tests
End-to-end testing with real databases:
- Use SQL Server containers via testcontainers
- Test complete data migration workflows
- Verify data integrity and pipeline functionality
- Run with: `make test-integration`

### Test Dependencies
- `pytest` - Testing framework
- `pytest-mock` - Mocking utilities
- `testcontainers` - Docker container management for tests
- Coverage reporting with `pytest-cov`

## Database Configuration

- **Source Database**: Port 1433, StackOverflowMini sample data
- **Destination Database**: Port 1434, TargetDB (created automatically)
- **Authentication**: SA user with password `Strong!Passw0rd`
- **SSL/Encryption**: Configured with TrustServerCertificate for development

## Project Structure

```
transfer-with-arrow/
├── dlt_scripts/              # DLT pipeline scripts and config
│   ├── copy_stackoverflow.py # Main migration script
│   ├── requirements.txt      # Python dependencies
│   ├── requirements-test.txt # Test dependencies
│   └── .dlt/                # DLT configuration files
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures and utilities
├── scripts/                # Database setup scripts
├── backups/                # Database backup files
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
1. Update the default tables list in `copy_stackoverflow.py`
2. Add corresponding test data in integration test fixtures
3. Update documentation

### Extending Pipeline
- Modify `copy_stackoverflow.py` for new data sources
- Update DLT configuration in `.dlt/` directory
- Add environment variables to `docker-compose.yaml`

## Troubleshooting

### Common Issues

**Container startup fails:**
```bash
# Check container logs
make logs

# Restart environment
make clean && make setup
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
- Adjust chunk_size in `copy_stackoverflow.py` for your data size
- Monitor Docker resource allocation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

## License

This project is provided as-is for educational and demonstration purposes.