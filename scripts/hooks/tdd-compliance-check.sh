#!/bin/bash
# Enhanced TDD Compliance Check for Pre-commit
# Validates TDD artifacts for feature/agent/task branches

set -e

echo "🔍 Running TDD Compliance Check..."

# Get current branch name
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "")

# Skip for non-feature branches
if [[ ! "$BRANCH_NAME" =~ ^(feature|agent|task)/.+ ]]; then
    echo "ℹ️ Not a feature/agent/task branch, skipping TDD artifact validation"
    exit 0
fi

# Extract feature name (get last part after slashes)
FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's/^\(feature\|agent\|task\)\///' | sed 's/.*\///' | sed 's/^task-//')
echo "📋 Validating TDD artifacts for feature: $FEATURE_NAME"

# Check required artifacts
MISSING_ARTIFACTS=()
ERRORS=()
WARNINGS=()

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
        ERRORS+=("Missing required artifact: $artifact")
    done

    echo ""
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

# Check for any Python files being committed that might need tests
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | grep -E '(lightrag|src)' | head -5 || true)

if [[ -n "$STAGED_PY_FILES" ]]; then
    echo "📁 Python files being committed:"
    echo "$STAGED_PY_FILES" | sed 's/^/  • /'

    # Check if corresponding tests exist
    for py_file in $STAGED_PY_FILES; do
        if [[ "$py_file" =~ ^lightrag/(.+)\.py$ ]]; then
            module_name="${BASH_REMATCH[1]}"
            expected_test="tests/test_${module_name}.py"

            if [[ ! -f "$expected_test" ]]; then
                WARNINGS+=("No test file found for $py_file (expected: $expected_test)")
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

# Exit with error if there are blocking errors
if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo "❌ TDD compliance check FAILED - Commit blocked"
    echo "💡 Fix the issues above and try again"
    exit 1
else
    echo "✅ TDD compliance check PASSED"
    exit 0
fi
