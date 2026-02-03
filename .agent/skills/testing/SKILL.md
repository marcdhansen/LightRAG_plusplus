# 🧪 Testing Skill

**Purpose**: Manages comprehensive testing framework for LightRAG, including test execution, data management, and benchmark coordination.

## 🎯 Mission
- Execute test suites and generate reports
- Manage test data and environments
- Coordinate with evaluation frameworks
- Maintain test quality and coverage standards

## 🛠️ Tools & Scripts

### Test Execution
```bash
# Run full test suite
python3 -m pytest tests/ --verbose --cov=lightrag

# Run specific test category
python3 -m pytest tests/test_core.py --performance
```

### Test Data Management
```bash
# Generate test datasets
python3 scripts/generate_test_data.py --size 1000

# Validate test data quality
python3 scripts/validate_test_data.py
```

### Environment Setup
```bash
# Setup test environment
python3 scripts/setup_test_env.py --environment integration

# Cleanup test artifacts
python3 scripts/cleanup_tests.py
```

### Coverage Reporting
```bash
# Generate coverage report
python3 -m pytest --cov=lightrag --cov-report=html

# Check coverage thresholds
python3 scripts/check_coverage.py --threshold 80
```

## 📋 Usage Examples

### Basic Testing
```bash
# Run all tests
/testing --run-all

# Run specific test suite
/testing --run-suite performance

# Run tests with specific markers
/testing --run --marker integration
```

### Test Management
```bash
# Generate test report
/testing --report --format html

# Check test health
/testing --health-check

# Update test data
/testing --update-data --source production
```

### Environment Management
```bash
# Setup fresh test environment
/testing --setup-env --clean

# Run tests in isolation
/testing --run-isolated --test-file test_extraction.py

# Cleanup test artifacts
/testing --cleanup --older-than 24h
```

## 🔗 Integration Points
- **Evaluation Skill**: Coordinate test and evaluation pipelines
- **CI/CD**: Run tests in quality gates
- **Process Skill**: Manage test stages in pipeline
- **Beads**: Track test-related tasks and issues

## 📊 Metrics Tracked
- Test coverage percentage
- Test execution time and trends
- Pass/fail rates by test category
- Test environment setup time

## 🎯 Key Files
- `tests/` - Comprehensive test suite
- `pytest.ini` - Test configuration
- `scripts/generate_test_data.py` - Test data generator
- `coverage/` - Coverage reports and HTML output
