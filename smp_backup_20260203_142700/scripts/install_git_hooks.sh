#!/bin/bash
# Git hooks installation script
# Installs enhanced conflict prevention hooks

echo "🔧 Installing enhanced conflict prevention git hooks..."

# Create git hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook: validates task exclusivity and branch naming

BRANCH=$(git branch --show-current)

# Extract task from branch name
if [[ "$BRANCH" =~ ^agent/([^/]+)/task-([^/]+)$ ]]; then
    AGENT_ID="${BASH_REMATCH[1]}"
    TASK_ID="${BASH_REMATCH[2]}"

    # Validate task exclusivity
    if ! ./scripts/validate_task_exclusivity.sh "$TASK_ID" "$AGENT_ID" "check" >/dev/null 2>&1; then
        echo "❌ ERROR: Task $TASK_ID is locked by another agent"
        exit 1
    fi

    # Run git operation guard
    ./scripts/git_operation_guards.sh "$AGENT_ID" "$TASK_ID"
    if [ $? -ne 0 ]; then
        exit 1
    fi
else
    echo "❌ ERROR: Branch name does not follow required format"
    echo "   Required: agent/<agent-name>/task-<task-id>"
    exit 1
fi

exit 0
EOF

# Install pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook: validates push operations

BRANCH=$(git branch --show-current)

# Extract task from branch name
if [[ "$BRANCH" =~ ^agent/([^/]+)/task-([^/]+)$ ]]; then
    AGENT_ID="${BASH_REMATCH[1]}"
    TASK_ID="${BASH_REMATCH[2]}"

    # Run git operation guard for push
    ./scripts/git_operation_guards.sh "$AGENT_ID" "$TASK_ID" "$@"
    if [ $? -ne 0 ]; then
        exit 1
    fi
else
    echo "❌ ERROR: Branch name does not follow required format"
    exit 1
fi

exit 0
EOF

# Install prepare-commit-msg hook
cat > .git/hooks/prepare-commit-msg << 'EOF'
#!/bin/bash
# Prepare commit message hook: validates task ID format

COMMIT_MSG_FILE="$1"
COMMIT_MSG_SOURCE="$2"
COMMIT_HASH="$3"

# Skip validation for merge commits or rebases
if [ "$COMMIT_MSG_SOURCE" = "merge" ] || [ "$COMMIT_MSG_SOURCE" = "commit" ]; then
    exit 0
fi

BRANCH=$(git branch --show-current)

# Extract task from branch name
if [[ "$BRANCH" =~ ^agent/([^/]+)/task-([^/]+)$ ]]; then
    TASK_ID="${BASH_REMATCH[2]}"

    # Check if commit message contains task ID
    if ! grep -q "$TASK_ID" "$COMMIT_MSG_FILE"; then
        echo "⚠️  WARNING: Commit message should contain task ID: $TASK_ID"
        echo "   This helps with tracking and organization"
    fi
fi

exit 0
EOF

# Make hooks executable
chmod +x .git/hooks/pre-commit .git/hooks/pre-push .git/hooks/prepare-commit-msg

echo "✅ Git hooks installed successfully:"
echo "   pre-commit: Validates task exclusivity and branch naming"
echo "   pre-push: Validates push operations"
echo "   prepare-commit-msg: Validates commit message format"

exit 0
