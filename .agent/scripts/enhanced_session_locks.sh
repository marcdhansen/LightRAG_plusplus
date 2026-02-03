#!/bin/bash
# Enhanced session management script
# Provides improved session lock management with cleanup

TASK_ID="$1"
AGENT_ID="$2"
ACTION="$3"  # "start", "check", "end", "cleanup"

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ] || [ -z "$ACTION" ]; then
    echo "Usage: $0 <task_id> <agent_id> <action>"
    echo "Actions: start, check, end, cleanup"
    exit 1
fi

LOCK_DIR=".agent/session_locks"
SESSION_FILE="$LOCK_DIR/session_${AGENT_ID}_${TASK_ID}.json"
HEARTBEAT_INTERVAL=300  # 5 minutes

# Ensure lock directory exists
mkdir -p "$LOCK_DIR"

start_session() {
    echo "🚀 Starting session for task $TASK_ID by agent $AGENT_ID"
    
    # Check for existing session
    if [ -f "$SESSION_FILE" ]; then
        echo "WARNING: Existing session found for agent $AGENT_ID on task $TASK_ID"
        echo "Cleaning up old session first..."
        cleanup_session
    fi
    
    # Create session lock
    cat > "$SESSION_FILE" << EOF
{
  "agent_id": "$AGENT_ID",
  "session_id": "$(date +%s)",
  "task_id": "$TASK_ID",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_heartbeat": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "heartbeat_interval": $HEARTBEAT_INTERVAL,
  "status": "active",
  "workspace": "$(pwd)"
}
EOF
    
    # Start heartbeat in background
    ./.agent/scripts/start_heartbeat.sh "$AGENT_ID" "$TASK_ID" &
    HEARTBEAT_PID=$!
    
    echo "✅ Session started successfully"
    echo "   Session file: $SESSION_FILE"
    echo "   Heartbeat PID: $HEARTBEAT_PID"
    
    exit 0
}

check_session() {
    if [ -f "$SESSION_FILE" ]; then
        echo "✅ Active session found for agent $AGENT_ID on task $TASK_ID"
        echo "   Status: $(grep -o '"status": "[^"]*"' "$SESSION_FILE" | cut -d'"' -f4)"
        echo "   Last heartbeat: $(grep -o '"last_heartbeat": "[^"]*"' "$SESSION_FILE" | cut -d'"' -f4)"
        exit 0
    else
        echo "❌ No active session found for agent $AGENT_ID on task $TASK_ID"
        exit 1
    fi
}

end_session() {
    echo "🛬 Ending session for task $TASK_ID by agent $AGENT_ID"
    
    if [ -f "$SESSION_FILE" ]; then
        # Update session status
        sed -i.bak 's/"status": "active"/"status": "ended"/' "$SESSION_FILE"
        sed -i.bak "s/\"last_heartbeat\": \".*\"/\"last_heartbeat\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/" "$SESSION_FILE"
        rm -f "$SESSION_FILE.bak"
        
        # Stop heartbeat
        pkill -f "heartbeat_${AGENT_ID}_${TASK_ID}"
        
        # Release resources
        ./.agent/scripts/release_resources.sh "$TASK_ID" "$AGENT_ID"
        
        echo "✅ Session ended successfully"
        exit 0
    else
        echo "❌ No active session found for agent $AGENT_ID on task $TASK_ID"
        exit 1
    fi
}

cleanup_session() {
    echo "🧹 Cleaning up session for agent $AGENT_ID on task $TASK_ID"
    
    # Stop heartbeat processes
    pkill -f "heartbeat_${AGENT_ID}_${TASK_ID}"
    
    # Remove session file
    rm -f "$SESSION_FILE"
    
    # Release task lock
    ./.agent/scripts/validate_task_exclusivity.sh "$TASK_ID" "$AGENT_ID" "release"
    
    # Release resources
    ./.agent/scripts/release_resources.sh "$TASK_ID" "$AGENT_ID"
    
    echo "✅ Session cleanup completed"
    exit 0
}

# Execute requested action
case "$ACTION" in
    start)
        start_session
        ;;
    check)
        check_session
        ;;
    end)
        end_session
        ;;
    cleanup)
        cleanup_session
        ;;
    *)
        echo "ERROR: Unknown action $ACTION"
        exit 1
        ;;
esac