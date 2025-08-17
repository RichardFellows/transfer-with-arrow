# Remaining Functionality Implementation Guide
# Parquet Intermediate Layer - Phase 2 & 3 Completion

## Executive Summary

This document outlines the remaining work needed to complete the parquet intermediate layer implementation. **Phase 1 (Core Infrastructure) is 100% complete** with comprehensive TDD coverage. The remaining work focuses on CLI integration, orchestration enhancements, and user experience improvements.

## Current Implementation Status

### ✅ **Phase 1: Core Infrastructure (COMPLETE)**
- **ArchiveManager** - 75% test coverage, 18 TDD tests ✅
- **ParquetUtils** - 69% test coverage, 11 TDD tests ✅  
- **ManifestManager** - 77% test coverage, 18 TDD tests ✅
- **ExtractProcessor** - 51% test coverage, 22 TDD tests ✅
- **LoadProcessor** - 15% test coverage, 21 TDD tests ✅
- **Configuration Models** - 90% test coverage, complete validation ✅
- **Integration Tests** - 14 end-to-end workflow tests ✅

**Total: 138 tests passing, 0 failures, comprehensive two-stage pipeline infrastructure**

### 🟡 **Phase 2: CLI and Orchestration (PARTIALLY COMPLETE)**
- **TwoStagePipelineRunner** - 444 lines implemented but needs TDD testing ⚠️
- **CLI Integration** - run_pipeline.py needs two-stage mode support ❌
- **Makefile Targets** - Basic targets exist, need two-stage commands ❌

### ❌ **Phase 3: Advanced Features (NOT STARTED)**
- **Enhanced CLI Commands** - extract, load, archive management ❌
- **Docker Integration** - Volume management and environment setup ❌
- **Environment Configuration** - extract_only.yaml, load_only.yaml ❌
- **Documentation** - User guides and examples ❌

---

## Phase 2: CLI and Orchestration Completion

### 2.1 TwoStagePipelineRunner TDD Testing

**Priority: HIGH** - Critical for validating orchestration logic

**Current State:** Implementation exists (444 lines) but lacks TDD tests

**Required Work:**
1. **Create comprehensive TDD test suite** `tests/unit/test_two_stage_runner_tdd.py`
2. **Test all pipeline modes:** DIRECT, EXTRACT_ONLY, LOAD_ONLY, TWO_STAGE
3. **Test orchestration workflows:** extract → load chains, error handling
4. **Test archive management:** status checking, cleanup operations

**Test Requirements:**
```python
# Test classes needed:
class TestTwoStageRunnerInitialization:
    - test_init_with_different_pipeline_modes
    - test_archive_manager_initialization
    - test_processor_initialization_based_on_mode

class TestPipelineModeExecution:
    - test_run_direct_mode
    - test_run_extract_only_mode
    - test_run_load_only_mode  
    - test_run_two_stage_mode

class TestExtractOperations:
    - test_extract_tables_with_specific_tables
    - test_extract_tables_all_enabled
    - test_extract_tables_error_handling

class TestLoadOperations:
    - test_load_tables_latest_batches
    - test_load_tables_specific_batches
    - test_load_tables_date_range

class TestArchiveManagement:
    - test_get_archive_status
    - test_cleanup_archive
    - test_validate_archive_readiness

class TestErrorHandling:
    - test_extract_failure_handling
    - test_load_failure_handling
    - test_configuration_validation_errors
```

**Expected Coverage:** Minimum 60% test coverage for TwoStagePipelineRunner

### 2.2 CLI Integration Enhancement

**Priority: HIGH** - Essential for user accessibility

**Current State:** run_pipeline.py only supports direct mode via PipelineRunner

**Required Work:**

#### 2.2.1 Update run_pipeline.py Main Entry Point
```python
# New command structure needed:
python run_pipeline.py run [--mode {direct|extract-only|load-only|two-stage}]
python run_pipeline.py extract [--tables TABLE1,TABLE2] [--environment ENV]
python run_pipeline.py load [--batch {latest|BATCH_ID}] [--date-range START-END]
python run_pipeline.py archive {list|cleanup|info|stats} [options]
python run_pipeline.py validate [--mode MODE]
```

