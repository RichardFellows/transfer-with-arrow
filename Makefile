.PHONY: help up down setup restore-backup test-copy clean logs test test-unit test-integration test-build test-clean

help:
	@echo "Available commands:"
	@echo "  make up           - Start all containers"
	@echo "  make setup        - Setup databases and restore backup"
	@echo "  make test-copy    - Run test copy of all tables"
	@echo "  make test-users   - Copy only Users table"
	@echo "  make test-incremental - Test incremental loading"
	@echo "  make verify       - Verify data copy"
	@echo "  make logs         - Show container logs"
	@echo "  make clean        - Stop and remove all containers and volumes"
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

test-copy:
	docker exec dlt-runner python /app/copy_stackoverflow.py

test-users:
	docker exec dlt-runner python /app/copy_stackoverflow.py --tables Users

test-incremental:
	docker exec dlt-runner python /app/copy_stackoverflow.py --tables Posts --incremental

verify:
	docker exec dlt-runner python /app/copy_stackoverflow.py --verify

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