#!/bin/bash
# CI/CD Debug Information Collection Script
# Gathers comprehensive debugging information for CI/CD issues

set -e

echo "🔍 Collecting CI/CD Debug Information..."
echo "===================================="

# Create debug info directory
DEBUG_DIR="ci-debug-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEBUG_DIR"

echo "📁 Debug information will be saved to: $DEBUG_DIR"
echo ""

# Function to capture command output
capture() {
    local cmd="$1"
    local file="$2"
    local description="$3"

    echo "🔍 Capturing: $description"
    echo "Command: $cmd" > "$DEBUG_DIR/$file"
    echo "Description: $description" >> "$DEBUG_DIR/$file"
    echo "Timestamp: $(date)" >> "$DEBUG_DIR/$file"
    echo "" >> "$DEBUG_DIR/$file"

    # Capture output with error handling
    if eval "$cmd" >> "$DEBUG_DIR/$file" 2>&1; then
        echo "✅ Success: $description"
    else
        echo "⚠️  Error: $description (captured anyway)"
    fi
    echo ""
}

# Function to capture file contents
capture_file() {
    local file_path="$1"
    local description="$2"

    if [[ -f "$file_path" ]]; then
        echo "🔍 Capturing file: $description"
        cp "$file_path" "$DEBUG_DIR/$(basename $file_path)"
        echo "✅ Captured: $description"
    else
        echo "⚠️  File not found: $file_path"
    fi
    echo ""
}

# Environment information
capture "uname -a" "system_info.txt" "System Information"
capture "whoami" "user.txt" "Current User"
capture "pwd" "directory.txt" "Current Directory"
capture "env | grep -E '(CI|GITHUB|PATH|PYTHON)' | sort" "environment.txt" "Relevant Environment Variables"

# Python environment
capture "python --version" "python_version.txt" "Python Version"
capture "pip --version" "pip_version.txt" "Pip Version"
capture "pip list" "pip_packages.txt" "Installed Python Packages"
capture "which python" "python_path.txt" "Python Executable Path"

# Node.js/Bun environment (if applicable)
capture "node --version 2>/dev/null || echo 'Node.js not found'" "node_version.txt" "Node.js Version"
capture "bun --version 2>/dev/null || echo 'Bun not found'" "bun_version.txt" "Bun Version"
capture "npm --version 2>/dev/null || echo 'npm not found'" "npm_version.txt" "npm Version"

# Development tools
capture "ruff --version 2>/dev/null || echo 'Ruff not found'" "ruff_version.txt" "Ruff Version"
capture "pre-commit --version 2>/dev/null || echo 'Pre-commit not found'" "precommit_version.txt" "Pre-commit Version"
capture "bd --version 2>/dev/null || echo 'Beads not found'" "beads_version.txt" "Beads Version"

# Git information
capture "git --version" "git_version.txt" "Git Version"
capture "git status --porcelain" "git_status.txt" "Git Status"
capture "git branch --show-current" "git_branch.txt" "Current Git Branch"
capture "git log --oneline -5" "git_history.txt" "Recent Git History"

# Project structure
capture "find . -maxdepth 2 -type d | grep -v '\\.git' | sort" "directory_structure.txt" "Project Directory Structure"
capture "ls -la" "file_list.txt" "Current Directory Files"

# Pre-commit configuration
capture_file ".pre-commit-config.yaml" "Pre-commit Configuration"
capture_file "pyproject.toml" "Python Project Configuration"
capture_file "package.json" "Node.js Package Configuration (if exists)"

# Test and documentation structure
capture "find tests -name '*.py' | head -20" "test_files.txt" "Test Files"
capture "find docs -name '*.md' | head -20" "doc_files.txt" "Documentation Files"

# Beads information (if available)
if [[ -d ".beads" ]]; then
    capture "bd status" "beads_status.txt" "Beads Status"
    capture "bd list --all" "beads_issues.txt" "Beads Issues"
fi

# WebUI information (if available)
if [[ -d "lightrag_webui" ]]; then
    capture_file "lightrag_webui/package.json" "WebUI Package Configuration"
    capture "ls -la lightrag_webui/" "webui_files.txt" "WebUI Directory Contents"
    capture "ls -la lightrag_webui/node_modules/ 2>/dev/null | head -10 || echo 'Node modules not found'" "webui_deps.txt" "WebUI Dependencies Status"
fi

# Run pre-commit check (non-destructive)
echo "🔍 Testing pre-commit hooks..."
if command -v pre-commit >/dev/null 2>&1; then
    echo "Testing pre-commit configuration..." > "$DEBUG_DIR/precommit_test.txt"
    pre-commit validate-config >> "$DEBUG_DIR/precommit_test.txt" 2>&1
    echo "" >> "$DEBUG_DIR/precommit_test.txt"
    echo "Available hooks:" >> "$DEBUG_DIR/precommit_test.txt"
    pre-commit run --list-hooks >> "$DEBUG_DIR/precommit_test.txt" 2>&1
else
    echo "Pre-commit not available" > "$DEBUG_DIR/precommit_test.txt"
fi

