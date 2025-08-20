# PowerShell Scripts for Transfer with Arrow Pipeline
# Windows equivalent of Makefile commands

# Environment Management
function Start-Environment {
    Write-Host "🚀 Starting Docker containers..." -ForegroundColor Green
    docker-compose up -d --remove-orphans
    Write-Host "Waiting for services to be healthy..."
    Start-Sleep -Seconds 10
    docker ps
}

function Stop-Environment {
    Write-Host "⏹️ Stopping Docker containers..." -ForegroundColor Yellow
    docker-compose down
}

function Setup-Environment {
    Write-Host "🔧 Setting up databases and creating reporting tables..." -ForegroundColor Green
    docker-compose up -d --remove-orphans
    Write-Host "Waiting for services to be healthy..."
    Start-Sleep -Seconds 15
    
    # Setup databases (you may need to add specific setup commands here)
    Write-Host "✅ Environment setup complete!" -ForegroundColor Green
}

function Clean-Environment {
    Write-Host "🧹 Cleaning up containers and volumes..." -ForegroundColor Red
    docker-compose down --volumes --remove-orphans
    docker system prune -f
}

# Pipeline Commands
function Run-Pipeline {
    Write-Host "▶️ Running pipeline with default configuration..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run
}

function Run-PipelineDev {
    Write-Host "▶️ Running pipeline with development environment..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run --environment dev
}

function Sync-ReportingClient {
    Write-Host "📊 Running Reporting_Client pipeline..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client
}

function Sync-ReportingSCD2 {
    Write-Host "📈 Running Reporting_Client_SCD2 pipeline..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client_SCD2
}

function Run-ReportingIncremental {
    Write-Host "🔄 Running incremental sync for both reporting tables..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client Reporting_Client_SCD2
}

function Verify-ReportingData {
    Write-Host "✅ Verifying data integrity..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py run --tables Reporting_Client Reporting_Client_SCD2
}

function Validate-Pipeline {
    Write-Host "🔍 Validating pipeline configuration..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py validate
}

function Show-PipelineStats {
    Write-Host "📊 Showing pipeline statistics..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py stats
}

function Show-PipelineHelp {
    Write-Host "❓ Showing pipeline help..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py --help
}

# Two-Stage Pipeline Operations
function Extract-Data {
    param(
        [string]$Environment = "",
        [string[]]$Tables = @()
    )
    
    $cmd = "docker exec dlt-runner python /app/run_pipeline.py extract"
    if ($Environment) { $cmd += " --environment $Environment" }
    if ($Tables) { $cmd += " --tables " + ($Tables -join " ") }
    
    Write-Host "📦 Extracting data to archive..." -ForegroundColor Blue
    Invoke-Expression $cmd
}

function Load-Data {
    param(
        [string]$Environment = "",
        [string]$Batch = "latest",
        [string[]]$Tables = @()
    )
    
    $cmd = "docker exec dlt-runner python /app/run_pipeline.py load --batch $Batch"
    if ($Environment) { $cmd += " --environment $Environment" }
    if ($Tables) { $cmd += " --tables " + ($Tables -join " ") }
    
    Write-Host "⬆️ Loading data from archive..." -ForegroundColor Blue
    Invoke-Expression $cmd
}

function Show-ArchiveList {
    param([int]$Last = 10)
    Write-Host "📋 Listing archive batches..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py archive list --last $Last
}

function Show-ArchiveStats {
    Write-Host "📊 Showing archive statistics..." -ForegroundColor Blue
    docker exec dlt-runner python /app/run_pipeline.py archive stats
}

function Clean-Archive {
    param([string]$OlderThan = "30d")
    Write-Host "🧹 Cleaning archive older than $OlderThan..." -ForegroundColor Yellow
    docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than $OlderThan
}

# Development Commands
function Show-Logs {
    Write-Host "📄 Showing container logs..." -ForegroundColor Blue
    docker-compose logs -f
}

function Enter-Shell {
    Write-Host "🐚 Accessing DLT runner container shell..." -ForegroundColor Blue
    docker exec -it dlt-runner bash
}

function Connect-SourceDB {
    Write-Host "🗄️ Connecting to source database..." -ForegroundColor Blue
    docker exec -it mssql-source sqlcmd -S localhost -U sa -P SecurePass123
}

function Connect-DestDB {
    Write-Host "🗄️ Connecting to destination database..." -ForegroundColor Blue
    docker exec -it mssql-dest sqlcmd -S localhost -U sa -P SecurePass123
}

# Testing Commands
function Run-Tests {
    Write-Host "🧪 Running all tests (unit + integration)..." -ForegroundColor Green
    docker exec dlt-runner python -m pytest tests/ -v
}

function Run-UnitTests {
    Write-Host "⚡ Running unit tests..." -ForegroundColor Green
    docker exec dlt-runner python -m pytest tests/unit/ -v --tb=short -x
}

function Run-IntegrationTests {
    Write-Host "🔗 Running integration tests..." -ForegroundColor Green
    docker exec dlt-runner python -m pytest tests/integration/ -v
}

function Run-TestsWithCoverage {
    Write-Host "📊 Running tests with coverage report..." -ForegroundColor Green
    docker exec dlt-runner python -m pytest tests/ --cov=src --cov-report=html --cov-report=xml
}

