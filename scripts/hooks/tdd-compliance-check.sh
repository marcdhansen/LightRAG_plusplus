#!/bin/bash
# Enhanced TDD Compliance Check for Pre-commit
# Validates TDD artifacts for feature/agent/task branches

# Allow failure in CI environments for graceful degradation
if [[ "$GITHUB_ACTIONS" == "true" || "$CI" == "true" ]]; then
    set +e  # Don't exit on error in CI
    echo "🤖 Running in CI mode - using lenient validation"
else
    set -e  # Strict mode for local development
    echo "🔧 Running in local development mode - strict validation"
fi

echo "🔍 Running TDD Compliance Check..."

# Function to check if we're in CI and should be more lenient
is_ci() {
    [[ "$GITHUB_ACTIONS" == "true" || "$CI" == "true" ]]
}

# Get current branch name
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")

# In CI, try to get branch name from environment if git fails
if [[ -z "$BRANCH_NAME" && -n "$GITHUB_REF_NAME" ]]; then
    BRANCH_NAME="$GITHUB_REF_NAME"
fi

# Skip for non-feature branches
if [[ ! "$BRANCH_NAME" =~ ^(feature|agent|task)/.+ ]]; then
    echo "ℹ️ Not a feature/agent/task branch (branch: $BRANCH_NAME), skipping TDD artifact validation"
    exit 0
fi

# Extract feature name (get last part after slashes)
FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's/^\(feature\|agent\|task\)\///' | sed 's/.*\///' | sed 's/^task-//')
echo "📋 Validating TDD artifacts for feature: $FEATURE_NAME"

# Check required artifacts
MISSING_ARTIFACTS=()
ERRORS=()
WARNINGS=()

# Create test and docs directories if they don't exist (CI-friendly)
mkdir -p tests docs

# Check TDD test file
if [[ ! -f "tests/${FEATURE_NAME}_tdd.py" ]]; then
    MISSING_ARTIFACTS+=("tests/${FEATURE_NAME}_tdd.py")
fi

# Check functional test file
if [[ ! -f "tests/${FEATURE_NAME}_functional.py" ]]; then
    MISSING_ARTIFACTS+=("tests/${FEATURE_NAME}_functional.py")
fi

# Check documentation
if [[ ! -f "docs/${FEATURE_NAME}_analysis.md" ]]; then
    MISSING_ARTIFACTS+=("docs/${FEATURE_NAME}_analysis.md")
fi