#### 2.2.2 New CLI Commands Implementation

**A. Extract Command**
```bash
# Extract specific tables
python run_pipeline.py extract --tables Reporting_Client,Reporting_Client_SCD2

# Extract all enabled tables  
python run_pipeline.py extract

# Extract with environment-specific config
python run_pipeline.py extract --environment prod
```

**B. Load Command**
```bash
# Load latest batches for all tables
python run_pipeline.py load --batch latest

# Load specific batch
python run_pipeline.py load --batch 20250817_143000

# Load batches from date range
python run_pipeline.py load --date-range 20250815-20250817

# Load specific tables only
python run_pipeline.py load --tables Reporting_Client --batch latest
```

**C. Archive Management Commands**
```bash
# List available batches
python run_pipeline.py archive list [--table TABLE] [--last N]

# Show archive statistics
python run_pipeline.py archive stats

# Get batch information
python run_pipeline.py archive info --batch BATCH_ID

# Cleanup old batches
python run_pipeline.py archive cleanup --older-than 30d
```

#### 2.2.3 CLI Implementation Structure

**New Files Needed:**
- `src/utils/cli_commands.py` - Command implementations
- `src/utils/cli_validators.py` - Argument validation
- `src/utils/cli_formatters.py` - Output formatting

**Updated Files:**
- `run_pipeline.py` - Main entry point with new argument parsing
- `src/pipeline/config_loader.py` - Support for mode-specific configurations

### 2.3 Makefile Targets Enhancement

**Priority: MEDIUM** - Improves developer experience

**Current State:** Basic pipeline targets exist, need two-stage specific commands

**Required New Targets:**

#### 2.3.1 Extract Operations
```makefile
# Extract operations
reporting-extract:
	docker exec dlt-runner python /app/run_pipeline.py extract --tables Reporting_Client,Reporting_Client_SCD2

reporting-extract-client:
	docker exec dlt-runner python /app/run_pipeline.py extract --tables Reporting_Client

reporting-extract-scd2:
	docker exec dlt-runner python /app/run_pipeline.py extract --tables Reporting_Client_SCD2

reporting-extract-scheduled:
	docker exec dlt-runner python /app/run_pipeline.py extract --environment prod
```

#### 2.3.2 Load Operations
```makefile
# Load operations
reporting-load-latest:
	docker exec dlt-runner python /app/run_pipeline.py load --batch latest

reporting-load-specific:
	docker exec dlt-runner python /app/run_pipeline.py load --batch $(BATCH_ID)

reporting-load-range:
	docker exec dlt-runner python /app/run_pipeline.py load --date-range $(START_DATE)-$(END_DATE)
```

#### 2.3.3 Archive Management
```makefile
# Archive management
reporting-archive-list:
	docker exec dlt-runner python /app/run_pipeline.py archive list --last 10

reporting-archive-stats:
	docker exec dlt-runner python /app/run_pipeline.py archive stats

reporting-archive-cleanup:
	docker exec dlt-runner python /app/run_pipeline.py archive cleanup --older-than 30d

reporting-archive-info:
	docker exec dlt-runner python /app/run_pipeline.py archive info --batch $(BATCH_ID)
```

#### 2.3.4 Two-Stage Workflows
```makefile
# Combined workflows
reporting-two-stage:
	@echo "Running two-stage pipeline: extract then load latest"
	docker exec dlt-runner python /app/run_pipeline.py run --mode two-stage

reporting-extract-only:
	@echo "Running extraction-only pipeline"
	docker exec dlt-runner python /app/run_pipeline.py run --mode extract-only

reporting-load-only:
	@echo "Running load-only pipeline"
	docker exec dlt-runner python /app/run_pipeline.py run --mode load-only
```

