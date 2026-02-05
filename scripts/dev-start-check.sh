#!/bin/bash
# Development Start Check - Run before starting development on any feature
# Ensures TDD compliance before work begins

set -e

echo "🚀 LightRAG Development Start Check"
echo "=================================="

# Get current branch name
BRANCH_NAME=$(git branch --show-current)
echo "Current branch: $BRANCH_NAME"

# Check if we're on a feature branch
if [[ ! "$BRANCH_NAME" =~ ^(feature|agent|task)/.+ ]]; then
    echo "ℹ️ Not on a feature/agent/task branch"
    echo "Consider creating a feature branch for new work:"
    echo "  git checkout -b feature/your-feature-name"
    echo ""
    echo "Continuing with basic checks..."
    exit 0
fi

# Extract feature name (get last part after slashes)
FEATURE_NAME=$(echo "$BRANCH_NAME" | sed 's/^\(feature\|agent\|task\)\///' | sed 's/.*\///' | sed 's/^task-//')
echo "📋 Feature detected: $FEATURE_NAME"

# Check for beads issue
echo ""
echo "🔗 Checking beads compliance..."

if command -v bd >/dev/null 2>&1; then
    # Check if there are any beads issues
    ISSUE_COUNT=$(bd list --all 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    echo "Available beads issues: $ISSUE_COUNT"
    
    if [[ $ISSUE_COUNT -eq 0 ]]; then
        echo "⚠️  No beads issues found"
        echo "💡 Consider creating a beads issue for tracking:"
        echo "   bd create -t \"Implement $FEATURE_NAME\" -d \"TDD development for $FEATURE_NAME\""
    else
        echo "✅ Beads issues found"
        # Look for feature-specific issues
        MATCHING_ISSUES=$(bd list --all 2>/dev/null | grep -i "$FEATURE_NAME" | wc -l | tr -d ' ' || echo "0")
        if [[ $MATCHING_ISSUES -gt 0 ]]; then
            echo "✅ Found $MATCHING_ISSUES issue(s) for feature: $FEATURE_NAME"
        else
            echo "⚠️  No specific issues for feature: $FEATURE_NAME"
        fi
    fi
else
    echo "⚠️  Beads command not available"
fi

# Check TDD artifacts
echo ""
echo "🧪 Checking TDD artifacts..."

MISSING_ARTIFACTS=()

# Check TDD test file
if [[ ! -f "tests/${FEATURE_NAME}_tdd.py" ]]; then
    MISSING_ARTIFACTS+=("tests/${FEATURE_NAME}_tdd.py")
else
    echo "✅ TDD test file exists"
fi

# Check functional test file  
if [[ ! -f "tests/${FEATURE_NAME}_functional.py" ]]; then
    MISSING_ARTIFACTS+=("tests/${FEATURE_NAME}_functional.py")
else
    echo "✅ Functional test file exists"
fi

# Check documentation
if [[ ! -f "docs/${FEATURE_NAME}_analysis.md" ]]; then
    MISSING_ARTIFACTS+=("docs/${FEATURE_NAME}_analysis.md")
else
    echo "✅ Documentation exists"
fi

# Report results
echo ""
if [[ ${#MISSING_ARTIFACTS[@]} -eq 0 ]]; then
    echo "🎉 SUCCESS: All TDD artifacts present for feature: $FEATURE_NAME"
    echo ""
    echo "✅ Ready for development!"
    echo ""
    echo "Next steps:"
    echo "1. Implement your feature"
    echo "2. Run tests: pytest tests/${FEATURE_NAME}_*_test.py -v"
    echo "3. Commit changes: git add . && git commit -m \"Implement $FEATURE_NAME\""
    echo "4. Push changes: git push"
else
    echo "❌ ACTION REQUIRED: Missing TDD artifacts for feature: $FEATURE_NAME"
    echo ""
    echo "Missing artifacts:"
    for artifact in "${MISSING_ARTIFACTS[@]}"; do
        echo "  - ❌ $artifact"
    done
    echo ""
    echo "🚨 Development blocked until TDD artifacts are created"
    echo ""
    echo "💡 Auto-create missing artifacts:"
    echo "   ./scripts/create-tdd-artifacts.sh $FEATURE_NAME"
    echo ""
    echo "Or create them manually:"
    echo "1. Create tests/${FEATURE_NAME}_tdd.py with unit tests"
    echo "2. Create tests/${FEATURE_NAME}_functional.py with integration tests"
    echo "3. Create docs/${FEATURE_NAME}_analysis.md with technical analysis"
    echo ""
    echo "After creating artifacts, run this script again."
    exit 1
fi

# Additional checks
echo ""
echo "🔍 Additional checks..."

# Check if pytest is available
if command -v pytest >/dev/null 2>&1; then
    echo "✅ pytest available"
else
    echo "⚠️  pytest not available - install with: pip install pytest"
fi

# Check if working directory is clean
if [[ -z $(git status --porcelain) ]]; then
    echo "✅ Working directory clean"
else
    echo "⚠️  Working directory has uncommitted changes"
    echo "   Consider committing before starting new work"
fi

echo ""
echo "🏁 Development start check complete!"