#!/bin/bash
# Beads Sync Check for Pre-commit
# Ensures beads changes are flushed before commits

echo "🔗 Running Beads Sync Check..."

# Check if beads is available
if ! command -v bd >/dev/null 2>&1; then
    echo "⚠️  Beads command not available, skipping sync check"
    exit 0
fi

# Check if this is a beads-enabled repository
if [[ ! -d ".beads" ]]; then
    echo "ℹ️ Not a beads repository, skipping sync check"
    exit 0
fi

# Check if there are pending beads changes
if command -v bd >/dev/null 2>&1; then
    # Try to check for pending changes
    if bd status --quiet 2>/dev/null; then
        echo "✅ Beads status clean"
    else
        echo "⚠️  Beads has pending changes, flushing to JSONL..."
        if bd flush 2>/dev/null; then
            echo "✅ Beads changes flushed successfully"
        else
            echo "⚠️  Could not flush beads changes, but continuing..."
        fi
    fi
fi

echo "✅ Beads sync check complete"
exit 0
