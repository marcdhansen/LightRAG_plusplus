#!/bin/bash
# CI Diagnostic Script
# Comprehensive testing of CI/CD setup and configuration

set -e

echo "🧪 Running Comprehensive CI Diagnostics..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"

    echo -e "\n${BLUE}🔍 Testing: $test_name${NC}"
    echo "Command: $test_command"

    ((TESTS_TOTAL++))

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        echo "Command failed: $test_command"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to run test with detailed output
run_test_verbose() {
    local test_name="$1"
    local test_command="$2"

    echo -e "\n${BLUE}🔍 Testing: $test_name${NC}"
    echo "Command: $test_command"
    echo "Output:"
    echo "---"

    ((TESTS_TOTAL++))

    if eval "$test_command"; then
        echo "---"
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo "---"
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check file existence
check_file() {
    local file_path="$1"
    local description="$2"

    echo -e "\n${BLUE}📁 Checking: $description${NC}"
    echo "Path: $file_path"

    ((TESTS_TOTAL++))

    if [[ -f "$file_path" ]]; then
        echo -e "${GREEN}✅ EXISTS: $description${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ MISSING: $description${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check directory existence
check_dir() {
    local dir_path="$1"
    local description="$2"

    echo -e "\n${BLUE}📂 Checking: $description${NC}"
    echo "Path: $dir_path"

    ((TESTS_TOTAL++))

    if [[ -d "$dir_path" ]]; then
        echo -e "${GREEN}✅ EXISTS: $description${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ MISSING: $description${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "\n${BLUE}🔧 Environment Tests${NC}"
echo "==================="

# Python environment
run_test "Python version (3.10+)" "python --version | grep -E '3\.(1[0-9]|[2-9][0-9])'"
run_test "Pip is available" "pip --version"
run_test "Ruff is installed" "ruff --version"
run_test "Pre-commit is installed" "pre-commit --version"

# Node.js environment (if WebUI exists)
if [[ -d "lightrag_webui" ]]; then
    echo -e "\n${BLUE}🎨 WebUI Environment Tests${NC}"
    echo "==========================="

    run_test "Node.js is available" "node --version"
    run_test "Bun is available (preferred)" "bun --version"
    run_test "npm is available (fallback)" "npm --version"
    check_dir "lightrag_webui" "WebUI directory"
    check_file "lightrag_webui/package.json" "WebUI package configuration"
    check_dir "lightrag_webui/node_modules" "WebUI node modules"
fi

# Beads environment (if applicable)
if [[ -d ".beads" ]]; then
    echo -e "\n${BLUE}🔗 Beads Environment Tests${NC}"
    echo "=========================="

    run_test "Beads is available" "bd --version"
    run_test "Beads status check" "bd status --quiet"
fi

echo -e "\n${BLUE}📋 Configuration Tests${NC}"
echo "========================"

# Configuration files
check_file ".pre-commit-config.yaml" "Pre-commit configuration"
check_file "pyproject.toml" "Python project configuration"
check_file ".github/workflows/linting.yaml" "Linting workflow"
check_file ".github/workflows/ci-setup.yml" "CI setup workflow"

# Script files
check_file "scripts/hooks/tdd-compliance-check.sh" "TDD compliance hook"
check_file "scripts/hooks/beads-sync-check.sh" "Beads sync hook"
check_file "scripts/hooks/webui-lint-check.sh" "WebUI linting hook"
check_file "scripts/collect-ci-debug-info.sh" "Debug info script"

echo -e "\n${BLUE}🔍 Pre-commit Tests${NC}"
echo "======================"

# Pre-commit validation
run_test "Pre-commit configuration is valid" "pre-commit validate-config"

# Test individual hooks (non-destructive)
run_test "TDD compliance hook syntax" "bash -n scripts/hooks/tdd-compliance-check.sh"
run_test "Beads sync hook syntax" "bash -n scripts/hooks/beads-sync-check.sh"
run_test "WebUI lint hook syntax" "bash -n scripts/hooks/webui-lint-check.sh"

echo -e "\n${BLUE}🧪 Functionality Tests${NC}"
echo "======================"

# Test ruff functionality
run_test "Ruff can check configuration" "ruff check --help | head -5"
run_test "Ruff format is available" "ruff format --help | head -5"

# Test Python package structure
run_test "LightRAG package can be imported" "python -c 'import lightrag; print(lightrag.__version__)'"

# Test TDD artifact detection
if [[ -n "$(git branch --show-current 2>/dev/null | grep -E '^(feature|agent|task)/')" ]]; then
    BRANCH_NAME=$(git branch --show-current 2>/dev/null)
    FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's/^\(feature\|agent\|task\)\///' | sed 's/.*\///' | sed 's/^task-//')

    echo -e "\n${BLUE}📋 TDD Artifact Tests (Feature: $FEATURE_NAME)${NC}"
    echo "=============================================="

    check_file "tests/${FEATURE_NAME}_tdd.py" "TDD test file"
    check_file "tests/${FEATURE_NAME}_functional.py" "Functional test file"
    check_file "docs/${FEATURE_NAME}_analysis.md" "Analysis documentation"
fi

echo -e "\n${BLUE}🚀 CI/CD Pipeline Tests${NC}"
echo "========================="

# Test workflow syntax
run_test "Linting workflow is valid YAML" "python -c 'import yaml; yaml.safe_load(open(\".github/workflows/linting.yaml\"))'"
run_test "CI setup workflow is valid YAML" "python -c 'import yaml; yaml.safe_load(open(\".github/workflows/ci-setup.yml\"))'"

# Test workflow dependencies
run_test_verbose "Workflow Python version matches project" "grep -q 'python-version.*3\\.12' .github/workflows/linting.yaml"

echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=================="

echo "Total tests: $TESTS_TOTAL"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 All tests passed! CI/CD configuration looks good.${NC}"
    echo -e "\n${BLUE}💡 Next steps:${NC}"
    echo "1. Run pre-commit locally: pre-commit run --all-files"
    echo "2. Test your changes in a feature branch"
    echo "3. Create a pull request to test the full pipeline"
else
    echo -e "\n${RED}⚠️  Some tests failed. Please review the issues above.${NC}"
    echo -e "\n${BLUE}🛠️  Recommended actions:${NC}"
    echo "1. Fix missing dependencies or configuration issues"
    echo "2. Run debug script: ./scripts/collect-ci-debug-info.sh"
    echo "3. See troubleshooting guide: docs/ci-troubleshooting.md"
    echo "4. Re-run this diagnostic after fixing issues"
fi

echo -e "\n${BLUE}📚 Additional Resources${NC}"
echo "========================"
echo "• Troubleshooting guide: docs/ci-troubleshooting.md"
echo "• Debug information: ./scripts/collect-ci-debug-info.sh"
echo "• Pre-commit hooks: .pre-commit-config.yaml"
echo "• Workflows: .github/workflows/"

# Function to create GitHub issue if running in CI and tests failed
create_ci_issue_if_failed() {
    # Only create issue if running in GitHub Actions and tests failed
    if [[ $TESTS_FAILED -gt 0 && -n "$GITHUB_ACTIONS" && -n "$WORKFLOW_NAME" ]]; then
        echo "📝 Creating GitHub issue for CI failure..."

        ISSUE_TITLE="CI failed: $WORKFLOW_NAME"
        ISSUE_BODY="## 🚨 CI/CD Pipeline Failure

**Workflow:** $WORKFLOW_NAME
**Run URL:** $RUN_URL
**Branch:** ${GITHUB_REF_NAME:-unknown}
**Commit:** ${GITHUB_SHA:-unknown}
**Timestamp:** $(date -u +%Y-%m-%dT%H:%M:%SZ)

### 📊 Diagnostic Results
- Total tests: $TESTS_TOTAL
- Failed: $TESTS_FAILED
- Passed: $TESTS_PASSED

### 🔗 Links
- [Workflow Run]($RUN_URL)
- [Repository](https://github.com/${GITHUB_REPOSITORY:-repository})

---
🤖 This issue was automatically created by CI diagnostic failure.
Please review the diagnostic output above and address the failure."

        gh issue create \
            --title "$ISSUE_TITLE" \
            --body "$ISSUE_BODY" \
            --label "ci-failure,diagnostic" || {
            echo "⚠️ Failed to create GitHub issue"
            return 1
        }

        echo "✅ GitHub issue created successfully"
    fi
}

# Create issue if CI failed and we're in GitHub Actions
create_ci_issue_if_failed

# Exit with appropriate code
if [[ $TESTS_FAILED -eq 0 ]]; then
    exit 0
else
    exit 1
fi
