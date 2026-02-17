#!/bin/bash
# CHANGELOG Commit-msg Validation Hook
# Validates CHANGELOG.md changes in staged diff before commit is finalized

set -euo pipefail

CHANGELOG_FILE="CHANGELOG.md"
COMMIT_MSG_FILE="$1"

# Check if CHANGELOG.md exists in the repository (either staged or already tracked)
if ! git ls-files --error-unmatch "$CHANGELOG_FILE" 2>/dev/null; then
    echo "ℹ️ CHANGELOG.md does not exist in repo (optional)"
    exit 0
fi

ERRORS=0

# Get the staged version of CHANGELOG.md (from index)
STAGED_CHANGELOG=$(git show ":CHANGELOG.md" 2>/dev/null || echo "")

if [ -z "$STAGED_CHANGELOG" ]; then
    echo "ℹ️ No staged CHANGELOG.md to validate"
    exit 0
fi

# Check for empty version: ## [] - 
if echo "$STAGED_CHANGELOG" | grep -qE "^## \[\s*\] - "; then
    echo "❌ ERROR: Staged CHANGELOG has corrupted entry (empty version): ## [] - "
    ERRORS=$((ERRORS + 1))
fi

# Check for Unreleased without date
if echo "$STAGED_CHANGELOG" | grep -qE "^## \[Unreleased\]\s*$"; then
    echo "❌ ERROR: Staged CHANGELOG has corrupted entry (Unreleased without date)"
    ERRORS=$((ERRORS + 1))
fi

# Check for version without author
if echo "$STAGED_CHANGELOG" | grep -qE "^## \[20[0-9]{2}-[0-9]{2}-[0-9]{2}\]\s*-\s*$"; then
    echo "❌ ERROR: Staged CHANGELOG has corrupted entry (version without author)"
    ERRORS=$((ERRORS + 1))
fi

# Check for entry without content
if echo "$STAGED_CHANGELOG" | grep -qE "^## \[.+\]\s*-\s*$"; then
    echo "❌ ERROR: Staged CHANGELOG has corrupted entry (missing author/content)"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "Found $ERRORS corrupted entries in staged CHANGELOG.md"
    echo "Please fix the above errors before committing."
    exit 1
fi

echo "✅ Staged CHANGELOG.md validation passed"
exit 0