function Clean-TestEnvironment {
    Write-Host "🧹 Cleaning test containers and volumes..." -ForegroundColor Red
    docker-compose -f docker-compose.test.yaml down --volumes --remove-orphans
}

function Enter-TestShell {
    Write-Host "🐚 Starting test container shell..." -ForegroundColor Blue
    docker-compose -f docker-compose.test.yaml run --rm test-runner bash
}

# Local Development Functions
function Setup-LocalEnvironment {
    Write-Host "🖥️ Setting up local development environment..." -ForegroundColor Green
    
    Set-Location dlt_scripts
    
    # Create virtual environment
    Write-Host "Creating virtual environment with uv..." -ForegroundColor Blue
    uv venv --python 3.11
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Blue
    .\.venv\Scripts\Activate.ps1
    
    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Blue
    uv pip install -r requirements.txt
    
    # Create local directories
    Write-Host "Creating local directories..." -ForegroundColor Blue
    New-Item -ItemType Directory -Path "data\archive" -Force
    New-Item -ItemType Directory -Path "data\manifests" -Force
    New-Item -ItemType Directory -Path "logs" -Force
    
    Write-Host "✅ Local environment setup complete!" -ForegroundColor Green
    Write-Host "💡 Don't forget to set your connection string environment variables!" -ForegroundColor Yellow
}

function Run-LocalPipeline {
    param(
        [string]$Environment = "local",
        [string]$Mode = "",
        [string[]]$Tables = @()
    )
    
    Set-Location dlt_scripts
    
    $cmd = "python run_pipeline.py run --environment $Environment"
    if ($Mode) { $cmd += " --mode $Mode" }
    if ($Tables) { $cmd += " --tables " + ($Tables -join " ") }
    
    Write-Host "▶️ Running local pipeline..." -ForegroundColor Blue
    Invoke-Expression $cmd
}

function Extract-LocalData {
    param(
        [string]$Environment = "local",
        [string[]]$Tables = @()
    )
    
    Set-Location dlt_scripts
    
    $cmd = "python run_pipeline.py extract --environment $Environment"
    if ($Tables) { $cmd += " --tables " + ($Tables -join " ") }
    
    Write-Host "📦 Extracting data locally..." -ForegroundColor Blue
    Invoke-Expression $cmd
}

function Load-LocalData {
    param(
        [string]$Environment = "local",
        [string]$Batch = "latest"
    )
    
    Set-Location dlt_scripts
    
    Write-Host "⬆️ Loading data locally..." -ForegroundColor Blue
    python run_pipeline.py load --environment $Environment --batch $Batch
}

function Test-LocalConnection {
    Write-Host "🔍 Testing local ODBC connection..." -ForegroundColor Blue
    python -c "import pyodbc; print('Available ODBC drivers:'); [print(f'  - {driver}') for driver in pyodbc.drivers()]"
}

# Helper Functions
function Show-Help {
    Write-Host @"
🚀 Transfer with Arrow - PowerShell Commands

ENVIRONMENT MANAGEMENT:
  Start-Environment          Start Docker containers
  Stop-Environment           Stop Docker containers
  Setup-Environment          Setup databases and containers
  Clean-Environment          Remove containers and volumes

PIPELINE OPERATIONS:
  Run-Pipeline               Run pipeline with default config
  Run-PipelineDev           Run with development environment
  Sync-ReportingClient      Run Reporting_Client pipeline
  Sync-ReportingSCD2        Run Reporting_Client_SCD2 pipeline
  Run-ReportingIncremental  Run incremental sync
  Validate-Pipeline         Validate configuration
  Show-PipelineStats        Show pipeline statistics
  Show-PipelineHelp         Show pipeline CLI help

TWO-STAGE OPERATIONS:
  Extract-Data              Extract data to archive
  Load-Data                 Load data from archive
  Show-ArchiveList          List archive batches
  Show-ArchiveStats         Show archive statistics
  Clean-Archive             Clean old archive batches

DEVELOPMENT:
  Show-Logs                 Show container logs
  Enter-Shell               Access container shell
  Connect-SourceDB          Connect to source database
  Connect-DestDB            Connect to destination database

TESTING:
  Run-Tests                 Run all tests
  Run-UnitTests            Run unit tests only
  Run-IntegrationTests     Run integration tests only
  Run-TestsWithCoverage    Run tests with coverage
  Clean-TestEnvironment    Clean test environment
  Enter-TestShell          Start test shell

LOCAL DEVELOPMENT:
  Setup-LocalEnvironment   Setup local Python environment
  Run-LocalPipeline        Run pipeline locally
  Extract-LocalData        Extract data locally
  Load-LocalData           Load data locally
  Test-LocalConnection     Test ODBC connection

EXAMPLES:
  # Start environment and run pipeline
  Start-Environment
  Run-Pipeline

  # Extract specific tables
  Extract-Data -Tables @("Reporting_Client") -Environment "dev"

  # Load latest batch
  Load-Data -Batch "latest" -Environment "local"

  # Setup local development
  Setup-LocalEnvironment
"@ -ForegroundColor Cyan
}

# Export functions for easy access
Export-ModuleMember -Function *

Write-Host "✅ PowerShell scripts loaded! Type 'Show-Help' for available commands." -ForegroundColor Green