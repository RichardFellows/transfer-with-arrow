.PHONY: help up down setup restore-backup test-copy clean logs test test-unit test-integration test-build test-clean reporting-setup reporting-full-sync reporting-add-day reporting-incremental reporting-verify reporting-scenario reporting-full-workflow reporting-incremental-workflow

help:
	@echo "Available commands:"
	@echo "  make up           - Start all containers"
	@echo "  make setup        - Setup databases and restore backup"
	@echo "  make logs         - Show container logs"
	@echo "  make clean        - Stop and remove all containers and volumes"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make pipeline-run          - Run pipeline with default config"
	@echo "  make pipeline-run-dev      - Run pipeline with dev environment"
	@echo "  make pipeline-run-users    - Run pipeline with only Users table"
	@echo "  make pipeline-validate     - Validate pipeline configuration"
	@echo "  make pipeline-stats        - Show pipeline statistics"
	@echo "  make pipeline-help         - Show pipeline CLI help"
	@echo ""
	@echo "Common Aliases:"
	@echo "  make test-copy             - Run full pipeline (alias for pipeline-run)"
	@echo "  make test-users            - Run Users table only (alias for pipeline-run-users)"
	@echo "  make test-incremental      - Run incremental loading example"
	@echo "  make verify                - Run pipeline with verification (alias for pipeline-run)"
	@echo ""
	@echo "Production-Scale Testing:"
	@echo "  make reporting-setup       - Create Reporting_Client table and load 6M records"
	@echo "  make reporting-full-sync   - Run initial full sync of Reporting_Client" 
	@echo "  make reporting-add-day     - Add next day's data (2M records)"
	@echo "  make reporting-incremental - Run incremental sync of new data"
	@echo "  make reporting-verify      - Verify sync results and data integrity"
	@echo "  make reporting-scenario    - Run complete incremental test scenario"
	@echo ""
	@echo "Testing commands:"
	@echo "  make test         - Run all tests (unit + integration) with coverage"
	@echo "  make test-unit    - Run only unit tests with coverage"
	@echo "  make test-integration - Run only integration tests with coverage"
	@echo "  make test-coverage - Alias for 'make test' (all commands now include coverage)"
	@echo "  make test-build   - Build test container"
	@echo "  make test-clean   - Clean test containers and volumes"

up:
	docker-compose up -d --remove-orphans
	@echo "Waiting for services to be healthy..."
	@sleep 10

down:
	docker-compose down --remove-orphans

setup: up
	@echo "Setting up databases..."
	docker exec mssql-dest /scripts/setup_destination.sh
	@echo "Restoring StackOverflow backup..."
	docker exec mssql-source /scripts/restore_backup.sh
	@echo "Setup complete!"

# Convenient aliases for common tasks
test-copy:
	make pipeline-run

test-users:
	make pipeline-run-users

test-incremental:
	docker exec dlt-runner python /app/run_pipeline.py run --tables Posts --environment dev

verify:
	make pipeline-run

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --remove-orphans
# 	rm -rf backups/*.bak

shell:
	docker exec -it dlt-runner /bin/bash

sql-source:
	docker exec -it mssql-source /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'Strong!Passw0rd'

sql-dest:
	docker exec -it mssql-dest /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'Strong!Passw0rd'

# New configuration-driven pipeline commands
pipeline-run:
	docker exec dlt-runner python /app/run_pipeline.py run

pipeline-run-dev:
	docker exec dlt-runner python /app/run_pipeline.py -e dev run

pipeline-validate:
	docker exec dlt-runner python /app/run_pipeline.py validate

pipeline-stats:
	docker exec dlt-runner python /app/run_pipeline.py stats

pipeline-help:
	docker exec dlt-runner python /app/run_pipeline.py --help

# Pipeline commands with specific configurations
pipeline-run-users:
	docker exec dlt-runner python /app/run_pipeline.py run --tables Users

pipeline-run-test:
	docker exec dlt-runner python /app/run_pipeline.py -e test run

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

test-coverage: test

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

# Interactive development
shell:
	docker exec -it dlt-runner bash

# Database access for troubleshooting
sql-source:
	docker exec -it mssql-source /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Strong!Passw0rd -C

sql-dest:
	docker exec -it mssql-dest /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Strong!Passw0rd -C

# Production-Scale Incremental Loading Test Targets
reporting-setup:
	@echo "Creating Reporting_Client table and loading 6M records..."
	docker exec mssql-source /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Strong!Passw0rd -C -i /scripts/create_reporting_client_table.sql
	docker exec mssql-source /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Strong!Passw0rd -C -i /scripts/populate_reporting_client_data.sql
	@echo "Reporting_Client setup complete! 6M records loaded across 3 days."

reporting-full-sync:
	@echo "Running initial full synchronization of Reporting_Client..."
	docker exec dlt-runner python /app/run_pipeline.py --config /app/config/reporting_client_config.yaml --tables Reporting_Client
	@echo "Full sync complete!"

reporting-add-day:
	@echo "Adding next day's data (2M records)..."
	docker exec mssql-source /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Strong!Passw0rd -C -i /scripts/add_next_day_data.sql
	@echo "Next day data added! Ready for incremental sync."

reporting-incremental:
	@echo "Running incremental synchronization (new records only)..."
	docker exec dlt-runner python /app/run_pipeline.py --config /app/config/reporting_client_config.yaml --tables Reporting_Client
	@echo "Incremental sync complete!"

reporting-verify:
	@echo "Verifying sync results and data integrity..."
	docker exec dlt-runner python /scripts/verify_incremental_sync.py
	@echo "Verification complete!"

reporting-scenario:
	@echo "Running complete incremental loading test scenario..."
	docker exec dlt-runner python /scripts/run_incremental_test_scenario.py
	@echo "Complete scenario test finished!"

# Convenience targets for step-by-step testing
reporting-full-workflow: reporting-setup reporting-full-sync reporting-verify
	@echo "Full workflow (setup + sync + verify) completed!"

reporting-incremental-workflow: reporting-add-day reporting-incremental reporting-verify  
	@echo "Incremental workflow (add data + sync + verify) completed!"