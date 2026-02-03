#!/bin/bash
# Heartbeat script for session management
AGENT_ID="$1"
TASK_ID="$2"

if [ -z "$AGENT_ID" ] || [ -z "$TASK_ID" ]; then
    echo "Usage: $0 <agent_id> <task_id>"
    exit 1
fi

LOCK_DIR=".agent/session_locks"
SESSION_FILE="$LOCK_DIR/session_${AGENT_ID}_${TASK_ID}.json"
HEARTBEAT_INTERVAL=300  # 5 minutes

heartbeat() {
    while true; do
        if [ -f "$SESSION_FILE" ]; then
            # Update heartbeat timestamp
            sed -i.bak "s/\"last_heartbeat\": \".*\"/\"last_heartbeat\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/" "$SESSION_FILE"
            rm -f "$SESSION_FILE.bak"
        else
            echo "Session file disappeared, stopping heartbeat"
            exit 0
        fi

        sleep $HEARTBEAT_INTERVAL
    done
}

# Start heartbeat loop
heartbeat
