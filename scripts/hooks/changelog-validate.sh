#!/bin/bash
# CHANGELOG Validation Hook
# Validates CHANGELOG.md format and catches corruption

set -euo pipefail

CHANGELOG_FILE="CHANGELOG.md"

if [ ! -f "$CHANGELOG_FILE" ]; then
    echo "ℹ️ CHANGELOG.md does not exist (optional)"
    exit 0
fi

ERRORS=0

# Check for empty version: ## [] - 
if grep -qE "^## \[\s*\] - " "$CHANGELOG_FILE"; then
    echo "❌ ERROR: Corrupted CHANGELOG entry (empty version): ## [] - "
    ERRORS=$((ERRORS + 1))
fi

# Check for Unreleased without date: ## [Unreleased] (nothing after)
if grep -qE "^## \[Unreleased\]\s*$" "$CHANGELOG_FILE"; then
    echo "❌ ERROR: Corrupted CHANGELOG entry (Unreleased without date)"
    ERRORS=$((ERRORS + 1))
fi

# Check for version without author: ## [2026-02-17] - (nothing after)
if grep -qE "^## \[20[0-9]{2}-[0-9]{2}-[0-9]{2}\]\s*-\s*$" "$CHANGELOG_FILE"; then
    echo "❌ ERROR: Corrupted CHANGELOG entry (version without author)"
    ERRORS=$((ERRORS + 1))
fi

# Check for entry without any content after version line
if grep -qE "^## \[.+\]\s*-\s*$" "$CHANGELOG_FILE"; then
    echo "❌ ERROR: Corrupted CHANGELOG entry (missing author/content)"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "Found $ERRORS corrupted entries in CHANGELOG.md"
    echo "Please fix the above errors before committing."
    exit 1
fi

echo "✅ CHANGELOG.md validation passed"
exit 0
