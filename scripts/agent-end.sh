#!/bin/bash
#
# Agent Session End Script
# Cleans up the session lock file when an agent finishes working
#

set -e

# Configuration
LOCKS_DIR=".agent/session_locks"

# Get agent info
AGENT_ID="${OPENCODE_AGENT_ID:-unknown}"
SESSION_ID="${OPENCODE_SESSION_ID:-$(date +%s)}"

# Try to find lock file
find_lock_file() {
    local lock_file=""

    # First, check if AGENT_LOCK_FILE is set
    if [ -n "$AGENT_LOCK_FILE" ] && [ -f "$AGENT_LOCK_FILE" ]; then
        echo "$AGENT_LOCK_FILE"
        return 0
    fi

    # Otherwise, search for lock file matching agent and session
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue

        if [[ "$(basename "$lock")" == *"${AGENT_ID}"* ]] && [[ "$(basename "$lock")" == *"${SESSION_ID}"* ]]; then
            echo "$lock"
            return 0
        fi
    done

    # Search by PID as fallback
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue

        local lock_pid=$(grep '"pid"' "$lock" | sed 's/.*: \([0-9]*\).*/\1/')
        if [ "$lock_pid" = "$$" ]; then
            echo "$lock"
            return 0
        fi
    done

    return 1
}

# Function to clean up lock file
cleanup_lock() {
    local lock_file="$1"

    if [ -f "$lock_file" ]; then
        rm -f "$lock_file"
        echo "✅ Lock file removed: $(basename "$lock_file")"
        return 0
    else
        echo "⚠️  Lock file not found: $lock_file"
        return 1
    fi
}

# Function to kill heartbeat process
kill_heartbeat() {
    local lock_file="$1"
    if [ -f "$lock_file" ]; then
        # Extract heartbeat PID (macOS compatible grep/sed)
        local hb_pid=$(grep '"heartbeat_pid"' "$lock_file" | sed 's/.*: \([0-9]*\),.*/\1/')

        if [ -n "$hb_pid" ] && kill -0 "$hb_pid" 2>/dev/null; then
            echo "💓 Stopping heartbeat process (PID: $hb_pid)..."
            kill "$hb_pid" || true
            echo "✅ Heartbeat stopped"
        fi
    fi
}

# Function to show session summary
show_summary() {
    local lock_file="$1"

    if [ -f "$lock_file" ]; then
        local agent=$(grep '"agent_name"' "$lock_file" | sed 's/.*: "\([^"]*\)".*/\1/')
        local task=$(grep '"current_task"' "$lock_file" | sed 's/.*: "\([^"]*\)".*/\1/')
        local start_time=$(grep '"started_at"' "$lock_file" | sed 's/.*: "\([^"]*\)".*/\1/')
        local end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # Calculate duration
        local start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$start_time" +%s 2>/dev/null || echo "0")
        local end_epoch=$(date +%s)
        local duration=$((end_epoch - start_epoch))
        local duration_min=$((duration / 60))

        echo ""
        echo "📊 Session Summary"
        echo "=================="
        echo "Agent: ${agent}"
        echo "Task: ${task}"
        echo "Started: ${start_time}"
        echo "Ended: ${end_time}"
        echo "Duration: ${duration_min} minutes (${duration} seconds)"
    fi
}

# Function to show usage
usage() {
    echo "Usage: $0 [--lock-file <path>] [--silent] [--skip-pr]"
    echo ""
    echo "Options:"
    echo "  --lock-file <path>  Explicitly specify lock file to remove"
    echo "  --silent            Don't show session summary"
    echo "  --skip-pr           Skip PR creation and branch cleanup"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --lock-file .agent/session_locks/agent_xyz_123.json"
    echo "  $0 --silent"
    echo "  $0 --skip-pr  # For WIP sessions"
}

# Parse arguments
EXPLICIT_LOCK_FILE=""
SILENT=false
SKIP_PR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --lock-file)
            EXPLICIT_LOCK_FILE="$2"
            shift 2
            ;;
        --silent)
            SILENT=true
            shift
            ;;
        --skip-pr)
            SKIP_PR=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
echo "🏁 Agent Session End"
echo "===================="

# Find lock file
if [ -n "$EXPLICIT_LOCK_FILE" ]; then
    LOCK_FILE="$EXPLICIT_LOCK_FILE"
    if [ ! -f "$LOCK_FILE" ]; then
        echo "❌ Specified lock file not found: $LOCK_FILE"
        exit 1
    fi
else
    LOCK_FILE=$(find_lock_file)
    if [ -z "$LOCK_FILE" ]; then
        echo "⚠️  No lock file found for this session"
        echo "   (This is okay if session wasn't started with agent-start.sh)"
        exit 0
    fi
fi

# Show summary if not silent
if [ "$SILENT" = false ]; then
    show_summary "$LOCK_FILE"
fi

# Stop heartbeat
kill_heartbeat "$LOCK_FILE"

# Clean up lock file
echo ""
cleanup_lock "$LOCK_FILE"

echo ""
echo "✅ Session ended successfully"
echo "   Lock file cleaned up"

# OpenViking Session Flush (if enabled)
if [ -n "$OPENVIKING_ENABLED" ]; then
    echo "🧠 Flushing OpenViking session..."
    curl -sf -X POST http://localhost:8000/session/flush > /dev/null || echo "⚠️  OpenViking flush failed"
fi

# Update beads if task was set
if [ -f "$LOCK_FILE.tmp" ]; then  # Check if we saved task info before removal
    task=$(grep '"current_task"' "$LOCK_FILE.tmp" | sed 's/.*: "\([^"]*\)".*/\1/')
    if [ "$task" != "unknown" ] && [ -n "$task" ]; then
        echo "💡 Remember to update task status with: bd close $task -r 'completion reason'"
    fi
    rm -f "$LOCK_FILE.tmp"
fi

# PR Lifecycle (unless --skip-pr)
if [ "$SKIP_PR" = false ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
        echo ""
        echo "🔀 PR Lifecycle..."
        echo "   Current branch: $CURRENT_BRANCH"

        # Check if gh CLI is available
        if command -v gh &> /dev/null; then
            # Check for uncommitted changes
            if [ -n "$(git status --porcelain)" ]; then
                echo "⚠️  Uncommitted changes detected. Commit before creating PR."
            else
                # Check if PR already exists
                if gh pr view "$CURRENT_BRANCH" --json state &> /dev/null; then
                    echo "✅ PR already exists for this branch"
                    echo "   Run: gh pr merge --auto --squash --delete-branch"
                else
                    echo "📝 Creating PR..."
                    if gh pr create --fill --base main; then
                        echo "🔄 Enabling auto-merge (squash, delete-branch)..."
                        gh pr merge --auto --squash --delete-branch || echo "⚠️  Auto-merge setup failed (check branch protection rules)"
                    fi
                fi

                echo ""
                echo "💡 After PR merges, run:"
                echo "   git checkout main && git pull"
                echo "   git branch -d $CURRENT_BRANCH"
                echo "   git remote prune origin"
            fi
        else
            echo "⚠️  GitHub CLI (gh) not found. Install with: brew install gh"
            echo "   Manual PR: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:\/]//;s/.git$//')/compare/$CURRENT_BRANCH"
        fi
    else
        echo "✅ On main branch - no PR needed"
    fi
fi
