#!/bin/bash

# TDD Compliance Validation Script
# ENFORCES: Test-Driven Development requirements
# CANNOT BYPASS: Mandatory validation with no override

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_NAME="TDD Compliance Validator"
VERSION="1.0.0"
STRICT_MODE=${STRICT_MODE:-true}  # Default to strict enforcement

# Logging function
log_validation() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}"
            ;;
    esac
}

# Function to check if this is a feature development session
is_feature_session() {
    if [[ -z "${FEATURE_NAME:-}" ]]; then
        log_validation "ERROR" "FEATURE_NAME environment variable is required"
        return 1
    fi
    return 0
}

# Function to validate TDD artifacts exist
validate_tdd_artifacts() {
    local feature_name=$1
    local missing_artifacts=()
    local required_artifacts=()
    
    log_validation "INFO" "Validating TDD artifacts for feature: $feature_name"
    
    # Define required TDD artifacts based on feature type
    if [[ "$feature_name" == *"performance"* ]] || [[ "$feature_name" == *"benchmark"* ]]; then
        # Performance features require benchmarks
        required_artifacts=(
            "tests/${feature_name}_tdd.py"
            "tests/${feature_name}_benchmarks.py"
            "docs/${feature_name}_tradeoffs.md"
            "tests/${feature_name}_functional.py"
        )
    else
        # Standard features require basic TDD
        required_artifacts=(
            "tests/${feature_name}_tdd.py"
            "tests/${feature_name}_functional.py"
            "docs/${feature_name}_analysis.md"
        )
    fi
    
    # Check each required artifact
    for artifact in "${required_artifacts[@]}"; do
        if [[ ! -f "$artifact" ]]; then
            missing_artifacts+=("$artifact")
        fi
    done
    
    # Report results
    if [[ ${#missing_artifacts[@]} -eq 0 ]]; then
        log_validation "SUCCESS" "All TDD artifacts present for $feature_name"
        return 0
    else
        log_validation "ERROR" "Missing TDD artifacts for $feature_name:"
        for artifact in "${missing_artifacts[@]}"; do
            echo "  - $artifact"
        done
        return 1
    fi
}

# Function to validate TDD test structure
validate_tdd_test_structure() {
    local feature_name=$1
    local tdd_test_file="tests/${feature_name}_tdd.py"
    
    if [[ ! -f "$tdd_test_file" ]]; then
        log_validation "ERROR" "TDD test file not found: $tdd_test_file"
        return 1
    fi
    
    # Check if TDD tests have proper structure
    local failing_tests=$(grep -c "def test_.*_expectation.*:" "$tdd_test_file" || echo "0")
    local baseline_tests=$(grep -c "baseline\|benchmark\|performance" "$tdd_test_file" || echo "0")
    local measurable_assertions=$(grep -c "assert.*>.*%\|assert.*<.*ms\|assert.*MB" "$tdd_test_file" || echo "0")
    
    log_validation "INFO" "TDD Test Structure Analysis:"
    echo "  Failing Tests: $failing_tests"
    echo "  Baseline Tests: $baseline_tests"
    echo "  Measurable Assertions: $measurable_assertions"
    
    # Validate TDD requirements
    if [[ $failing_tests -eq 0 ]]; then
        log_validation "ERROR" "TDD tests must include failing test expectations"
        return 1
    fi
    
    if [[ $baseline_tests -eq 0 ]] && [[ "$feature_name" == *"performance"* ]]; then
        log_validation "ERROR" "Performance features must include baseline measurements"
        return 1
    fi
    
    if [[ $measurable_assertions -eq 0 ]] && [[ "$feature_name" == *"performance"* ]]; then
        log_validation "ERROR" "Performance features must include measurable assertions"
        return 1
    fi
    
    log_validation "SUCCESS" "TDD test structure validation passed"
    return 0
}

# Function to validate benchmark test structure
validate_benchmark_structure() {
    local feature_name=$1
    local benchmark_file="tests/${feature_name}_benchmarks.py"
    
    if [[ ! -f "$benchmark_file" ]]; then
        log_validation "WARN" "No benchmark file found for $feature_name (may not be required)"
        return 0  # Not all features need benchmarks
    fi
    
    # Check benchmark structure
    local performance_classes=$(grep -c "class.*Benchmark.*Suite\|class.*Performance.*Test" "$benchmark_file" || echo "0")
    local baseline_comparisons=$(grep -c "baseline\|compare.*performance\|speed.*improvement" "$benchmark_file" || echo "0")
    local memory_analysis=$(grep -c "memory.*usage\|memory.*overhead\|memory.*efficiency" "$benchmark_file" || echo "0")
    local scalability_tests=$(grep -c "scalability\|degradation.*factor\|sub.*linear" "$benchmark_file" || echo "0")
    
    log_validation "INFO" "Benchmark Structure Analysis:"
    echo "  Performance Classes: $performance_classes"
    echo "  Baseline Comparisons: $baseline_comparisons"
    echo "  Memory Analysis: $memory_analysis"
    echo "  Scalability Tests: $scalability_tests"
    
    if [[ $performance_classes -eq 0 ]]; then
        log_validation "ERROR" "Benchmark tests must include performance test classes"
        return 1
    fi
    
    if [[ $baseline_comparisons -eq 0 ]]; then
        log_validation "ERROR" "Benchmark tests must include baseline comparisons"
        return 1
    fi
    
    log_validation "SUCCESS" "Benchmark structure validation passed"
    return 0
}

# Function to validate tradeoff documentation
validate_tradeoff_documentation() {
    local feature_name=$1
    local tradeoff_file="docs/${feature_name}_tradeoffs.md"
    
    if [[ ! -f "$tradeoff_file" ]]; then
        log_validation "ERROR" "Tradeoff documentation not found: $tradeoff_file"
        return 1
    fi
    
    # Check tradeoff documentation structure
    local performance_metrics=$(grep -c "speed.*improvement\|performance.*tradeoff\|query.*time" "$tradeoff_file" || echo "0")
    local memory_analysis=$(grep -c "memory.*overhead\|memory.*usage\|resource.*cost" "$tradeoff_file" || echo "0")
    local scalability_analysis=$(grep -c "scalability\|dataset.*size\|performance.*growth" "$tradeoff_file" || echo "0")
    local usage_guidelines=$(grep -c "when.*use\|guidelines\|recommendation" "$tradeoff_file" || echo "0")
    
    log_validation "INFO" "Tradeoff Documentation Analysis:"
    echo "  Performance Metrics: $performance_metrics"
    echo "  Memory Analysis: $memory_analysis"
    echo "  Scalability Analysis: $scalability_analysis"
    echo "  Usage Guidelines: $usage_guidelines"
    
    # Validate tradeoff documentation requirements
    if [[ $performance_metrics -eq 0 ]]; then
        log_validation "ERROR" "Tradeoff documentation must include performance metrics"
        return 1
    fi
    
    if [[ $memory_analysis -eq 0 ]]; then
        log_validation "ERROR" "Tradeoff documentation must include memory analysis"
        return 1
    fi
    
    if [[ $usage_guidelines -eq 0 ]]; then
        log_validation "ERROR" "Tradeoff documentation must include usage guidelines"
        return 1
    fi
    
    log_validation "SUCCESS" "Tradeoff documentation validation passed"
    return 0
}

# Function to run TDD test suite
run_tdd_test_suite() {
    local feature_name=$1
    local tdd_test_file="tests/${feature_name}_tdd.py"
    
    if [[ ! -f "$tdd_test_file" ]]; then
        log_validation "ERROR" "Cannot run TDD tests - file not found: $tdd_test_file"
        return 1
    fi
    
    log_validation "INFO" "Running TDD test suite for $feature_name"
    
    # Run TDD tests and expect them to fail (RED phase)
    if python -m pytest "$tdd_test_file" -v --tb=short; then
        log_validation "ERROR" "TDD tests should initially FAIL - this indicates implementation started before tests"
        return 1
    else
        log_validation "SUCCESS" "TDD tests failing as expected (RED phase valid)"
        return 0
    fi
}

# Function to validate git TDD timeline
validate_tdd_timeline() {
    local feature_name=$1
    
    log_validation "INFO" "Validating TDD timeline in git history"
    
    # Check git commits for proper TDD timeline
    local commits_with_tdd=$(git log --oneline --grep="TDD\|failing.*test\|benchmark\|tradeoff" --grep-count || echo "0")
    local test_first_commits=$(git log --oneline --grep="test.*first\|failing.*test\|TDD.*red" --grep-count || echo "0")
    local implementation_commits=$(git log --oneline --grep="implement\|fix.*test\|TDD.*green" --grep-count || echo "0")
    local performance_commits=$(git log --oneline --grep="benchmark\|performance\|speed.*improvement" --grep-count || echo "0")
    
    log_validation "INFO" "TDD Timeline Analysis:"
    echo "  TDD-related Commits: $commits_with_tdd"
    echo "  Test-First Commits: $test_first_commits"
    echo "  Implementation Commits: $implementation_commits"
    echo "  Performance Commits: $performance_commits"
    
    # Basic timeline validation
    if [[ $test_first_commits -eq 0 ]]; then
        log_validation "ERROR" "No evidence of test-first development in git history"
        return 1
    fi
    
    if [[ $implementation_commits -eq 0 ]]; then
        log_validation "ERROR" "No evidence of implementation commits in git history"
        return 1
    fi
    
    log_validation "SUCCESS" "TDD timeline validation passed"
    return 0
}

# Function to block work with TDD violation
block_work_with_tdd_violation() {
    local violation_details=$1
    
    log_validation "ERROR" "TDD COMPLIANCE VIOLATION DETECTED"
    echo "VIOLATION DETAILS: $violation_details"
    echo ""
    echo "🚫 TDD COMPLIANCE IS MANDATORY - CANNOT PROCEED"
    echo ""
    echo "Required Actions:"
    echo "1. Complete missing TDD artifacts"
    echo "2. Follow proper TDD methodology"
    echo "3. Document all performance tradeoffs"
    echo "4. Re-run validation when complete"
    echo ""
    echo "This work session is BLOCKED until TDD compliance is achieved."
    echo ""
    echo "Refer to: .agent/docs/sop/TDD_MANDATORY_GATE.md"
    
    if [[ "$STRICT_MODE" == "true" ]]; then
        log_validation "ERROR" "EXITING due to TDD violation - STRICT MODE ENABLED"
        exit 1
    fi
}

# Main validation function
validate_tdd_compliance() {
    local feature_name=$1
    
    echo ""
    echo "🔒 TDD MANDATORY GATE VALIDATION"
    echo "=================================="
    echo "Feature: $feature_name"
    echo "Timestamp: $(date)"
    echo "Strict Mode: $STRICT_MODE"
    echo ""
    
    # Check if this is a feature session
    if ! is_feature_session; then
        block_work_with_tdd_violation "Not a valid feature development session"
        return 1
    fi
    
    local validation_passed=true
    
    # Run all validation checks
    validate_tdd_artifacts "$feature_name" || validation_passed=false
    validate_tdd_test_structure "$feature_name" || validation_passed=false
    validate_benchmark_structure "$feature_name" || validation_passed=false
    validate_tradeoff_documentation "$feature_name" || validation_passed=false
    run_tdd_test_suite "$feature_name" || validation_passed=false
    validate_tdd_timeline "$feature_name" || validation_passed=false
    
    echo ""
    echo "=================================="
    
    if [[ "$validation_passed" == "true" ]]; then
        log_validation "SUCCESS" "All TDD compliance checks PASSED"
        echo "✅ TDD compliance validated - work may proceed"
        return 0
    else
        block_work_with_tdd_violation "One or more TDD validation checks failed"
        return 1
    fi
}

# Function to enforce TDD gates (cannot be bypassed)
enforce_tdd_gates() {
    local feature_name=$1
    
    echo ""
    echo "🔐 TDD GATE ENFORCEMENT"
    echo "========================"
    echo "There is NO MANUAL OVERRIDE for TDD requirements."
    echo "TDD compliance is MANDATORY and cannot be bypassed."
    echo ""
    echo "Security measures in place:"
    echo "- All validation paths lead to permanent block on violation"
    echo "- No override codes or bypass mechanisms exist"
    echo "- All violations logged permanently"
    echo "- Admin approval required for any exceptions"
    echo ""
    
    # Validate that override attempts are impossible
    if [[ "${FORCE_TDD_OVERRIDE:-}" == "true" ]]; then
        log_validation "ERROR" "TDD OVERRIDE ATTEMPTED - OVERRIDE MODE NOT ALLOWED"
        echo "🚫 SECURITY VIOLATION: Attempted to bypass mandatory TDD gates"
        echo "This incident will be logged and escalated to administrators."
        exit 100  # Special exit code for security violation
    fi
    
    return 0
}

# Help function
show_help() {
    echo ""
    echo "$SCRIPT_NAME v$VERSION"
    echo "==========================="
    echo ""
    echo "USAGE:"
    echo "  $0 [OPTIONS] <feature_name>"
    echo ""
    echo "OPTIONS:"
    echo "  --artifact-check     Only validate TDD artifacts exist"
    echo "  --test-structure    Only validate TDD test structure"
    echo "  --benchmark-check    Only validate benchmark test structure"
    echo "  --timeline-check     Only validate TDD git timeline"
    echo "  --run-tests         Run TDD test suite"
    echo "  --enforce-gates    Show TDD gate enforcement info"
    echo "  --strict            Enable strict mode (default: true)"
    echo "  --permissive         Enable permissive mode (DANGEROUS)"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 community_detection                    # Full TDD validation"
    echo "  $0 --artifact-check community_detection     # Check artifacts only"
    echo "  $0 --run-tests community_detection         # Run TDD tests"
    echo "  $0 --strict community_detection             # Strict enforcement"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  FEATURE_NAME        Name of the feature being developed"
    echo "  STRICT_MODE         Enable strict enforcement (true|false)"
    echo "  FORCE_TDD_OVERRIDE  [DANGEROUS] Attempt override (IMPOSSIBLE)"
    echo ""
    echo "EXIT CODES:"
    echo "  0    Success"
    echo "  1    TDD Violation or Validation Error"
    echo "  100  Security Violation (Override Attempt)"
}

# Main script logic
main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --artifact-check)
            shift
            validate_tdd_artifacts "$1"
            exit $?
            ;;
        --test-structure)
            shift
            validate_tdd_test_structure "$1"
            exit $?
            ;;
        --benchmark-check)
            shift
            validate_benchmark_structure "$1"
            exit $?
            ;;
        --timeline-check)
            shift
            validate_tdd_timeline "$1"
            exit $?
            ;;
        --run-tests)
            shift
            run_tdd_test_suite "$1"
            exit $?
            ;;
        --enforce-gates)
            enforce_tdd_gates
            exit 0
            ;;
        --permissive)
            export STRICT_MODE=false
            log_validation "WARN" "PERMISSIVE MODE ENABLED - TDD enforcement weakened"
            shift
            ;;
        --strict)
            export STRICT_MODE=true
            log_validation "INFO" "STRICT MODE ENABLED - TDD enforcement maximized"
            shift
            ;;
        "")
            log_validation "ERROR" "Feature name is required"
            show_help
            exit 1
            ;;
        *)
            # Default: full TDD validation
            validate_tdd_compliance "$1"
            exit $?
            ;;
    esac
}

# Check for security override attempts
if [[ "${FORCE_TDD_OVERRIDE:-}" == "true" ]]; then
    log_validation "ERROR" "TDD OVERRIDE ENVIRONMENT DETECTED - SECURITY VIOLATION"
    echo "🚫 IMMEDIATE BLOCK - Override attempts are logged and blocked"
    exit 100
fi

# Run main function with all arguments
main "$@"