@echo off
REM Windows CMD Scripts for Transfer with Arrow Pipeline
REM Batch file equivalents of Makefile commands

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="up" goto up
if "%1"=="down" goto down
if "%1"=="setup" goto setup
if "%1"=="clean" goto clean
if "%1"=="pipeline-run" goto pipeline-run
if "%1"=="pipeline-run-dev" goto pipeline-run-dev
if "%1"=="reporting-client-sync" goto reporting-client-sync
if "%1"=="reporting-scd2-sync" goto reporting-scd2-sync
if "%1"=="reporting-incremental" goto reporting-incremental
if "%1"=="reporting-verify" goto reporting-verify
if "%1"=="pipeline-validate" goto pipeline-validate
if "%1"=="pipeline-stats" goto pipeline-stats
if "%1"=="pipeline-help" goto pipeline-help
if "%1"=="extract" goto extract
if "%1"=="load" goto load
if "%1"=="archive-list" goto archive-list
if "%1"=="archive-stats" goto archive-stats
if "%1"=="archive-cleanup" goto archive-cleanup
if "%1"=="logs" goto logs
if "%1"=="shell" goto shell
if "%1"=="sql-source" goto sql-source
if "%1"=="sql-dest" goto sql-dest
if "%1"=="test" goto test
if "%1"=="test-unit" goto test-unit
if "%1"=="test-integration" goto test-integration
if "%1"=="test-coverage" goto test-coverage
if "%1"=="test-clean" goto test-clean
if "%1"=="test-shell" goto test-shell
if "%1"=="local-setup" goto local-setup
if "%1"=="local-run" goto local-run
if "%1"=="local-extract" goto local-extract
if "%1"=="local-load" goto local-load
if "%1"=="local-test-connection" goto local-test-connection

echo Unknown command: %1
goto help

:help
echo.
echo 🚀 Transfer with Arrow - Windows CMD Commands
echo.
echo ENVIRONMENT MANAGEMENT:
echo   scripts up                    Start Docker containers
echo   scripts down                  Stop Docker containers  
echo   scripts setup                 Setup databases and containers
echo   scripts clean                 Remove containers and volumes
echo.
echo PIPELINE OPERATIONS:
echo   scripts pipeline-run          Run pipeline with default config
echo   scripts pipeline-run-dev      Run with development environment
echo   scripts reporting-client-sync Run Reporting_Client pipeline
echo   scripts reporting-scd2-sync   Run Reporting_Client_SCD2 pipeline
echo   scripts reporting-incremental Run incremental sync
echo   scripts reporting-verify      Verify data integrity
echo   scripts pipeline-validate     Validate configuration
echo   scripts pipeline-stats        Show pipeline statistics
echo   scripts pipeline-help         Show pipeline CLI help
echo.
echo TWO-STAGE OPERATIONS:
echo   scripts extract               Extract data to archive
echo   scripts load                  Load data from archive
echo   scripts archive-list          List archive batches
echo   scripts archive-stats         Show archive statistics
echo   scripts archive-cleanup       Clean old archive batches
echo.
echo DEVELOPMENT:
echo   scripts logs                  Show container logs
echo   scripts shell                 Access container shell
echo   scripts sql-source            Connect to source database
echo   scripts sql-dest              Connect to destination database
echo.
echo TESTING:
echo   scripts test                  Run all tests
echo   scripts test-unit             Run unit tests only
echo   scripts test-integration      Run integration tests only
echo   scripts test-coverage         Run tests with coverage
echo   scripts test-clean            Clean test environment
echo   scripts test-shell            Start test shell
echo.
echo LOCAL DEVELOPMENT:
echo   scripts local-setup           Setup local Python environment
echo   scripts local-run             Run pipeline locally
echo   scripts local-extract         Extract data locally
echo   scripts local-load            Load data locally
echo   scripts local-test-connection Test ODBC connection
echo.
echo EXAMPLES:
echo   scripts setup                 # Start environment
echo   scripts pipeline-run          # Run pipeline
echo   scripts extract               # Extract data
echo   scripts load                  # Load latest batch
echo   scripts local-setup           # Setup local development
echo.
goto end

:up
echo 🚀 Starting Docker containers...
docker-compose up -d --remove-orphans
echo Waiting for services to be healthy...
timeout /t 10 /nobreak >nul
docker ps
goto end

:down
echo ⏹️ Stopping Docker containers...
docker-compose down
goto end

:setup
echo 🔧 Setting up databases and creating reporting tables...
docker-compose up -d --remove-orphans
echo Waiting for services to be healthy...
timeout /t 15 /nobreak >nul
echo ✅ Environment setup complete!
goto end

:clean
echo 🧹 Cleaning up containers and volumes...
docker-compose down --volumes --remove-orphans
docker system prune -f
goto end

:pipeline-run
echo ▶️ Running pipeline with default configuration...
docker exec dlt-runner python /app/run_pipeline.py run
goto end

