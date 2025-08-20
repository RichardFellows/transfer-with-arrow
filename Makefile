.PHONY: help up down setup clean logs test test-unit test-integration test-build test-clean \
        pipeline-run pipeline-validate pipeline-stats pipeline-help \
        pipeline-extract pipeline-extract-tables pipeline-load pipeline-load-batch pipeline-load-tables pipeline-load-date-range \
        archive-list archive-list-table archive-list-last archive-stats archive-info archive-cleanup-dry archive-cleanup-dry-days archive-cleanup archive-cleanup-days \
        pipeline-two-stage pipeline-two-stage-tables pipeline-extract-only pipeline-load-only pipeline-direct \
        reporting-setup reporting-client-sync reporting-scd2-sync reporting-incremental reporting-verify reporting-two-stage reporting-extract reporting-load

help:
	@echo "Available commands:"
	@echo "  make up           - Start all containers"
	@echo "  make setup        - Setup databases and create reporting tables"
	@echo "  make logs         - Show container logs"
	@echo "  make clean        - Stop and remove all containers and volumes"
	@echo ""
	@echo "Basic Data Pipeline:"
	@echo "  make pipeline-run          - Run pipeline with default config"
	@echo "  make pipeline-validate     - Validate pipeline configuration"
	@echo "  make pipeline-stats        - Show pipeline statistics"
	@echo "  make pipeline-help         - Show pipeline CLI help"
	@echo ""
	@echo "Two-Stage Pipeline Modes:"
	@echo "  make pipeline-two-stage    - Run complete two-stage pipeline (extract → load)"
	@echo "  make pipeline-extract-only - Run in extract-only mode"
	@echo "  make pipeline-load-only    - Run in load-only mode"
	@echo "  make pipeline-direct       - Run in direct mode (traditional)"
	@echo ""
	@echo "Extract Operations:"
	@echo "  make pipeline-extract                    - Extract all tables to archive"
	@echo "  make pipeline-extract-tables TABLES=... - Extract specific tables"
	@echo ""
	@echo "Load Operations:"
	@echo "  make pipeline-load                       - Load latest batches from archive"
	@echo "  make pipeline-load-batch BATCH=...      - Load specific batch"
	@echo "  make pipeline-load-tables TABLES=...    - Load specific tables"
	@echo "  make pipeline-load-date-range DATE_RANGE=... - Load batches from date range"
	@echo ""
	@echo "Archive Management:"
	@echo "  make archive-list                        - List available batches"
	@echo "  make archive-list-table TABLE=...       - List batches for specific table"
	@echo "  make archive-list-last LAST=...         - List last N batches"
	@echo "  make archive-stats                       - Show archive statistics"
	@echo "  make archive-info BATCH=...             - Show batch information"
	@echo "  make archive-cleanup-dry                 - Archive cleanup (dry run)"
	@echo "  make archive-cleanup-dry-days DAYS=...  - Cleanup with retention (dry run)"
	@echo "  make archive-cleanup                     - Archive cleanup (LIVE - deletes files)"
	@echo "  make archive-cleanup-days DAYS=...      - Cleanup with retention (LIVE)"
	@echo ""
	@echo "Reporting Data Pipeline:"
	@echo "  make reporting-setup       - Create reporting tables and load test data"
	@echo "  make reporting-client-sync - Run Reporting_Client pipeline (direct mode)"
	@echo "  make reporting-scd2-sync   - Run Reporting_Client_SCD2 pipeline (direct mode)"
	@echo "  make reporting-incremental - Run incremental sync for both tables (direct mode)"
	@echo "  make reporting-two-stage   - Run two-stage pipeline for reporting tables"
	@echo "  make reporting-extract     - Extract reporting tables to archive"
	@echo "  make reporting-load        - Load latest reporting table batches"
	@echo "  make reporting-verify      - Verify data integrity"
	@echo ""
	@echo "Testing commands:"
	@echo "  make test         - Run all tests (unit + integration) with coverage"
	@echo "  make test-unit    - Run only unit tests with coverage"
	@echo "  make test-integration - Run only integration tests with coverage"
	@echo "  make test-build   - Build test container"
	@echo "  make test-clean   - Clean test containers and volumes"

up:
	docker-compose up -d --remove-orphans
	@echo "Waiting for services to be healthy..."
	@sleep 10

