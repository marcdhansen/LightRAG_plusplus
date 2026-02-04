#!/bin/bash

# Simplified Execution Coordinator
# Streamlined workflow orchestration that combines and eliminates redundant steps

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Workflow state
WORKFLOW_MODE=""
TARGET_ACTION=""
CONTEXT_FILE=""
FAST_MODE=false
DRY_RUN=false

# Execution tracking
EXECUTED_STEPS=()
SKIPPED_STEPS=()
FAILED_STEPS=()

usage() {
    echo "Usage: $0 --action <action> [--mode <mode>] [--fast] [--dry-run]"
    echo ""
    echo "Simplified workflow coordinator that eliminates redundancy and streamlines execution"
    echo ""
    echo "Required:"
    echo "  --action <action>     Target action to execute"
    echo "                         Available: start, work, test, review, complete, emergency"
    echo ""
    echo "Optional:"
    echo "  --mode <mode>         Workflow mode (standard, quick, maintenance, recovery)"
    echo "                         Default: inferred from action"
    echo "  --context <file>      Context file with session information"
    echo "  --fast                Skip optional optimization steps"
    echo "  --dry-run             Show execution plan without running"
    echo ""
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --action)
            TARGET_ACTION="$2"
            shift 2
            ;;
        --mode)
            WORKFLOW_MODE="$2"
            shift 2
            ;;
        --context)
            CONTEXT_FILE="$2"
            shift 2
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$TARGET_ACTION" ]]; then
    echo -e "${RED}Error: --action is required${NC}"
    usage
fi

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%H:%M:%S')

    case "$level" in
        "INFO")
            echo -e "${GREEN}[INFO $timestamp]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN $timestamp]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR $timestamp]${NC} $message"
            ;;
        "DEBUG")
            echo -e "${CYAN}[DEBUG $timestamp]${NC} $message"
            ;;
    esac
}

# Function to infer workflow mode from action
infer_workflow_mode() {
    local action="$1"

    case "$action" in
        "emergency"|"recovery")
            echo "emergency"
            ;;
        "quick")
            echo "quick"
            ;;
        "maintenance")
            echo "maintenance"
            ;;
        *)
            echo "standard"
            ;;
    esac
}

# Function to load context
load_context() {
    local context_source="$1"

    if [[ -n "$context_source" && -f "$context_source" ]]; then
        log "DEBUG" "Loading context from: $context_source"
        cat "$context_source"
    elif [[ -f ".agent/session_context.json" ]]; then
        log "DEBUG" "Loading default session context"
        cat ".agent/session_context.json"
    else
        # Generate minimal context
        cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "working_directory": "$(pwd)",
  "git_status": $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ' || echo "0"),
  "user": "$(whoami)",
  "session_id": "$(date +%s)"
}
EOF
    fi
}

