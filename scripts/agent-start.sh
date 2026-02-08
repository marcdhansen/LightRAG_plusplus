#!/bin/bash
#
# Agent Session Start Script
# Creates a session lock file to signal that an agent is actively working
#

set -e

# Configuration
LOCKS_DIR=".agent/session_locks"
HEARTBEAT_INTERVAL=300  # 5 minutes in seconds
STALE_THRESHOLD=600     # 10 minutes in seconds

# Get agent info
AGENT_ID="${OPENCODE_AGENT_ID:-unknown}"
AGENT_NAME="${OPENCODE_AGENT_NAME:-$(whoami)}"
SESSION_ID="${OPENCODE_SESSION_ID:-$(date +%s)}"
WORKSPACE="$(pwd)"
PID=$$

# Generate lock filename
LOCK_FILE="${LOCKS_DIR}/agent_${AGENT_ID}_${SESSION_ID}.json"

# Function to create lock file
create_lock() {
    local task_id="${1:-unknown}"
    local task_desc="${2:-unknown}"

    cat > "$LOCK_FILE" << EOF
{
  "agent_id": "${AGENT_ID}",
  "agent_name": "${AGENT_NAME}",
  "session_id": "${SESSION_ID}",
  "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "last_heartbeat": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "current_task": "${task_id}",
  "task_description": "${task_desc}",
  "pid": ${PID},
  "workspace": "${WORKSPACE}",
  "heartbeat_interval": ${HEARTBEAT_INTERVAL},
  "version": "1.0"
}
EOF

    echo "✅ Session lock created: $(basename "$LOCK_FILE")"
}

# Function to start background heartbeat
start_heartbeat() {
    echo "💓 Starting background heartbeat every $((HEARTBEAT_INTERVAL / 60)) minutes..."
    (
        # Allow some time for the lock file to be fully written and for the parent to update the PID
        sleep 2
        while [ -f "$LOCK_FILE" ]; do
            # Use absolute path to ensure it works from any directory
            "$(dirname "$0")/agent-heartbeat.sh" > /dev/null 2>&1 || true
            sleep "$HEARTBEAT_INTERVAL"
        done
    ) &
    HB_PID=$!

    # Store the heartbeat PID in the lock file (macOS compatible sed)
    sed -i '' 's/"version": "1.0"/ "heartbeat_pid": '"$HB_PID"',\n  "version": "1.0"/' "$LOCK_FILE"

    echo "💓 Heartbeat process started with PID: $HB_PID"
}

# Function to check for stale locks and warn
check_existing_locks() {
    local stale_count=0
    local active_count=0
    local now=$(date +%s)

    for lock in "${LOCKS_DIR}"/*.json; do
        # Skip if no lock files exist
        [ -e "$lock" ] || continue

        # Skip our own lock if it exists
        [[ "$(basename "$lock")" == *"${SESSION_ID}"* ]] && continue

        # Extract last heartbeat
        local last_heartbeat=$(grep '"last_heartbeat"' "$lock" | sed 's/.*: "\([^"]*\)".*/\1/')
        local lock_time=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_heartbeat" +%s 2>/dev/null || echo "0")

        # Calculate age
        local age=$((now - lock_time))
        local agent=$(grep '"agent_name"' "$lock" | sed 's/.*: "\([^"]*\)".*/\1/')
        local task=$(grep '"current_task"' "$lock" | sed 's/.*: "\([^"]*\)".*/\1/')

        if [ $age -gt $STALE_THRESHOLD ]; then
            echo "⚠️  Stale lock detected ($(basename "$lock"): ${age}s old, ${agent} working on ${task})"
            stale_count=$((stale_count + 1))
        else
            echo "🔴 Active agent detected: ${agent} working on ${task} ($(basename "$lock"))"
            active_count=$((active_count + 1))
        fi
    done

    if [ $active_count -gt 0 ]; then
        echo ""
        echo "⚠️  WARNING: ${active_count} active agent(s) detected!"
        echo "Consider coordinating to avoid conflicts."
        echo "Run './scripts/agent-status.sh' for details."
        echo ""
    fi
}

# Function to show usage
usage() {
    echo "Usage: $0 [--task-id <id>] [--task-desc <desc>] [--quiet]"
    echo ""
    echo "Options:"
    echo "  --task-id <id>      Current task/issue being worked on"
    echo "  --task-desc <desc>  Brief description of current work"
    echo "  --quiet             Suppress warnings about other agents"
    echo ""
    echo "Examples:"
    echo "  $0 --task-id lightrag-8g4 --task-desc \"Implement citation system\""
    echo "  $0 --quiet  # Skip warnings about other agents"
}

# Function to validate Beads task
validate_beads_task() {
    local task_id="$1"
    if [ "$task_id" = "unknown" ]; then
        return 0
    fi

    echo "🔍 Validating Beads task: $task_id..."
    # Check if task exists in Beads
    if bd list --id "$task_id" --all --json | grep -q "\"id\": \"$task_id\""; then
        echo "✅ Task $task_id found in Beads."

        # Automatically label the task with the current agent if not already present
        # This helps with coordination and visibility in bd list
        bd update "$task_id" --labels "agent:${AGENT_NAME}" > /dev/null 2>&1 || true
    else
        echo "⚠️  WARNING: Task $task_id NOT FOUND in Beads."
        echo "Please verify the ID or create it with 'bd create'."
    fi
}

# Parse arguments
TASK_ID="unknown"
TASK_DESC="unknown"
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --task-id)
            TASK_ID="$2"
            shift 2
            ;;
        --task-desc)
            TASK_DESC="$2"
            shift 2
            ;;
        --quiet)
            QUIET=true
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
echo "🔐 Agent Session Start"
echo "======================"
echo "Agent: ${AGENT_NAME} (${AGENT_ID})"
echo "Session: ${SESSION_ID}"
echo "Workspace: ${WORKSPACE}"
echo "PID: ${PID}"
echo ""

# Check for existing locks
if [ "$QUIET" = false ]; then
    check_existing_locks
fi

# Validate Beads task
validate_beads_task "$TASK_ID"

# Run P0 workflow violation prevention validation
echo "🚨 Running P0 workflow violation prevention..."
if python scripts/p0_workflow_fix.py --validate; then
    echo "✅ P0 workflow validation passed"
else
    echo ""
    echo "🚨 P0 WORKFLOW VIOLATION DETECTED"
    echo "Agents are attempting to start new work without completing current phase."
    echo "This violates the Universal Agent Protocol and compromises phase-based development."
    echo ""
    echo "CRITICAL: Work is BLOCKED until violations are resolved"
    echo ""
    echo "To request emergency override (requires manager approval):"
    echo "  python scripts/p0_workflow_fix.py --enforce-gate <target_phase>"
    echo ""
    exit 1
fi

# Create lock file
create_lock "$TASK_ID" "$TASK_DESC"

# Start automated heartbeat
start_heartbeat

# Export lock file path for other scripts
export AGENT_LOCK_FILE="$LOCK_FILE"

echo ""
echo "✅ Session started successfully"
echo "Lock file: ${LOCK_FILE}"
echo ""
echo "💡 Tip: Run './scripts/agent-status.sh' anytime to check agent activity"
echo "💡 Tip: Use './scripts/agent-end.sh' when finished to clean up"

# Output lock file path (for scripts to capture)
echo "$LOCK_FILE"