down:
	docker-compose down --remove-orphans

setup: up
	@echo "Setting up source and destination databases..."
	@echo "Creating ReportingDB database on source..."
	docker exec mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ReportingDB') CREATE DATABASE ReportingDB;"
	@echo "Creating TargetDB database on destination..."
	docker exec mssql-dest /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'TargetDB') CREATE DATABASE TargetDB;"
	@echo "Creating Reporting_Client table..."
	docker exec mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d ReportingDB -i /scripts/create_reporting_client_table.sql
	@echo "Creating Reporting_Client_SCD2 table..."
	docker exec mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d ReportingDB -i /scripts/create_reporting_client_scd2_table.sql
	@echo "Loading test data..."
	docker exec mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d ReportingDB -i /scripts/populate_reporting_client_unified_quick.sql
	docker exec mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d ReportingDB -i /scripts/populate_reporting_client_scd2_data.sql
	@echo "Setup complete!"

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --remove-orphans

shell:
	docker exec -it dlt-runner /bin/bash

sql-source:
	docker exec -it mssql-source /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d ReportingDB -C

sql-dest:
	docker exec -it mssql-dest /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -C

# Configuration-driven pipeline commands
pipeline-run:
	docker exec dlt-runner python /app/run_pipeline.py run

pipeline-validate:
	docker exec dlt-runner python /app/run_pipeline.py validate

pipeline-stats:
	docker exec dlt-runner python /app/run_pipeline.py stats

pipeline-help:
	docker exec dlt-runner python /app/run_pipeline.py --help

# Two-stage pipeline operation commands
pipeline-extract:
	@echo "🚀 Extracting all tables to archive..."
	docker exec dlt-runner python /app/run_pipeline.py extract

pipeline-extract-tables:
	@echo "🚀 Extracting specific tables to archive..."
	@echo "Usage: make pipeline-extract-tables TABLES='table1 table2'"
	@if [ -z "$(TABLES)" ]; then echo "❌ Error: TABLES variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py extract --tables $(TABLES)

pipeline-load:
	@echo "🚀 Loading latest batches from archive..."
	docker exec dlt-runner python /app/run_pipeline.py load

pipeline-load-batch:
	@echo "🚀 Loading specific batch from archive..."
	@echo "Usage: make pipeline-load-batch BATCH=20250817_143000"
	@if [ -z "$(BATCH)" ]; then echo "❌ Error: BATCH variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py load --batch $(BATCH)

pipeline-load-tables:
	@echo "🚀 Loading specific tables from archive..."
	@echo "Usage: make pipeline-load-tables TABLES='table1 table2'"
	@if [ -z "$(TABLES)" ]; then echo "❌ Error: TABLES variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py load --tables $(TABLES)

pipeline-load-date-range:
	@echo "🚀 Loading batches from date range..."
	@echo "Usage: make pipeline-load-date-range DATE_RANGE=20250815-20250817"
	@if [ -z "$(DATE_RANGE)" ]; then echo "❌ Error: DATE_RANGE variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py load --date-range $(DATE_RANGE)

# Archive management commands
archive-list:
	@echo "📋 Listing available batches..."
	docker exec dlt-runner python /app/run_pipeline.py archive list

archive-list-table:
	@echo "📋 Listing batches for specific table..."
	@echo "Usage: make archive-list-table TABLE=table_name"
	@if [ -z "$(TABLE)" ]; then echo "❌ Error: TABLE variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py archive list --table $(TABLE)

archive-list-last:
	@echo "📋 Listing last N batches..."
	@echo "Usage: make archive-list-last LAST=10"
	@if [ -z "$(LAST)" ]; then echo "❌ Error: LAST variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py archive list --last $(LAST)

archive-stats:
	@echo "📊 Showing archive statistics..."
	docker exec dlt-runner python /app/run_pipeline.py archive stats

archive-info:
	@echo "📦 Showing batch information..."
	@echo "Usage: make archive-info BATCH=20250817_143000"
	@if [ -z "$(BATCH)" ]; then echo "❌ Error: BATCH variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py archive info --batch $(BATCH)

archive-cleanup-dry:
	@echo "🧹 Archive cleanup (dry run)..."
	docker exec dlt-runner python /app/run_pipeline.py archive cleanup

