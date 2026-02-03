#!/bin/bash
# Resource release script
TASK_ID="$1"
AGENT_ID="$2"

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task_id> <agent_id>"
    exit 1
fi

echo "🧹 Releasing resources for task $TASK_ID by agent $AGENT_ID"

# Remove resource allocation file
RESOURCE_FILE=".agent/session_locks/resources_${TASK_ID}.json"
if [ -f "$RESOURCE_FILE" ]; then
    echo "   Removing resource allocation file: $RESOURCE_FILE"
    rm -f "$RESOURCE_FILE"
fi

# Remove worktree
WORKTREE_DIR="worktrees/$TASK_ID"
if [ -d "$WORKTREE_DIR" ]; then
    echo "   Removing worktree: $WORKTREE_DIR"
    cd "$(git rev-parse --show-toplevel)"
    git worktree remove "$WORKTREE_DIR" 2>/dev/null || rm -rf "$WORKTREE_DIR"
    cd - >/dev/null
fi

# Kill any processes using allocated ports
if [ -f "$RESOURCE_FILE" ]; then
    # Try to read from backup if main file was removed
    echo "   Checking for processes using allocated ports..."
    
    # Common port cleanup
    for port in 9620 9621 9622 3000 3001 3002 8000 8001 8002; do
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$PID" ]; then
            echo "   Killing process $PID using port $port"
            kill -9 $PID 2>/dev/null
        fi
    done
fi

echo "✅ Resource release completed"
exit 0