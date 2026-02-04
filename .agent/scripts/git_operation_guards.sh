#!/bin/bash
# Git operation guard - prevents conflicting operations
# Used as git pre-commit and pre-push hook

BRANCH=$(git branch --show-current)
AGENT_ID="$1"  # Optional: passed from git hook
TASK_ID="$2"    # Optional: extracted from branch name

echo "🔒 Git operation guard checking branch: $BRANCH"

# Extract agent and task from branch name
if [[ "$BRANCH" =~ ^agent/([^/]+)/task-([^/]+)$ ]]; then
    BRANCH_AGENT="${BASH_REMATCH[1]}"
    BRANCH_TASK="${BASH_REMATCH[2]}"
elif [[ "$BRANCH" =~ ^dependabot/ ]] || [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "dev" ]]; then
    echo "⚠️  Operating on non-agent branch: $BRANCH"
    BRANCH_AGENT="system"
    BRANCH_TASK="none"
else
    echo "❌ ERROR: Branch name does not follow required format"
    echo "   Required: agent/<agent-name>/task-<task-id>"
    exit 1
fi

# Check if this agent owns this branch
if [ -n "$AGENT_ID" ] && [ "$BRANCH_AGENT" != "$AGENT_ID" ]; then
    echo "❌ ERROR: Cannot push to branch owned by agent $BRANCH_AGENT"
    echo "   Current agent: $AGENT_ID"
    echo "   Branch owner: $BRANCH_AGENT"
    exit 1
fi

# Validate task exclusivity
if [ -n "$BRANCH_TASK" ]; then
    if ! ./.agent/scripts/validate_task_exclusivity.sh "$BRANCH_TASK" "$BRANCH_AGENT" "check" >/dev/null 2>&1; then
        echo "❌ ERROR: Task $BRANCH_TASK is locked by another agent"
        exit 1
    fi
fi

# Check for uncommitted changes that might conflict
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  WARNING: Uncommitted changes detected"
    echo "   These changes should be committed before pushing to avoid conflicts"
fi

# Check for force push attempts
if [ "$1" = "--force" ] || [ "$2" = "--force" ]; then
    echo "❌ ERROR: Force push is not allowed on collaborative branches"
    echo "   Use git merge or git rebase instead"
    exit 1
fi

echo "✅ Git operation guard checks passed"
exit 0