:pipeline-run-dev
echo ▶️ Running pipeline with development environment...
docker exec dlt-runner python /app/run_pipeline.py run --environment dev
goto end

:reporting-client-sync
echo 📊 Running Reporting_Client pipeline...
docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client
goto end

:reporting-scd2-sync
echo 📈 Running Reporting_Client_SCD2 pipeline...
docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client_SCD2
goto end

:reporting-incremental
echo 🔄 Running incremental sync for both reporting tables...
docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client Reporting_Client_SCD2
goto end

:reporting-verify
echo ✅ Verifying data integrity...
docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client Reporting_Client_SCD2
goto end

:pipeline-validate
echo 🔍 Validating pipeline configuration...
docker exec dlt-runner python /app/run_pipeline.py validate
goto end

:pipeline-stats
echo 📊 Showing pipeline statistics...
docker exec dlt-runner python /app/run_pipeline.py stats
goto end

:pipeline-help
echo ❓ Showing pipeline help...
docker exec dlt-runner python /app/run_pipeline.py --help
goto end

:extract
echo 📦 Extracting data to archive...
if "%2"=="" (
    docker exec dlt-runner python /app/run_pipeline.py extract
) else (
    docker exec dlt-runner python /app/run_pipeline.py extract --environment %2
)
goto end

:load
echo ⬆️ Loading data from archive...
if "%2"=="" (
    docker exec dlt-runner python /app/run_pipeline.py load --batch latest
) else (
    docker exec dlt-runner python /app/run_pipeline.py load --batch %2
)
goto end

:archive-list
echo 📋 Listing archive batches...
if "%2"=="" (
    docker exec dlt-runner python /app/run_pipeline.py archive list --last 10
) else (
    docker exec dlt-runner python /app/run_pipeline.py archive list --last %2
)
goto end

:archive-stats
echo 📊 Showing archive statistics...
docker exec dlt-runner python /app/run_pipeline.py archive stats
goto end

:archive-cleanup
echo 🧹 Cleaning archive...
if "%2"=="" (
    docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than 30d
) else (
    docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than %2
)
goto end

:logs
echo 📄 Showing container logs...
docker-compose logs -f
goto end

:shell
echo 🐚 Accessing DLT runner container shell...
docker exec -it dlt-runner bash
goto end

:sql-source
echo 🗄️ Connecting to source database...
docker exec -it mssql-source sqlcmd -S localhost -U sa -P SecurePass123
goto end

:sql-dest
echo 🗄️ Connecting to destination database...
docker exec -it mssql-dest sqlcmd -S localhost -U sa -P SecurePass123
goto end

:test
echo 🧪 Running all tests (unit + integration)...
docker exec dlt-runner python -m pytest tests/ -v
goto end

:test-unit
echo ⚡ Running unit tests...
docker exec dlt-runner python -m pytest tests/unit/ -v --tb=short -x
goto end

:test-integration
echo 🔗 Running integration tests...
docker exec dlt-runner python -m pytest tests/integration/ -v
goto end

:test-coverage
echo 📊 Running tests with coverage report...
docker exec dlt-runner python -m pytest tests/ --cov=src --cov-report=html --cov-report=xml
goto end

:test-clean
echo 🧹 Cleaning test containers and volumes...
docker-compose -f docker-compose.test.yaml down --volumes --remove-orphans
goto end

:test-shell
echo 🐚 Starting test container shell...
docker-compose -f docker-compose.test.yaml run --rm test-runner bash
goto end

:local-setup
echo 🖥️ Setting up local development environment...
cd dlt_scripts
echo Creating virtual environment with uv...
uv venv --python 3.11
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Installing dependencies...
uv pip install -r requirements.txt
echo Creating local directories...
if not exist "data\archive" mkdir data\archive
if not exist "data\manifests" mkdir data\manifests
if not exist "logs" mkdir logs
echo ✅ Local environment setup complete!
echo 💡 Don't forget to set your connection string environment variables!
goto end

:local-run
echo ▶️ Running local pipeline...
cd dlt_scripts
if "%2"=="" (
    python run_pipeline.py run --environment local
) else (
    python run_pipeline.py run --environment %2
)
goto end

:local-extract
echo 📦 Extracting data locally...
cd dlt_scripts
if "%2"=="" (
    python run_pipeline.py extract --environment local
) else (
    python run_pipeline.py extract --environment %2
)
goto end

:local-load
echo ⬆️ Loading data locally...
cd dlt_scripts
if "%2"=="" (
    python run_pipeline.py load --environment local --batch latest
) else (
    python run_pipeline.py load --environment local --batch %2
)
goto end

:local-test-connection
echo 🔍 Testing local ODBC connection...
python -c "import pyodbc; print('Available ODBC drivers:'); [print(f'  - {driver}') for driver in pyodbc.drivers()]"
goto end

:end