# Check TDD artifacts
echo "🔍 Checking TDD artifacts..."
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "unknown")
if [[ "$BRANCH_NAME" =~ ^(feature|agent|task)/.+ ]]; then
    FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's/^\(feature\|agent\|task\)\///' | sed 's/.*\///' | sed 's/^task-//')

    echo "Feature name: $FEATURE_NAME" > "$DEBUG_DIR/tdd_artifacts.txt"
    echo "TDD artifacts for feature: $FEATURE_NAME" >> "$DEBUG_DIR/tdd_artifacts.txt"
    echo "" >> "$DEBUG_DIR/tdd_artifacts.txt"

    if [[ -f "tests/${FEATURE_NAME}_tdd.py" ]]; then
        echo "✅ TDD test file found: tests/${FEATURE_NAME}_tdd.py" >> "$DEBUG_DIR/tdd_artifacts.txt"
        grep -c "def test_" "tests/${FEATURE_NAME}_tdd.py" >> "$DEBUG_DIR/tdd_artifacts.txt" || echo "0 test functions" >> "$DEBUG_DIR/tdd_artifacts.txt"
        grep -c "assert" "tests/${FEATURE_NAME}_tdd.py" >> "$DEBUG_DIR/tdd_artifacts.txt" || echo "0 assertions" >> "$DEBUG_DIR/tdd_artifacts.txt"
    else
        echo "❌ TDD test file missing: tests/${FEATURE_NAME}_tdd.py" >> "$DEBUG_DIR/tdd_artifacts.txt"
    fi

    if [[ -f "tests/${FEATURE_NAME}_functional.py" ]]; then
        echo "✅ Functional test file found: tests/${FEATURE_NAME}_functional.py" >> "$DEBUG_DIR/tdd_artifacts.txt"
    else
        echo "❌ Functional test file missing: tests/${FEATURE_NAME}_functional.py" >> "$DEBUG_DIR/tdd_artifacts.txt"
    fi

    if [[ -f "docs/${FEATURE_NAME}_analysis.md" ]]; then
        echo "✅ Documentation found: docs/${FEATURE_NAME}_analysis.md" >> "$DEBUG_DIR/tdd_artifacts.txt"
    else
        echo "❌ Documentation missing: docs/${FEATURE_NAME}_analysis.md" >> "$DEBUG_DIR/tdd_artifacts.txt"
    fi
else
    echo "Not a feature branch, skipping TDD artifact check" > "$DEBUG_DIR/tdd_artifacts.txt"
fi

# Check recent changes (last 24 hours)
echo "🔍 Analyzing recent changes..."
capture "git log --since='24 hours ago' --oneline --name-only" "recent_changes.txt" "Recent Changes (24 hours)"

# System resource information
capture "df -h" "disk_usage.txt" "Disk Usage"
capture "free -h 2>/dev/null || vm_stat | head -10" "memory_usage.txt" "Memory Usage"
capture "uptime" "uptime.txt" "System Uptime"

# Create summary report
echo "📊 Creating summary report..."
cat > "$DEBUG_DIR/README.md" << EOF
# CI/CD Debug Information Report

Generated: $(date)
Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")

## Files in this Report

| File | Description |
|------|-------------|
$(for file in "$DEBUG_DIR"/*.txt; do basename "$file"; done | while read -r file; do echo "| $file | $(head -1 "$DEBUG_DIR/$file" | sed 's/^Description: //' | sed 's/Command: //' | sed 's/^System/### System/' || echo 'N/A') |"; done)

## Quick Diagnosis

### Python Environment
- Version: $(python --version 2>/dev/null || echo "Not found")
- Pip packages: $(pip list 2>/dev/null | wc -l || echo "0") packages installed
- Key tools: $(which ruff pre-commit pytest 2>/dev/null | wc -l || echo "0")/3 tools found

### Node.js Environment
- Node.js: $(node --version 2>/dev/null || echo "Not found")
- Bun: $(bun --version 2>/dev/null || echo "Not found")
- npm: $(npm --version 2>/dev/null || echo "Not found")

### Git Status
- Branch: $(git branch --show-current 2>/dev/null || echo "Unknown")
- Status: $(git status --porcelain 2>/dev/null | wc -l || echo "0") files modified

### Pre-commit Status
- Configuration: $(pre-commit validate-config >/dev/null 2>&1 && echo "✅ Valid" || echo "❌ Invalid")
- Hooks installed: $(pre-commit run --list-hooks >/dev/null 2>&1 | wc -l || echo "0") hooks available

## Next Steps

1. **Review error files**: Look for files with error indicators
2. **Check missing dependencies**: Verify all required tools are installed
3. **Validate configuration**: Ensure config files are properly formatted
4. **Test locally**: Run pre-commit locally before pushing

For detailed troubleshooting, see: [docs/ci-troubleshooting.md](../docs/ci-troubleshooting.md)
EOF

# Create archive
echo "📦 Creating archive..."
cd "$DEBUG_DIR"
tar -czf "../${DEBUG_DIR}.tar.gz" .
cd ..

echo ""
echo "✅ Debug information collection complete!"
echo "📁 Location: $DEBUG_DIR/"
echo "📦 Archive: ${DEBUG_DIR}.tar.gz"
echo ""
echo "📊 Summary:"
echo "  - Files created: $(find "$DEBUG_DIR" -type f | wc -l)"
echo "  - Total size: $(du -sh "$DEBUG_DIR" | cut -f1)"
echo "  - Archive size: $(du -sh "${DEBUG_DIR}.tar.gz" | cut -f1)"
echo ""
echo "📤 To share this information:"
echo "  1. Extract relevant files from $DEBUG_DIR/"
echo "  2. Or upload the archive: ${DEBUG_DIR}.tar.gz"
echo "  3. Include this information in your GitHub issue"
echo ""
echo "🔧 For common solutions, see: docs/ci-troubleshooting.md"
