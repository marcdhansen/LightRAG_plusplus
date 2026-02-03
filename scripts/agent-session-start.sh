#!/bin/bash
# agent-session-start.sh - Mandatory session initialization script

set -e

echo "🤖 Agent Session Initialization"
echo "================================"

# Check arguments
if [[ $# -lt 2 ]]; then
  echo "❌ Usage: $0 --task-id <task-id> --task-desc <description> [--branch <branch-name>]"
  echo ""
  echo "Example: $0 --task-id lightrag-abc --task-desc 'Implement feature X' --branch agent/marchansen/task-lightrag-abc"
  exit 1
fi

# Parse arguments
TASK_ID=""
TASK_DESC=""
BRANCH_NAME=""

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
    --branch)
      BRANCH_NAME="$2"
      shift 2
      ;;
    *)
      echo "❌ Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$TASK_ID" || -z "$TASK_DESC" ]]; then
  echo "❌ Missing required arguments: --task-id and --task-desc are mandatory"
  exit 1
fi

# Generate branch name if not provided
if [[ -z "$BRANCH_NAME" ]]; then
  BRANCH_NAME="agent/marchansen/task-$TASK_ID"
fi

echo "📍 Task ID: $TASK_ID"
echo "📝 Description: $TASK_DESC"
echo "🌿 Branch: $BRANCH_NAME"

# Check agent status
echo "🔍 Checking agent status..."
if ./scripts/agent-status.sh | grep -q "Active agents"; then
  echo "⚠️  Other agents are working. Please coordinate with them."
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Create and checkout branch
echo "🌿 Creating branch: $BRANCH_NAME"
if ! git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  git checkout -b "$BRANCH_NAME"
else
  echo "📍 Branch exists, checking out: $BRANCH_NAME"
  git checkout "$BRANCH_NAME"
fi

# Create worktree if not exists
WORKTREE_PATH="worktrees/$TASK_ID"
if [[ ! -d "$WORKTREE_PATH" ]]; then
  echo "🌳 Creating worktree: $WORKTREE_PATH"
  mkdir -p worktrees
  git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
fi

# Change to worktree
echo "🔄 Switching to worktree: $WORKTREE_PATH"
cd "$WORKTREE_PATH"

# Create session lock
echo "🔒 Creating session lock..."
./scripts/agent-start.sh --task-id "$TASK_ID" --task-desc "$TASK_DESC"

# Verify setup
echo "✅ Session initialized successfully!"
echo "   🌿 Branch: $(git branch --show-current)"
echo "   📁 Worktree: $(pwd)"
echo "   🔒 Session: $TASK_ID"
echo ""
echo "📝 Working directory: $(pwd)"
echo "🚀 Ready to start work!"

# Show current agent status
echo ""
echo "📊 Current Agent Status:"
./scripts/agent-status.sh
