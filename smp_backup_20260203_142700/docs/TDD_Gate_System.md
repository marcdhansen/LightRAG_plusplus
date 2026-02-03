# TDD Gate System for AutoFlightDirector

A comprehensive Test-Driven Development validation system that blocks commits when test requirements are not met, with emergency bypass capability.

## Overview

The TDD Gate System enforces strict test requirements before allowing code changes, ensuring that all development follows Test-Driven Development principles. This prevents issues like those encountered in task `lightrag-k1f` where performance optimizations were implemented without baseline measurements or adequate testing.

## Components

### 1. TDD Gate Validator (`.agent/scripts/tdd_gate_validator.py`)

Core validation engine that checks:
- **Test file existence**: Ensures test files exist for modified source code
- **Test quality**: Analyzes test functions, assertions, and structure
- **Test coverage**: Validates minimum coverage thresholds (default: 80%)
- **Task-specific requirements**: Performance tasks require baselines, complex tasks require integration tests
- **Emergency bypass**: Allows bypass with justification when absolutely necessary

**Usage**:
```bash
# Standard validation
python .agent/scripts/tdd_gate_validator.py

# With task ID
python .agent/scripts/tdd_gate_validator.py --task-id lightrag-k1f

# Emergency bypass
python .agent/scripts/tdd_gate_validator.py --bypass-justification "Critical security fix"
```

### 2. Enhanced Pre-Flight Check (PFC)

Extended PFC that includes TDD validation:
```bash
python .agent/skills/FlightDirector/scripts/check_flight_readiness.py --pfc
```

**Checks performed**:
- Multi-agent coordination
- Workspace isolation
- Beads system connectivity
- Task artifact verification
- Plan approval freshness
- **TDD Gate validation** ✨ (NEW)

### 3. Pre-commit Hooks

Automatic validation before commits:
- **TDD validation** on all Python file changes
- **Coverage gate** on pushes (minimum 80% coverage)
- Standard linting and formatting checks

### 4. Baseline Framework (`.agent/scripts/baseline_framework.py`)

Establishes performance and quality baselines for optimization tasks:

```bash
# Create extraction performance baseline
python .agent/scripts/baseline_framework.py --task-id lightrag-k1f --baseline-type extraction --test-suite tests/test_extraction.py

# Create general performance baseline
python .agent/scripts/baseline_framework.py --task-id lightrag-oef --baseline-type performance --test-suite tests/test_performance.py

# Compare with existing baseline
python .agent/scripts/baseline_framework.py --task-id lightrag-k1f --compare new_metrics.json
```

### 5. TDD Metadata Enhancer (`.agent/scripts/tdd_metadata_enhancer.py`)

Enhances Beads tasks with TDD requirements:

```bash
# Auto-detect requirements from task
python .agent/scripts/tdd_metadata_enhancer.py --task-id lightrag-k1f --auto-detect

# Manual TDD requirements
python .agent/scripts/tdd_metadata_enhancer.py --task-id lightrag-k1f --tdd-requirements '{"unit_tests_required": true, "coverage_threshold": 85}'

# List enhancement status for all tasks
python .agent/scripts/tdd_metadata_enhancer.py --list-status
```

### 6. Configuration (`.agent/config/tdd_config.yaml`)

Centralized configuration for TDD requirements:

```yaml
tdd_gates:
  enabled: true
  coverage_threshold: 80
  unit_tests_required: true
  integration_tests_for_complex_tasks: true
  baseline_required_for_performance_tasks: true

performance_task_patterns:
  - ".*optimization.*"
  - ".*benchmark.*"
  - ".*performance.*"
  - ".*speed.*"
  - ".*extraction.*prompt.*"
```

## Workflow Integration

### Standard Development Workflow

1. **Task Selection**: Choose task from `bd ready`
2. **Baseline Creation**: For performance tasks, create baseline first
3. **TDD Implementation**: Write tests before implementation
4. **Validation**: TDD gates automatically check compliance
5. **Commit**: Only allowed when all gates pass

