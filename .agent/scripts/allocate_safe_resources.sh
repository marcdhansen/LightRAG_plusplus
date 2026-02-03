#!/bin/bash
# Safe resource allocation script
# Allocates unique ports and worktrees to prevent conflicts

TASK_ID="$1"
AGENT_ID="$2"

if [ -z "$TASK_ID" ] || [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <task_id> <agent_id>"
    exit 1
fi

echo "🔧 Allocating safe resources for task $TASK_ID by agent $AGENT_ID"

# Base port ranges to allocate from
LIGHTRAG_PORT_BASE=9620
LANGFUSE_PORT_BASE=3000
AUTOMEM_PORT_BASE=8000
PORT_OFFSET_MAX=20

# Function to find available port
find_available_port() {
    local base_port=$1
    local offset=0
    
    while [ $offset -lt $PORT_OFFSET_MAX ]; do
        local port=$((base_port + offset))
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
        offset=$((offset + 1))
    done
    
    echo "ERROR: No available port found for base $base_port"
    return 1
}

# Find available ports with task-based offset
TASK_HASH=$(echo "$TASK_ID" | md5sum | cut -c1-2)
TASK_OFFSET=$((16#$TASK_HASH % 10))

LIGHTRAG_PORT=$(find_available_port $((LIGHTRAG_PORT_BASE + TASK_OFFSET)))
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot allocate LightRAG port"
    exit 1
fi

LANGFUSE_PORT=$(find_available_port $((LANGFUSE_PORT_BASE + TASK_OFFSET)))
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot allocate Langfuse port"
    exit 1
fi

AUTOMEM_PORT=$(find_available_port $((AUTOMEM_PORT_BASE + TASK_OFFSET)))
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot allocate Automem port"
    exit 1
fi

# Create isolated worktree
WORKTREE_DIR="worktrees/$TASK_ID"

# Clean up any existing worktree state more aggressively
echo "   Cleaning up any existing worktree $WORKTREE_DIR"

# Get to top-level git directory
cd "$(git rev-parse --show-toplevel)"

# Remove worktree using multiple methods
git worktree remove "$WORKTREE_DIR" 2>/dev/null || true
git worktree prune 2>/dev/null
rm -rf "$WORKTREE_DIR" 2>/dev/null

# Wait a moment for filesystem to sync
sleep 1

# Try to create worktree with more robust error handling
if ! git worktree add "$WORKTREE_DIR" HEAD; then
    echo "ERROR: Cannot create worktree $WORKTREE_DIR"
    exit 1
fi

# Verify worktree was created
if [ ! -d "$WORKTREE_DIR" ]; then
    echo "ERROR: Worktree $WORKTREE_DIR was not created successfully"
    exit 1
fi

# Save resource allocation
RESOURCE_FILE=".agent/session_locks/resources_${TASK_ID}.json"
cat > "$RESOURCE_FILE" << EOF
{
  "task_id": "$TASK_ID",
  "agent_id": "$AGENT_ID",
  "allocated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ports": {
    "lightrag": $LIGHTRAG_PORT,
    "langfuse": $LANGFUSE_PORT,
    "automem": $AUTOMEM_PORT
  },
  "worktree": "$WORKTREE_DIR",
  "status": "allocated"
}
EOF

echo "✅ Resources allocated successfully:"
echo "   LightRAG Port: $LIGHTRAG_PORT"
echo "   Langfuse Port: $LANGFUSE_PORT"
echo "   Automem Port: $AUTOMEM_PORT"
echo "   Worktree: $WORKTREE_DIR"
echo "   Config file: $RESOURCE_FILE"

# Export environment variables for use by other scripts
export LIGHTRAG_PORT=$LIGHTRAG_PORT
export LANGFUSE_PORT=$LANGFUSE_PORT
export AUTOMEM_PORT=$AUTOMEM_PORT
export WORKTREE_DIR="$WORKTREE_DIR"

exit 0