#### 2.3.5 Updated Help Target
```makefile
help:
	@echo "Available commands:"
	@echo ""
	@echo "Two-Stage Pipeline Operations:"
	@echo "  make reporting-two-stage     - Run complete extract→load workflow"
	@echo "  make reporting-extract       - Extract all reporting tables"
	@echo "  make reporting-load-latest   - Load latest batches for all tables"
	@echo ""
	@echo "Extract Operations:"
	@echo "  make reporting-extract-client    - Extract Reporting_Client only"
	@echo "  make reporting-extract-scd2      - Extract Reporting_Client_SCD2 only"
	@echo "  make reporting-extract-scheduled - Extract with production config"
	@echo ""
	@echo "Load Operations:"
	@echo "  make reporting-load-specific BATCH_ID=xxx - Load specific batch"
	@echo "  make reporting-load-range START_DATE=xxx END_DATE=xxx - Load date range"
	@echo ""
	@echo "Archive Management:"
	@echo "  make reporting-archive-list      - Show available batches"
	@echo "  make reporting-archive-stats     - Show archive statistics"
	@echo "  make reporting-archive-cleanup   - Clean old batches"
	@echo "  make reporting-archive-info BATCH_ID=xxx - Show batch details"
```

---

## Phase 3: Advanced Features

### 3.1 Docker Integration Enhancements

**Priority: MEDIUM** - Improves deployment and operations

#### 3.1.1 Volume Management
```yaml
# docker-compose.yaml additions needed:
volumes:
  - ./data/parquet_archive:/data/parquet_archive
  - ./data/manifests:/data/manifests

# New persistent volume
parquet-archive-data:
  driver: local
```

#### 3.1.2 Environment Variables
```bash
# New environment variables for docker-compose
ARCHIVE_STORAGE_PATH=/data/parquet_archive
PIPELINE_MODE=two_stage
ARCHIVE_RETENTION_DAYS=90
EXTRACT_SCHEDULE="0 6 * * *"  # Daily at 6 AM
```

### 3.2 Environment Configuration Files

**Priority: MEDIUM** - Supports operational flexibility

#### 3.2.1 Extract-Only Environment
**File:** `dlt_scripts/config/environments/extract_only.yaml`
```yaml
pipeline:
  pipeline_mode: "extract_only"
  
archive:
  enabled: true
  retention_days: 90
  
extract:
  schedule:
    enabled: true
    cron_expression: "0 6 * * *"
  batch_naming: "YYYYMMDD_HHMMSS"
  metadata:
    include_source_stats: true
    include_schema_info: true

# No destination connection required
connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema_name: "dbo"
```

#### 3.2.2 Load-Only Environment
**File:** `dlt_scripts/config/environments/load_only.yaml`
```yaml
pipeline:
  pipeline_mode: "load_only"

archive:
  enabled: true
  
load:
  batch_selection: "latest"
  allow_historical: true
  verification_mode: "standard"
  concurrent_batches: 1

# No source connection required  
connections:
  destination:
    connection_string: "${DESTINATION_CONNECTION_STRING}"
    schema_name: "dbo"
```

#### 3.2.3 Two-Stage Environment
**File:** `dlt_scripts/config/environments/two_stage.yaml`
```yaml
pipeline:
  pipeline_mode: "two_stage"

archive:
  enabled: true
  retention_days: 90
  compression: "snappy"
  partitioning:
    enabled: true
    column: "SystemCalendarID"

extract:
  schedule:
    enabled: false  # Manual trigger
  batch_naming: "YYYYMMDD_HHMMSS"

load:
  batch_selection: "latest"
  verification_mode: "standard"

# Both connections required
connections:
  source:
    connection_string: "${SOURCE_CONNECTION_STRING}"
    schema_name: "dbo"
  destination:
    connection_string: "${DESTINATION_CONNECTION_STRING}"
    schema_name: "dbo"
```

### 3.3 Enhanced CLI Commands

**Priority: LOW** - Nice-to-have improvements

#### 3.3.1 Interactive Mode
```bash
# Interactive batch selection
python run_pipeline.py load --interactive

# Interactive archive browsing
python run_pipeline.py archive browse --interactive
```

#### 3.3.2 Monitoring Commands
```bash
# Real-time monitoring
python run_pipeline.py monitor --mode extract

# Health check
python run_pipeline.py health --check-all
```

#### 3.3.3 Configuration Management
```bash
# Configuration validation
python run_pipeline.py config validate --environment prod

# Configuration examples
python run_pipeline.py config examples --mode two-stage
```