### Emergency Bypass Process

**When allowed**:
- Critical security fixes
- Production emergency fixes
- Infrastructure failures
- When explicitly approved by team lead

**Process**:
```bash
# Bypass TDD gates with justification
git commit -m "Fix: Critical security issue" --allow-empty
python .agent/scripts/tdd_gate_validator.py --bypass-justification "Critical security fix - CVE-2024-XXXX"
```

Bypasses are logged and audited.

## Quality Metrics

The system tracks:
- **Test coverage**: Minimum percentage thresholds
- **Test quality**: Assertions per test, function coverage
- **Performance baselines**: Before/after comparisons
- **Task complexity**: Determines required test types
- **Compliance rates**: TDD adherence over time

## Preventing Past Issues

The TDD Gate System specifically prevents:

### ✅ What we prevented:
- **Performance changes without baselines**: Now requires baseline measurements
- **Missing test coverage**: Enforces minimum thresholds
- **No quality tests**: Validates test structure and quality
- **Unvalidated optimizations**: Requires comparison with baseline
- **Emergency commits without justification**: Bypass requires documented reason

### ✅ Specific to lightrag-k1f:
Before TDD gates, lite extraction was implemented without:
- Baseline performance measurements
- Accuracy regression tests
- Token usage comparisons
- Speed improvement verification

Now required:
- ✅ Baseline measurements
- ✅ Performance comparison tests
- ✅ Quality regression prevention
- ✅ Emergency bypass justification

## Configuration

### Environment Variables
```bash
export TDD_COVERAGE_THRESHOLD=85          # Override default coverage
export TDD_BASELINE_REQUIRED=true         # Force baseline requirements
export TDD_STRICT_MODE=true              # Block all violations
```

### Custom Thresholds per Task Type
```yaml
task_complexity_thresholds:
  simple: 3    # Basic tests only
  medium: 7    # Unit + integration tests
  complex: 10  # Comprehensive testing

test_quality_thresholds:
  min_assertions_per_test: 2.0
  quality_score_threshold: 50
```

## Monitoring and Reporting

### TDD Compliance Dashboard
```bash
# Generate compliance report
python .agent/scripts/tdd_metadata_enhancer.py --list-status

# Compare baseline performance
python .agent/scripts/baseline_framework.py --task-id lightrag-k1f --compare baseline.json
```

### Integration with CI/CD
The TDD gates integrate with:
- Pre-commit hooks (local development)
- GitHub Actions (CI validation)
- Beads task metadata (project management)
- AutoFlightDirector coordination

## Success Criteria

The TDD Gate System is successful when:
- ✅ All performance tasks have baseline measurements
- ✅ All code changes meet coverage thresholds
- ✅ Test quality meets minimum standards
- ✅ Emergency bypasses are rare and justified
- ✅ Regression issues are eliminated

## Usage Examples

### Example 1: Performance Optimization Task
```bash
# 1. Create baseline BEFORE changes
python .agent/scripts/baseline_framework.py --task-id lightrag-oef --baseline-type performance --test-suite tests/test_extraction.py

# 2. Implement changes with tests
# (write code and tests)

# 3. Verify TDD compliance
python .agent/scripts/tdd_gate_validator.py --task-id lightrag-oef

# 4. Commit (only if TDD passes)
git add .
git commit -m "Optimize extraction performance"

# 5. Verify no regression
python .agent/scripts/baseline_framework.py --task-id lightrag-oef --compare new_metrics.json
```

### Example 2: Emergency Bypass
```bash
# Critical production issue - bypass TDD temporarily
python .agent/scripts/tdd_gate_validator.py --bypass-justification "Production database corruption - immediate fix required"

# Make the critical fix
git add .
git commit -m "CRITICAL: Fix database corruption"

# Follow up with proper tests
python .agent/scripts/tdd_metadata_enhancer.py --task-id lightrag-emergency --auto-detect
```

This comprehensive TDD Gate System ensures that all development follows strict test-first principles while maintaining the flexibility needed for emergency situations.