archive-cleanup-dry-days:
	@echo "🧹 Archive cleanup for specific retention period (dry run)..."
	@echo "Usage: make archive-cleanup-dry-days DAYS=30"
	@if [ -z "$(DAYS)" ]; then echo "❌ Error: DAYS variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than $(DAYS)d

archive-cleanup:
	@echo "🧹 Archive cleanup (LIVE MODE - will delete files)..."
	@echo "⚠️  This will permanently delete old batches. Press Ctrl+C to cancel..."
	@sleep 3
	docker exec dlt-runner python /app/run_pipeline.py archive cleanup --confirm

archive-cleanup-days:
	@echo "🧹 Archive cleanup for specific retention period (LIVE MODE)..."
	@echo "Usage: make archive-cleanup-days DAYS=30"
	@if [ -z "$(DAYS)" ]; then echo "❌ Error: DAYS variable is required"; exit 1; fi
	@echo "⚠️  This will permanently delete batches older than $(DAYS) days. Press Ctrl+C to cancel..."
	@sleep 3
	docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than $(DAYS)d --confirm

# Two-stage workflow commands
pipeline-two-stage:
	@echo "🔄 Running complete two-stage pipeline (extract → load)..."
	docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage

pipeline-two-stage-tables:
	@echo "🔄 Running two-stage pipeline for specific tables..."
	@echo "Usage: make pipeline-two-stage-tables TABLES='table1 table2'"
	@if [ -z "$(TABLES)" ]; then echo "❌ Error: TABLES variable is required"; exit 1; fi
	docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage --tables $(TABLES)

pipeline-extract-only:
	@echo "📦 Running pipeline in extract-only mode..."
	docker exec dlt-runner python /app/run_pipeline.py run --mode extract-only

pipeline-load-only:
	@echo "🚚 Running pipeline in load-only mode..."
	docker exec dlt-runner python /app/run_pipeline.py run --mode load-only

pipeline-direct:
	@echo "⚡ Running pipeline in direct mode..."
	docker exec dlt-runner python /app/run_pipeline.py run --mode direct

# Reporting table two-stage workflows
reporting-two-stage:
	@echo "🔄 Running two-stage pipeline for reporting tables..."
	docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage --tables Reporting_Client,Reporting_Client_SCD2

reporting-extract:
	@echo "📦 Extracting reporting tables to archive..."
	docker exec dlt-runner python /app/run_pipeline.py extract --tables Reporting_Client,Reporting_Client_SCD2

reporting-load:
	@echo "🚚 Loading latest reporting table batches..."
	docker exec dlt-runner python /app/run_pipeline.py load --tables Reporting_Client,Reporting_Client_SCD2

# Reporting table pipeline commands
reporting-client-sync:
	docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client

reporting-scd2-sync:
	docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client_SCD2

reporting-incremental:
	@echo "Running incremental sync for both reporting tables..."
	docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client,Reporting_Client_SCD2 --environment full

reporting-verify:
	@echo "Verifying reporting data integrity..."
	docker exec mssql-dest /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "SecurePass123" -d TargetDB -Q "SELECT 'Reporting_Client' as TableName, COUNT(*) as RecordCount, MIN(SystemCalendarID) as MinDate, MAX(SystemCalendarID) as MaxDate FROM reporting_data.reporting_client UNION ALL SELECT 'Reporting_Client_SCD2', COUNT(*), MIN(SystemCalendarID), MAX(SystemCalendarID) FROM reporting_data.reporting_client_scd2"

reporting-setup: setup
	@echo "Reporting tables setup complete!"

# Testing targets
test-build:
	@echo "Building test container..."
	docker-compose -f docker-compose.test.yaml build

test: test-build
	@echo "Running all tests with coverage and reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm --remove-orphans -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests -v --cov=/app/src --cov=/app/run_pipeline.py --cov-report=html:/test-reports/coverage_html --cov-report=term --cov-report=xml:/test-reports/coverage.xml --cov-report=lcov:/test-reports/lcov.info --html=/test-reports/test_report.html --self-contained-html --junitxml=/test-reports/test_results.xml --json-report --json-report-file=/test-reports/test_report.json --cov-fail-under=60
	@echo "Test reports generated in test-reports/ directory:"
	@echo "  - HTML Report: test-reports/test_report.html"
	@echo "  - JUnit XML: test-reports/test_results.xml"
	@echo "  - JSON Report: test-reports/test_report.json"
	@echo "  - Coverage HTML: test-reports/coverage_html/index.html"
	@echo "  - Coverage XML: test-reports/coverage.xml"
	@echo "  - Coverage LCOV: test-reports/lcov.info"

