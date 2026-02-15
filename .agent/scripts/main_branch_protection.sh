#!/bin/bash
# CI SKIP HEADER - defense in depth
# Pre-commit hooks are local development tools, not CI tools
if [[ "$GITHUB_ACTIONS" == "true" ]] || [[ "$CI" == "true" ]]; then
    echo "ℹ️ Skipping in CI (pre-commit hooks are local development tools)"
    exit 0
fi

# Main branch protection for TDD compliance
# Prevents commits to main/master branch without feature branch

BRANCH=$(git branch --show-current)
PROTECTION_MSG="❌ ERROR: Cannot commit to main/master branch. Create a feature branch first."

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "$PROTECTION_MSG"
    echo "💡 Use: git checkout -b feature/your-feature-name"
    exit 1
else
    echo "✅ Not on main/master branch"
    exit 0
fi