# Report results
if [[ ${#MISSING_ARTIFACTS[@]} -eq 0 ]]; then
    echo "✅ All TDD artifacts present for feature: $FEATURE_NAME"

    # Quick quality checks
    TDD_FILE="tests/${FEATURE_NAME}_tdd.py"
    if [[ -f "$TDD_FILE" ]]; then
        TEST_COUNT=$(grep -c "def test_" "$TDD_FILE" 2>/dev/null || echo "0")
        ASSERTION_COUNT=$(grep -c "assert" "$TDD_FILE" 2>/dev/null || echo "0")

        if [[ $TEST_COUNT -eq 0 ]]; then
            ERRORS+=("TDD test file exists but contains no test functions")
        elif [[ $ASSERTION_COUNT -eq 0 ]]; then
            WARNINGS+=("TDD test file contains no assertions")
        fi

        echo "  📊 Test functions: $TEST_COUNT, Assertions: $ASSERTION_COUNT"
    fi

else
    echo "❌ Missing TDD artifacts for feature: $FEATURE_NAME"

    for artifact in "${MISSING_ARTIFACTS[@]}"; do
        if is_ci; then
            WARNINGS+=("Missing artifact in CI: $artifact (auto-creation recommended)")
        else
            ERRORS+=("Missing required artifact: $artifact")
        fi
    done

    echo ""
    if is_ci; then
        echo "🤖 CI Environment: Auto-creating missing TDD artifacts..."
        # Try to auto-create missing artifacts in CI
        if command -v python >/dev/null 2>&1 && [[ -f "./scripts/create-tdd-artifacts.py" ]]; then
            python "./scripts/create-tdd-artifacts.py" "$FEATURE_NAME" --force || echo "⚠️ Auto-creation failed"
        elif [[ -f "./scripts/create-tdd-artifacts.sh" ]]; then
            ./scripts/create-tdd-artifacts.sh "$FEATURE_NAME" || echo "⚠️ Auto-creation failed"
        else
            echo "ℹ️ No auto-creation script available"
        fi
        echo "🛠️  SOLUTION OPTIONS:"
        echo ""
        echo "Option 1: Auto-generate all missing artifacts"
        echo "  ./scripts/create-tdd-artifacts.sh $FEATURE_NAME"
        echo ""
        echo "Option 2: Run development check (more guidance)"
        echo "  ./scripts/dev-start-check.sh"
        echo ""
        echo "Option 3: Manual creation"
        echo "  Create the missing files listed above with proper TDD structure"
        echo ""
    else
        echo "🛠️  SOLUTION OPTIONS:"
        echo ""
        echo "Option 1: Auto-generate all missing artifacts"
        echo "  ./scripts/create-tdd-artifacts.sh $FEATURE_NAME"
        echo ""
        echo "Option 2: Run development check (more guidance)"
        echo "  ./scripts/dev-start-check.sh"
        echo ""
        echo "Option 3: Manual creation"
        echo "  Create the missing files listed above with proper TDD structure"
        echo ""
    fi
fi

# Check for any Python files being committed that might need tests
if is_ci; then
    # In CI, check all Python files in the repo
    STAGED_PY_FILES=$(find . -name "*.py" -path "./lightrag/*" -type f | head -5 || true)
else
    # Local development: check staged files
    STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | grep -E '(lightrag|src)' | head -5 || true)
fi

if [[ -n "$STAGED_PY_FILES" ]]; then
    echo "📁 Python files to validate:"
    echo "$STAGED_PY_FILES" | sed 's/^/  • /'

    # Check if corresponding tests exist
    for py_file in $STAGED_PY_FILES; do
        # Convert to relative path if needed
        py_file=$(echo "$py_file" | sed 's|^\./||')

        if [[ "$py_file" =~ ^lightrag/(.+)\.py$ ]]; then
            module_name="${BASH_REMATCH[1]}"
            expected_test="tests/test_${module_name}.py"

            if [[ ! -f "$expected_test" ]]; then
                if is_ci; then
                    WARNINGS+=("No test file found for $py_file (expected: $expected_test)")
                else
                    ERRORS+=("No test file found for $py_file (expected: $expected_test)")
                fi
            fi
        fi
    done
fi

# Output results
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo "🚫 ERRORS (block commit):"
    for error in "${ERRORS[@]}"; do
        echo "  • $error"
    done
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "⚠️  WARNINGS (consider fixing):"
    for warning in "${WARNINGS[@]}"; do
        echo "  • $warning"
    done
fi

echo ""

# CI-friendly exit logic
if is_ci; then
    # In CI, warnings don't block commits but are reported
    if [[ ${#ERRORS[@]} -gt 0 ]]; then
        echo "❌ TDD compliance check FAILED - Critical errors in CI"
        echo "💡 These errors would block commits in local development"
        exit 1
    elif [[ ${#WARNINGS[@]} -gt 0 ]]; then
        echo "⚠️ TDD compliance check completed with warnings in CI"
        echo "💡 Warnings noted but not blocking in CI environment"
        exit 0
    else
        echo "✅ TDD compliance check PASSED in CI"
        exit 0
    fi
else
    # Local development: strict mode
    if [[ ${#ERRORS[@]} -gt 0 ]]; then
        echo "❌ TDD compliance check FAILED - Commit blocked"
        echo "💡 Fix issues above and try again"
        exit 1
    else
        echo "✅ TDD compliance check PASSED"
        exit 0
    fi
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "⚠️  WARNINGS (consider fixing):"
    for warning in "${WARNINGS[@]}"; do
        echo "  • $warning"
    done
fi

echo ""

# Exit with error if there are blocking errors
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "❌ TDD compliance check FAILED - Commit blocked"
    echo "💡 Fix the issues above and try again"
    exit 1
else
    echo "✅ TDD compliance check PASSED"
    exit 0
fi
