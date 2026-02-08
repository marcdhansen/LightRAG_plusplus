#!/bin/bash
# Beads Sync Check for Pre-commit
# Ensures beads changes are flushed before commits
# Enhanced with CI environment support and graceful error handling

set +e  # Don't exit on error for better resilience

echo "🔗 Running Beads Sync Check..."

# Function to check if we're in CI environment
is_ci() {
    [[ "$GITHUB_ACTIONS" == "true" || "$CI" == "true" || "$CONTINUOUS_INTEGRATION" == "true" ]]
}

# Function to check if beads command is available and working
beads_available() {
    if ! command -v bd >/dev/null 2>&1; then
        return 1
    fi

    # Test if beads command actually works
    if ! bd --version >/dev/null 2>&1; then
        return 1
    fi

    return 0
}

# In CI environments, be more lenient and provide helpful information
if is_ci; then
    echo "🤖 Running in CI environment - using lenient beads check"

    # Check if this is a beads-enabled repository
    if [[ ! -d ".beads" ]]; then
        echo "ℹ️ Not a beads repository, skipping sync check"
        exit 0
    fi

    if beads_available; then
        echo "✅ Beads command available, checking status..."

        # Try to check for pending changes with enhanced timeout and retry
        if timeout 30 bd status --quiet 2>/dev/null || timeout 30 bd status --quiet 2>/dev/null; then
            echo "✅ Beads status clean"
        else
            echo "⚠️  Beads has pending changes or command failed, attempting to flush..."
            if timeout 45 bd flush 2>/dev/null || timeout 45 bd flush --force 2>/dev/null; then
                echo "✅ Beads changes flushed successfully"
            else
                echo "⚠️  Could not flush beads changes (multiple timeouts or errors), but continuing in CI..."
                echo "💡 Note: Beads issues in CI are non-blocking with enhanced resilience"
            fi
        fi
    else
        echo "⚠️  Beads command not available or not working in CI"
        echo "💡 This is expected in CI environments where beads may not be installed"
        echo "ℹ️ Continuing without beads sync..."
    fi

    echo "✅ Beads sync check complete (CI mode)"
    exit 0
fi

# Local development: stricter checks
if ! beads_available; then
    echo "⚠️  Beads command not available, skipping sync check"
    echo "💡 To enable beads tracking: npm install -g @beadsdev/beads"
    exit 0
fi

# Check if this is a beads-enabled repository
if [[ ! -d ".beads" ]]; then
    echo "ℹ️ Not a beads repository, skipping sync check"
    exit 0
fi

echo "🔍 Checking beads status in local development..."

# Check if there are pending beads changes
if bd status --quiet 2>/dev/null; then
    echo "✅ Beads status clean"
else
    echo "⚠️  Beads has pending changes, flushing to JSONL..."
    if bd flush 2>/dev/null; then
        echo "✅ Beads changes flushed successfully"
    else
        echo "❌ Could not flush beads changes"
        echo "💡 Manual flush required: bd flush"
        echo "⚠️  Continuing with commit, but beads may be out of sync"

        # Ask user if they want to continue
        read -p "Continue with commit despite beads sync issue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Commit aborted by user"
            exit 1
        fi
    fi
fi

echo "✅ Beads sync check complete"
exit 0
