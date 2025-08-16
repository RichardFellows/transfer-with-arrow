.PHONY: help up down setup restore-backup test-copy clean logs test test-unit test-integration test-build test-clean

help:
	@echo "Available commands:"
	@echo "  make up           - Start all containers"
	@echo "  make setup        - Setup databases and restore backup"
	@echo "  make logs         - Show container logs"
	@echo "  make clean        - Stop and remove all containers and volumes"
	@echo ""
	@echo "Configuration-driven Data Pipeline:"
	@echo "  make pipeline-run          - Run pipeline with default config"
	@echo "  make pipeline-run-dev      - Run pipeline with dev environment"
	@echo "  make pipeline-run-users    - Run pipeline with only Users table"
	@echo "  make pipeline-validate     - Validate pipeline configuration"
	@echo "  make pipeline-stats        - Show pipeline statistics"
	@echo "  make pipeline-help         - Show pipeline CLI help"
	@echo ""
	@echo "Legacy Commands (redirected to new pipeline):"
	@echo "  make test-copy    - ⚠️  Use 'make pipeline-run' instead"
	@echo "  make test-users   - ⚠️  Use 'make pipeline-run-users' instead"
	@echo "  make test-incremental - ⚠️  Configure in YAML and use 'make pipeline-run'"
	@echo "  make verify       - ⚠️  Enable verification in config and use 'make pipeline-run'"
	@echo ""
	@echo "Testing commands:"
	@echo "  make test         - Run all tests (unit + integration)"
	@echo "  make test-unit    - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-build   - Build test container"
	@echo "  make test-clean   - Clean test containers and volumes"

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10

down:
	docker-compose down

setup: up
	@echo "Setting up databases..."
	docker exec mssql-dest /scripts/setup_destination.sh
	@echo "Restoring StackOverflow backup..."
	docker exec mssql-source /scripts/restore_backup.sh
	@echo "Setup complete!"

# Legacy commands (replaced by new configuration-driven pipeline)
test-copy:
	@echo "⚠️  Legacy command: Use 'make pipeline-run' instead"
	@echo "   New command provides equivalent functionality with better configurability"
	make pipeline-run

test-users:
	@echo "⚠️  Legacy command: Use 'make pipeline-run-users' instead"  
	@echo "   New command provides equivalent functionality with better configurability"
	make pipeline-run-users

test-incremental:
	@echo "⚠️  Legacy command: Configure incremental loading in YAML config and use 'make pipeline-run'"
	@echo "   New system provides more advanced incremental loading options"
	docker exec dlt-runner python /app/run_pipeline.py run --tables Posts --environment dev

verify:
	@echo "⚠️  Legacy command: Verification is now built into the pipeline"
	@echo "   Enable verification in configuration: verification.enabled: true"
	@echo "   Running pipeline with verification enabled..."
	make pipeline-run

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
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
	docker exec dlt-runner python /app/run_pipeline.py run --environment dev

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
	docker exec dlt-runner python /app/run_pipeline.py run --environment test

# Testing targets
test-build:
	@echo "Building test container..."
	docker-compose -f docker-compose.test.yaml build

test: test-build
	@echo "Running all tests with reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests -v --html=/test-reports/test_report.html --self-contained-html --junitxml=/test-reports/test_results.xml --json-report --json-report-file=/test-reports/test_report.json
	@echo "Test reports generated in test-reports/ directory:"
	@echo "  - HTML Report: test-reports/test_report.html"
	@echo "  - JUnit XML: test-reports/test_results.xml"
	@echo "  - JSON Report: test-reports/test_report.json"

test-unit: test-build
	@echo "Running unit tests with reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests/unit -v -m unit --html=/test-reports/unit_test_report.html --self-contained-html --junitxml=/test-reports/unit_test_results.xml

test-integration: test-build
	@echo "Running integration tests with reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests/integration -v -m integration --html=/test-reports/integration_test_report.html --self-contained-html --junitxml=/test-reports/integration_test_results.xml

test-clean:
	@echo "Cleaning test containers and volumes..."
	docker-compose -f docker-compose.test.yaml down -v
	docker rmi transfer-with-arrow_dlt-runner-test 2>/dev/null || true

test-coverage: test-build
	@echo "Running tests with coverage and reports..."
	@mkdir -p test-reports
	docker-compose -f docker-compose.test.yaml run --rm -v $(PWD)/test-reports:/test-reports dlt-runner-test pytest /tests -v --cov=copy_stackoverflow --cov-report=html:/test-reports/coverage_html --cov-report=term --cov-report=xml:/test-reports/coverage.xml --html=/test-reports/coverage_test_report.html --self-contained-html --junitxml=/test-reports/coverage_test_results.xml
	@echo "Coverage reports generated in test-reports/ directory:"
	@echo "  - HTML Coverage: test-reports/coverage_html/index.html"
	@echo "  - XML Coverage: test-reports/coverage.xml"
	@echo "  - Test Report: test-reports/coverage_test_report.html"

test-simple: test-build
	@echo "Running all tests (simple output)..."
	docker-compose -f docker-compose.test.yaml up --abort-on-container-exit
	docker-compose -f docker-compose.test.yaml down

test-shell: test-build
	@echo "Starting test container shell..."
	docker-compose -f docker-compose.test.yaml run --rm dlt-runner-test /bin/bash

test-help:
	@echo "Test Commands Available:"
	@echo "  make test              - Run all tests and generate comprehensive reports"
	@echo "  make test-unit         - Run only unit tests with reports"
	@echo "  make test-integration  - Run only integration tests with reports"
	@echo "  make test-coverage     - Run tests with code coverage analysis"
	@echo "  make test-simple       - Run tests with simple console output (no reports)"
	@echo "  make test-clean        - Clean test containers and volumes"
	@echo "  make test-shell        - Start test container shell for debugging"
	@echo ""
	@echo "Generated Reports (in test-reports/ directory):"
	@echo "  - test_report.html           - Comprehensive HTML test report"
	@echo "  - test_results.xml           - JUnit XML format (CI/CD)"
	@echo "  - test_report.json           - JSON format test results"
	@echo "  - unit_test_report.html      - Unit tests only"
	@echo "  - integration_test_report.html - Integration tests only"
	@echo "  - coverage_html/index.html   - Code coverage report"