test-unit: test-build
	@echo "Running unit tests with coverage and reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm --remove-orphans -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests/unit -v -m unit --cov=/app/src --cov=/app/run_pipeline.py --cov-report=html:/test-reports/unit_coverage_html --cov-report=term --cov-report=xml:/test-reports/unit_coverage.xml --cov-report=lcov:/test-reports/unit_lcov.info --html=/test-reports/unit_test_report.html --self-contained-html --junitxml=/test-reports/unit_test_results.xml --cov-fail-under=0
	@echo "Unit test reports generated in test-reports/ directory:"
	@echo "  - HTML Report: test-reports/unit_test_report.html"
	@echo "  - JUnit XML: test-reports/unit_test_results.xml"
	@echo "  - Coverage HTML: test-reports/unit_coverage_html/index.html"
	@echo "  - Coverage XML: test-reports/unit_coverage.xml"
	@echo "  - Coverage LCOV: test-reports/unit_lcov.info"

test-integration: test-build
	@echo "Running integration tests with coverage and reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm --remove-orphans -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests/integration -v -m integration --cov=/app/src --cov=/app/run_pipeline.py --cov-report=html:/test-reports/integration_coverage_html --cov-report=term --cov-report=xml:/test-reports/integration_coverage.xml --cov-report=lcov:/test-reports/integration_lcov.info --html=/test-reports/integration_test_report.html --self-contained-html --junitxml=/test-reports/integration_test_results.xml --cov-fail-under=0
	@echo "Integration test reports generated in test-reports/ directory:"
	@echo "  - HTML Report: test-reports/integration_test_report.html"
	@echo "  - JUnit XML: test-reports/integration_test_results.xml"
	@echo "  - Coverage HTML: test-reports/integration_coverage_html/index.html"
	@echo "  - Coverage XML: test-reports/integration_coverage.xml"
	@echo "  - Coverage LCOV: test-reports/integration_lcov.info"

test-clean:
	@echo "Cleaning test containers and volumes..."
	docker-compose -f docker-compose.test.yaml down -v --remove-orphans
	docker rmi transfer-with-arrow_dlt-runner-test 2>/dev/null || true

test-simple: test-build
	@echo "Running all tests (simple output)..."
	docker-compose -f docker-compose.test.yaml up --abort-on-container-exit --remove-orphans
	docker-compose -f docker-compose.test.yaml down --remove-orphans

test-shell: test-build
	@echo "Starting test container shell..."
	docker-compose -f docker-compose.test.yaml run --rm --remove-orphans dlt-runner-test /bin/bash

test-help:
	@echo "Test Commands Available:"
	@echo "  make test              - Run all tests with coverage and comprehensive reports"
	@echo "  make test-unit         - Run only unit tests with coverage and reports"
	@echo "  make test-integration  - Run only integration tests with coverage and reports"
	@echo "  make test-coverage     - Alias for 'make test' (all commands now include coverage)"
	@echo "  make test-simple       - Run tests with simple console output (no reports)"
	@echo "  make test-clean        - Clean test containers and volumes"
	@echo "  make test-shell        - Start test container shell for debugging"
	@echo ""
	@echo "Generated Reports (in test-reports/ directory):"
	@echo "All Tests (make test):"
	@echo "  - test_report.html           - Comprehensive HTML test report"
	@echo "  - test_results.xml           - JUnit XML format (CI/CD)"
	@echo "  - test_report.json           - JSON format test results"
	@echo "  - coverage_html/index.html   - Code coverage report"
	@echo "  - coverage.xml/coverage.lcov - Coverage in XML/LCOV formats"
	@echo "Unit Tests (make test-unit):"
	@echo "  - unit_test_report.html      - Unit tests HTML report"
	@echo "  - unit_coverage_html/index.html - Unit tests coverage"
	@echo "Integration Tests (make test-integration):"
	@echo "  - integration_test_report.html - Integration tests HTML report"
	@echo "  - integration_coverage_html/index.html - Integration tests coverage"

