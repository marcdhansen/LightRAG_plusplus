#!/bin/bash
# Task exclusivity validation script
# Prevents multiple agents from working on the same task

TASK_ID="$1"
AGENT_ID="$2"
ACTION="$3"  # "check" or "claim"

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task_id> <agent_id> [action]"
    exit 1
fi

LOCK_DIR=".agent/session_locks"
LOCK_FILE="$LOCK_DIR/task_${TASK_ID}.lock"
HEARTBEAT_FILE="$LOCK_DIR/task_${TASK_ID}.heartbeat"

# Create lock directory if it doesn't exist
mkdir -p "$LOCK_DIR"

if [ "$ACTION" = "check" ]; then
    # Check if task is already locked
    if [ -f "$LOCK_FILE" ]; then
        LOCKED_AGENT=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        if [ "$LOCKED_AGENT" = "$AGENT_ID" ]; then
            echo "Task $TASK_ID is already locked by you (marchansen)"
            exit 0
        fi
        echo "ERROR: Task $TASK_ID is already locked by agent $LOCKED_AGENT"
        exit 1
    else
        echo "Task $TASK_ID is available"
        exit 0
    fi
fi

if [ "$ACTION" = "claim" ] || [ -z "$ACTION" ]; then
    # Attempt to claim the task
    if [ -f "$LOCK_FILE" ]; then
        LOCKED_AGENT=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        echo "ERROR: Task $TASK_ID is already locked by agent $LOCKED_AGENT"
        exit 1
    else
        # Create exclusive lock
        echo "$AGENT_ID" > "$LOCK_FILE"
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$HEARTBEAT_FILE"
        echo "Task $TASK_ID locked by agent $AGENT_ID"
        exit 0
    fi
fi

if [ "$ACTION" = "release" ]; then
    # Release the task lock
    if [ -f "$LOCK_FILE" ]; then
        LOCKED_AGENT=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
        if [ "$LOCKED_AGENT" = "$AGENT_ID" ]; then
            rm -f "$LOCK_FILE" "$HEARTBEAT_FILE"
            echo "Task $TASK_ID released by agent $AGENT_ID"
            exit 0
        else
            echo "ERROR: Cannot release task $TASK_ID - locked by agent $LOCKED_AGENT"
            exit 1
        fi
    else
        echo "Task $TASK_ID is not locked"
        exit 0
    fi
fi

echo "ERROR: Unknown action $ACTION"
echo "Usage: $0 <task_id> <agent_id> [check|claim|release]"
exit 1