# Function to create optimized workflow plan
create_workflow_plan() {
    local action="$1"
    local mode="$2"
    local context="$3"

    log "DEBUG" "Creating optimized workflow plan for action: $action (mode: $mode)"

    # Define optimized workflows that eliminate redundancy
    case "$action" in
        "start")
            cat <<EOF
{
  "name": "session_start",
  "description": "Start new work session with optimized checks",
  "steps": [
    {
      "name": "intelligent_preflight",
      "description": "Smart preflight analysis based on context",
      "script": "intelligent_preflight_analyzer.sh",
      "args": ["$mode", "--skip-optional"],
      "critical": true,
      "combined": ["git_status", "resource_check", "session_lock"]
    },
    {
      "name": "allocate_resources",
      "description": "Allocate safe resources for work",
      "script": "allocate_safe_resources.sh",
      "critical": false,
      "condition": "$mode != emergency"
    },
    {
      "name": "show_ready_tasks",
      "description": "Show available work",
      "script": "bd",
      "args": ["ready"],
      "critical": false
    }
EOF
            ;;
        "work")
            cat <<EOF
{
  "name": "continue_work",
  "description": "Continue with current work session",
  "steps": [
    {
      "name": "session_check",
      "description": "Verify session is still valid",
      "script": "enhanced_session_locks.sh",
      "args": ["--check"],
      "critical": true
    },
    {
      "name": "sync_context",
      "description": "Sync with any external changes",
      "script": "git",
      "args": ["pull", "--rebase"],
      "critical": false,
      "condition": "$mode != emergency"
    },
    {
      "name": "show_status",
      "description": "Show current work status",
      "script": "bd",
      "args": ["status"],
      "critical": false
    }
EOF
            ;;
        "test")
            cat <<EOF
{
  "name": "run_tests",
  "description": "Execute relevant tests based on changes",
  "steps": [
    {
      "name": "detect_changes",
      "description": "Detect what has changed",
      "script": "git",
      "args": ["diff", "--name-only", "HEAD~1"],
      "critical": true
    },
    {
      "name": "run_targeted_tests",
      "description": "Run only tests relevant to changes",
      "script": "python",
      "args": ["-m", "pytest", "--reuse-db", "-v"],
      "critical": true,
      "combined": ["tdd_check", "quality_gate"]
    }
EOF
            ;;
        "review")
            cat <<EOF
{
  "name": "review_work",
  "description": "Review and validate completed work",
  "steps": [
    {
      "name": "quality_check",
      "description": "Run comprehensive quality checks",
      "script": "validate_tdd_compliance.sh",
      "critical": true,
      "combined": ["tdd_validation", "linting", "formatting"]
    },
    {
      "name": "documentation_check",
      "description": "Verify documentation integrity",
      "script": "verify_markdown_duplicates.sh",
      "critical": false
    }
EOF
            ;;
        "complete")
            cat <<EOF
{
  "name": "complete_session",
  "description": "Complete work session and cleanup",
  "steps": [
    {
      "name": "final_validation",
      "description": "Final validation before completion",
      "script": "sop_compliance_validator.py",
      "args": ["--critical-only"],
      "critical": true,
      "combined": ["final_checks", "cleanup_prep"]
    },
    {
      "name": "sync_changes",
      "description": "Sync all changes to remote",
      "script": "git",
      "args": ["push"],
      "critical": true
    },
    {
      "name": "cleanup_session",
      "description": "Cleanup session and release resources",
      "script": "release_resources.sh",
      "critical": false
    }
EOF
            ;;
        "emergency")
            cat <<EOF
{
  "name": "emergency_recovery",
  "description": "Emergency recovery with minimal checks",
  "steps": [
    {
      "name": "emergency_checks",
      "description": "Critical checks only",
      "script": "intelligent_preflight_analyzer.sh",
      "args": ["emergency", "--force-critical"],
      "critical": true
    },
    {
      "name": "stabilize_session",
      "description": "Stabilize current state",
      "script": "git",
      "args": ["stash"],
      "critical": false
    }
EOF
            ;;
        *)
            echo "Error: Unknown action: $action" >&2
            exit 1
            ;;
    esac

    echo "}"
}

# Function to execute workflow step
execute_step() {
    local step="$1"
    local step_name=$(echo "$step" | jq -r '.name')
    local description=$(echo "$step" | jq -r '.description')
    local script=$(echo "$step" | jq -r '.script // empty')
    local args=$(echo "$step" | jq -r '.args[]?' | tr '\n' ' ' || echo "")
    local critical=$(echo "$step" | jq -r '.critical // false')
    local condition=$(echo "$step" | jq -r '.condition // "true"')

    log "INFO" "Executing step: $step_name"
    log "DEBUG" "Description: $description"

    # Check condition
    if [[ "$condition" != "true" ]]; then
        log "DEBUG" "Step condition not met: $condition"
        SKIPPED_STEPS+=("$step_name (condition)")
        return 0
    fi

    # Skip combined steps if we have the info
    local combined_steps=$(echo "$step" | jq -r '.combined[]?' | tr '\n' ',' || echo "")
    if [[ -n "$combined_steps" && "$FAST_MODE" == "true" ]]; then
        log "INFO" "Fast mode: Skipping combined step: $combined_steps"
        SKIPPED_STEPS+=("$step_name (combined: $combined_steps)")
        return 0
    fi

    if [[ -z "$script" ]]; then
        log "DEBUG" "No script specified for step: $step_name"
        SKIPPED_STEPS+=("$step_name (no script)")
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "Would execute: $script $args"
        EXECUTED_STEPS+=("$step_name (dry-run)")
        return 0
    fi

    # Execute the step
    local full_command="$script $args"
    log "DEBUG" "Executing: $full_command"

    if eval "$full_command" 2>/dev/null; then
        log "DEBUG" "Step completed successfully: $step_name"
        EXECUTED_STEPS+=("$step_name")
        return 0
    else
        log "ERROR" "Step failed: $step_name"
        FAILED_STEPS+=("$step_name")

        if [[ "$critical" == "true" ]]; then
            log "ERROR" "Critical step failed, aborting workflow"
            return 1
        else
            log "WARN" "Non-critical step failed, continuing workflow"
            return 0
        fi
    fi
}

# Function to show workflow summary
show_workflow_summary() {
    echo ""
    echo -e "${CYAN}=== Workflow Execution Summary ===${NC}"
    echo "Action: $TARGET_ACTION"
    echo "Mode: $WORKFLOW_MODE"
    echo "Fast Mode: $FAST_MODE"
    echo ""

    if [[ ${#EXECUTED_STEPS[@]} -gt 0 ]]; then
        echo -e "${GREEN}✓ Executed Steps (${#EXECUTED_STEPS[@]}):${NC}"
        for step in "${EXECUTED_STEPS[@]}"; do
            echo "  ✓ $step"
        done
        echo ""
    fi

    if [[ ${#SKIPPED_STEPS[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⊘ Skipped Steps (${#SKIPPED_STEPS[@]}):${NC}"
        for step in "${SKIPPED_STEPS[@]}"; do
            echo "  ⊘ $step"
        done
        echo ""
    fi

    if [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
        echo -e "${RED}✗ Failed Steps (${#FAILED_STEPS[@]}):${NC}"
        for step in "${FAILED_STEPS[@]}"; do
            echo "  ✗ $step"
        done
        echo ""
    fi

    # Overall status
    if [[ ${#FAILED_STEPS[@]} -eq 0 ]]; then
        echo -e "${GREEN}🎉 Workflow completed successfully!${NC}"
    else
        echo -e "${RED}❌ Workflow completed with errors${NC}"
    fi
}

# Function to save session state
save_session_state() {
    local action="$1"
    local outcome="$2"
    local executed_steps="$3"
    local failed_steps="$4"

    local session_file=".agent/session_state.json"
    mkdir -p "$(dirname "$session_file")"

    cat <<EOF > "$session_file"
{
  "action": "$action",
  "mode": "$WORKFLOW_MODE",
  "outcome": "$outcome",
  "executed_steps": [$(echo "$executed_steps" | sed 's/^/"/' | sed 's/$/"/' | tr '\n' ',' | sed 's/,$//')],
  "failed_steps": [$(echo "$failed_steps" | sed 's/^/"/' | sed 's/$/"/' | tr '\n' ',' | sed 's/,$//')],
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "fast_mode": $FAST_MODE
}
EOF

    log "DEBUG" "Session state saved to: $session_file"
}

# Main execution function
main() {
    echo -e "${BLUE}=== Simplified Execution Coordinator ===${NC}"

    # Infer workflow mode if not specified
    if [[ -z "$WORKFLOW_MODE" ]]; then
        WORKFLOW_MODE=$(infer_workflow_mode "$TARGET_ACTION")
    fi

    echo "Action: $TARGET_ACTION"
    echo "Mode: $WORKFLOW_MODE"
    echo "Fast Mode: $FAST_MODE"
    echo ""

    # Load context
    local context=$(load_context "$CONTEXT_FILE")
    log "DEBUG" "Context loaded"

    # Create optimized workflow plan
    local workflow_plan=$(create_workflow_plan "$TARGET_ACTION" "$WORKFLOW_MODE" "$context")
    log "DEBUG" "Workflow plan created"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}=== Workflow Plan ===${NC}"
        echo "$workflow_plan" | jq -r '.description'
        echo ""
        echo "$workflow_plan" | jq -r '.steps[] | "- \(.name): \(.description)"'
        echo ""
    fi

    # Execute workflow steps
    local steps=$(echo "$workflow_plan" | jq -c '.steps[]')
    local workflow_failed=false

    while IFS= read -r step; do
        if ! execute_step "$step"; then
            workflow_failed=true
            break
        fi
    done <<< "$steps"

    # Show summary
    show_workflow_summary

    # Save session state
    local executed_steps_joined=$(IFS=,; echo "${EXECUTED_STEPS[*]}")
    local failed_steps_joined=$(IFS=,; echo "${FAILED_STEPS[*]}")
    local outcome="success"
    if [[ "$workflow_failed" == "true" ]]; then
        outcome="failed"
    elif [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
        outcome="partial"
    fi

    save_session_state "$TARGET_ACTION" "$outcome" "$executed_steps_joined" "$failed_steps_joined"

    # Exit with appropriate code
    if [[ "$workflow_failed" == "true" ]]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
