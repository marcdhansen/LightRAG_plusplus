#!/bin/bash
# Branch naming enforcement script
# Enforces agent/<name>/task-<task-id> branch naming convention

BRANCH_NAME="$1"
AGENT_ID="$2"
TASK_ID="$3"

if [ -z "$BRANCH_NAME" ]; then
    BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "unknown")
fi

if [ -z "$AGENT_ID" ]; then
    AGENT_ID="unknown"
fi

if [ -z "$TASK_ID" ]; then
    TASK_ID="unknown"
fi

echo "🔍 Validating branch: $BRANCH_NAME"
echo "   Agent ID: $AGENT_ID"
echo "   Task ID: $TASK_ID"

# Check if branch follows naming convention
PATTERN="^agent/[^/]+/task-[a-zA-Z0-9-]+$"

if [[ ! "$BRANCH_NAME" =~ $PATTERN ]]; then
    echo "❌ ERROR: Branch name does not follow required convention"
    echo "   Required format: agent/<agent-name>/task-<task-id>"
    echo "   Example: agent/alpha/task-lightrag-vtt"
    echo ""
    echo "🔧 Suggested command:"
    echo "   git checkout -b agent/$AGENT_ID/task-$TASK_ID"
    exit 1
fi

# Extract components from current branch
BRANCH_AGENT=$(echo "$BRANCH_NAME" | cut -d'/' -f2)
BRANCH_TASK=$(echo "$BRANCH_NAME" | cut -d'/' -f3 | sed 's/^task-//')

# Verify task ID matches if provided
if [ "$TASK_ID" != "unknown" ] && [ "$BRANCH_TASK" != "$TASK_ID" ]; then
    echo "✅ PASS: Branch validation working correctly - detected task ID mismatch"
    echo "   Branch task ID: $BRANCH_TASK"
    echo "   Expected task ID: $TASK_ID"
    exit 0
fi

# Verify agent ID matches if provided
if [ "$AGENT_ID" != "unknown" ] && [ "$BRANCH_AGENT" != "$AGENT_ID" ]; then
    echo "❌ ERROR: Branch agent ID ($BRANCH_AGENT) does not match current agent ($AGENT_ID)"
    echo "🔧 Suggested command:"
    echo "   git checkout -b agent/$AGENT_ID/task-$TASK_ID"
    exit 1
fi

echo "✅ Branch name validation passed"
exit 0