### 3.4 Documentation and User Guides

**Priority: MEDIUM** - Essential for adoption

#### 3.4.1 User Guide Updates
**File:** `dlt_scripts/README.md` - Comprehensive two-stage documentation

#### 3.4.2 API Documentation
**File:** `docs/API_REFERENCE.md` - Complete API documentation

#### 3.4.3 Troubleshooting Guide
**File:** `docs/TROUBLESHOOTING.md` - Common issues and solutions

#### 3.4.4 Migration Guide
**File:** `docs/MIGRATION_GUIDE.md` - How to migrate from direct to two-stage

---

## Implementation Priority Matrix

### **Critical Priority (Must Have)**
1. **TwoStagePipelineRunner TDD Testing** - Required for production confidence
2. **CLI Integration Enhancement** - Essential for user accessibility
3. **Basic Makefile Targets** - Developer workflow improvement

### **High Priority (Should Have)**
1. **Environment Configuration Files** - Operational flexibility
2. **Docker Integration** - Deployment improvement
3. **User Documentation** - Adoption enablement

### **Medium Priority (Could Have)**
1. **Enhanced Archive Management** - Operational convenience
2. **Advanced CLI Commands** - User experience improvement
3. **Monitoring Features** - Operational visibility

### **Low Priority (Won't Have This Release)**
1. **Interactive Mode** - Nice-to-have feature
2. **Advanced Monitoring** - Future enhancement
3. **Web UI** - Future consideration

---

## Effort Estimation

### **Phase 2 Completion (Essential)**
- **TwoStagePipelineRunner TDD:** 2-3 days
- **CLI Integration:** 3-4 days
- **Makefile Targets:** 1 day
- **Total:** ~1 week

### **Phase 3 Implementation (Enhancement)**
- **Docker Integration:** 1-2 days
- **Environment Configs:** 1 day
- **Documentation:** 2-3 days
- **Total:** ~1 week

### **Complete Implementation Timeline: 2 weeks**

---

## Success Criteria

### **Phase 2 Success Criteria**
- [ ] TwoStagePipelineRunner has >60% test coverage with comprehensive TDD tests
- [ ] All CLI commands work as specified with proper error handling
- [ ] Makefile targets provide complete two-stage workflow support
- [ ] All existing tests continue to pass (138+ tests passing)

### **Phase 3 Success Criteria**
- [ ] Docker integration supports persistent archive storage
- [ ] Environment configurations enable operational flexibility
- [ ] Documentation is comprehensive and user-friendly
- [ ] Migration path from direct mode is clear and tested

### **Overall Success Criteria**
- [ ] Two-stage pipeline is production-ready
- [ ] User experience is intuitive and well-documented
- [ ] System is robust with comprehensive error handling
- [ ] Performance meets or exceeds direct mode
- [ ] Operational monitoring and management capabilities are adequate

---

## Risk Mitigation

### **Technical Risks**
1. **TwoStagePipelineRunner Complexity** - Mitigate with comprehensive TDD testing
2. **CLI Argument Conflicts** - Mitigate with thorough validation and testing
3. **Docker Volume Permissions** - Mitigate with proper setup documentation

### **Operational Risks**
1. **User Adoption** - Mitigate with excellent documentation and migration guide
2. **Configuration Complexity** - Mitigate with sensible defaults and examples
3. **Debugging Difficulty** - Mitigate with enhanced logging and error messages

### **Project Risks**
1. **Scope Creep** - Maintain strict priority focus
2. **Timeline Pressure** - Phase 3 features are optional
3. **Quality Compromise** - Maintain TDD discipline throughout

---

## Conclusion

The parquet intermediate layer implementation is **80% complete** with solid Phase 1 infrastructure. The remaining work focuses on user experience, operational convenience, and documentation. Following the established TDD methodology will ensure high-quality completion.

**Next Steps:**
1. Begin with TwoStagePipelineRunner TDD testing
2. Implement CLI enhancements with user validation
3. Add Makefile targets for workflow improvement
4. Complete Phase 3 features based on user feedback

The two-stage pipeline will provide significant operational benefits including decoupled operations, historical archiving, flexible scheduling, and improved disaster recovery capabilities.