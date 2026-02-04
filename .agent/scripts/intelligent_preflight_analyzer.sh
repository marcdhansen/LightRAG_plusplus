#!/bin/bash

# Intelligent Preflight Analyzer
# Context-aware analysis that determines what checks are actually needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")/config"
LEARN_DIR="$(dirname "$SCRIPT_DIR")/learn"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default settings
FAST_MODE=false
SKIP_OPTIONAL=false
SESSION_TYPE="standard"
VERBOSE=false
DRY_RUN=false

# Analysis results
ANALYSIS_RESULT=""
SKIPPED_CHECKS=()
REQUIRED_CHECKS=()
OPTIONAL_CHECKS=()
CRITICAL_CHECKS=()

usage() {
    echo "Usage: $0 [options] [session_type]"
    echo ""
    echo "Intelligent preflight analysis that adapts to context and history"
    echo ""
    echo "Arguments:"
    echo "  session_type        Type of session (standard, quick, maintenance, emergency)"
    echo ""
    echo "Options:"
    echo "  --fast              Skip optional and optimization checks"
    echo "  --skip-optional     Skip all optional checks"
    echo "  --dry-run           Show what would be checked without running"
    echo "  --verbose           Show detailed analysis reasoning"
    echo "  --force-all         Force all checks regardless of context"
    echo "  --learn             Enable learning mode for check adaptation"
    echo ""
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST_MODE=true
            SKIP_OPTIONAL=true
            shift
            ;;
        --skip-optional)
            SKIP_OPTIONAL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --force-all)
            FORCE_ALL=true
            shift
            ;;
        --learn)
            LEARN_MODE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            ;;
        *)
            SESSION_TYPE="$1"
            shift
            ;;
    esac
done

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
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${CYAN}[DEBUG $timestamp]${NC} $message"
            fi
            ;;
        "CRITICAL")
            echo -e "${RED}[CRITICAL $timestamp]${NC} $message"
            ;;
    esac
}

# Function to analyze git state
analyze_git_state() {
    log "DEBUG" "Analyzing git repository state"

    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log "DEBUG" "Not in a git repository"
        return 1
    fi

    local git_state=$(git status --porcelain=v1 2>/dev/null)
    local branch_name=$(git branch --show-current 2>/dev/null || echo "detached")
    local has_staged=false
    local has_unstaged=false
    local has_untracked=false

    if [[ -n "$git_state" ]]; then
        if echo "$git_state" | grep -q "^[MADRCU] "; then
            has_staged=true
        fi
        if echo "$git_state" | grep -q "^.[MADRCU]"; then
            has_unstaged=true
        fi
        if echo "$git_state" | grep -q "^??"; then
            has_untracked=true
        fi
    fi

    cat <<EOF
{
  "is_git_repo": true,
  "branch": "$branch_name",
  "has_staged_changes": $has_staged,
  "has_unstaged_changes": $has_unstaged,
  "has_untracked_files": $has_untracked,
  "is_dirty": [[ "$git_state" != "" ]]
}
EOF
}

# Function to analyze recent session history
analyze_session_history() {
    log "DEBUG" "Analyzing recent session history"

    local history_file="$LEARN_DIR/session_history.jsonl"
    local recent_sessions=0
    local error_rate=0
    local common_failures=()

    if [[ -f "$history_file" ]]; then
        # Get last 10 sessions
        local recent_data=$(tail -n 10 "$history_file" 2>/dev/null || echo "")

        if [[ -n "$recent_data" ]]; then
            recent_sessions=$(echo "$recent_data" | wc -l | tr -d ' ')

            # Calculate error rate
            local failed_sessions=$(echo "$recent_data" | jq -r 'select(.status == "failed")' | wc -l | tr -d ' ')
            if [[ $recent_sessions -gt 0 ]]; then
                error_rate=$((failed_sessions * 100 / recent_sessions))
            fi

        # Find common failure points
        local common_failures=$(echo "$recent_data" | jq -r 'select(.status == "failed") | .failure_point' 2>/dev/null | sort | uniq -c | sort -nr | head -3 | jq -R -s 'split("\n") | map(select(length > 0))' || echo '[]')
        fi
    fi

    cat <<EOF
{
  "recent_sessions": $recent_sessions,
  "error_rate": $error_rate,
  "common_failures": $common_failures,
  "last_session": $(tail -n 1 "$history_file" 2>/dev/null | jq . 2>/dev/null || echo "null")
}
EOF
}

# Function to analyze system resources
analyze_system_resources() {
    log "DEBUG" "Analyzing system resources"

    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    local memory_usage=""
    local cpu_load=""

    # Try to get memory usage (macOS)
    if command -v vm_stat >/dev/null 2>&1; then
        local page_size=$(vm_stat | head -1 | sed 's/.*page size of \([0-9]*\).*/\1/' || echo "4096")
        local free_pages=$(vm_stat | grep "Pages free" | sed 's/.*\([0-9]*\).*/\1/' || echo "0")
        local inactive_pages=$(vm_stat | grep "Pages inactive" | sed 's/.*\([0-9]*\).*/\1/' || echo "0")

        # Get active and wired pages safely
        local active_pages=$(vm_stat | grep "Pages active" | sed 's/.*\([0-9]*\).*/\1/' || echo "0")
        local wired_pages=$(vm_stat | grep "Pages wired" | sed 's/.*\([0-9]*\).*/\1/' || echo "0")

        local used_memory=$(( (active_pages + wired_pages) * page_size / 1024 / 1024 / 1024 ))

        # Convert to percentage (rough estimate)
        memory_usage="$used_memory GB"
    fi

    # Get CPU load
    if command -v uptime >/dev/null 2>&1; then
        cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    fi

    cat <<EOF
{
  "disk_usage_percent": $disk_usage,
  "memory_usage": "$memory_usage",
  "cpu_load": "$cpu_load",
  "resources_ok": [[ $disk_usage -lt 90 ]]
}
EOF
}

# Function to analyze task context
analyze_task_context() {
    log "DEBUG" "Analyzing current task context"

    local current_task=""
    local task_type=""
    local task_complexity="medium"
    local has_dependencies=false

    # Check for current task
    if [[ -f ".beads/current.json" ]]; then
        current_task=$(jq -r '.id // ""' .beads/current.json 2>/dev/null || echo "")
        task_type=$(jq -r '.type // ""' .beads/current.json 2>/dev/null || echo "")

        # Determine complexity based on task tags
        local tags=$(jq -r '.tags[]?' .beads/current.json 2>/dev/null | tr '\n' ' ' || echo "")
        if [[ "$tags" =~ (complex|architecture|refactoring) ]]; then
            task_complexity="high"
        elif [[ "$tags" =~ (simple|fix|docs) ]]; then
            task_complexity="low"
        fi

        # Check for dependencies
        local deps=$(jq -r '.dependencies[]?' .beads/current.json 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ $deps -gt 0 ]]; then
            has_dependencies=true
        fi
    fi

    cat <<EOF
{
  "current_task": "$current_task",
  "task_type": "$task_type",
  "task_complexity": "$task_complexity",
  "has_dependencies": $has_dependencies,
  "task_active": [[ $current_task != "" ]]
}
EOF
}

# Function to determine check necessity
determine_check_necessity() {
    local check_name="$1"
    local check_category="$2"
    local criticality="$3"
    local context="$4"

    # Skip if forced all mode is off and check is not critical
    if [[ "${FORCE_ALL:-false}" != "true" && "$criticality" != "critical" ]]; then
        case "$check_category" in
            "optional")
                if [[ "$SKIP_OPTIONAL" == "true" || "$FAST_MODE" == "true" ]]; then
                    echo "skip"
                    return
                fi
                ;;
            "optimization")
                if [[ "$FAST_MODE" == "true" ]]; then
                    echo "skip"
                    return
                fi
                ;;
        esac
    fi

    # Context-specific logic
        case "$check_name" in
            "git_hooks")
                # Only check if we're in a git repo with changes
                local is_git=$(echo "$1" | jq -r '.git_state.is_git_repo // false')
                local has_changes=$(echo "$1" | jq -r '.git_state.has_unstaged_changes // false')
                if [[ "$is_git" != "true" || "$has_changes" != "true" ]]; then
                    echo "skip"
                    return
                fi
                ;;
            "resource_allocation")
                # Skip if not starting new work
                if [[ "$SESSION_TYPE" == "quick" || "$SESSION_TYPE" == "maintenance" ]]; then
                    echo "skip"
                    return
                fi
                ;;
            "dependency_check")
                # Only if task has dependencies
                local has_deps=$(echo "$1" | jq -r '.task_context.has_dependencies // false')
                if [[ "$has_deps" != "true" ]]; then
                    echo "skip"
                    return
                fi
                ;;
            "quality_gates")
                # Skip for emergency sessions
                if [[ "$SESSION_TYPE" == "emergency" ]]; then
                    echo "skip"
                    return
                fi
                ;;
        esac

    echo "run"
}

# Function to run individual check
run_check() {
    local check_name="$1"
    local check_script="$2"

    log "DEBUG" "Running check: $check_name"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "Would run: $check_script"
        return 0
    fi

    if [[ -x "$SCRIPT_DIR/$check_script" ]]; then
        if timeout 30 "$SCRIPT_DIR/$check_script" 2>/dev/null; then
            log "DEBUG" "Check passed: $check_name"
            return 0
        else
            log "WARN" "Check failed or timed out: $check_name"
            return 1
        fi
    else
        log "WARN" "Check script not found: $check_script"
        return 1
    fi
}

# Function to record session outcome
record_session_outcome() {
    local outcome="$1"
    local failure_point="$2"
    local session_data="$3"

    local history_file="$LEARN_DIR/session_history.jsonl"
    mkdir -p "$LEARN_DIR"

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local session_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "session_type": "$SESSION_TYPE",
  "outcome": "$outcome",
  "failure_point": "$failure_point",
  "analysis": $session_data,
  "fast_mode": $FAST_MODE,
  "skip_optional": $SKIP_OPTIONAL,
  "checks_run": ${#REQUIRED_CHECKS[@]},
  "checks_skipped": ${#SKIPPED_CHECKS[@]}
}
EOF
)

    echo "$session_entry" >> "$history_file"
    log "DEBUG" "Session outcome recorded to $history_file"
}

# Function to adapt check selection based on learning
adapt_check_selection() {
    local history_analysis="$1"

    if [[ "${LEARN_MODE:-false}" != "true" ]]; then
        return
    fi

    local error_rate=$(echo "$history_analysis" | jq -r '.error_rate // 0')
    local common_failures=$(echo "$history_analysis" | jq -r '.common_failures[]? // empty')

    # If high error rate, be more conservative
    if [[ $error_rate -gt 50 ]]; then
        log "INFO" "High error rate detected ($error_rate%), enabling more checks"
        SKIP_OPTIONAL=false
    fi

    # If specific checks commonly fail, ensure they run
    while IFS= read -r failure_point; do
        if [[ -n "$failure_point" ]]; then
            log "INFO" "Common failure point: $failure_point, ensuring check runs"
            # Add logic to force specific checks
            case "$failure_point" in
                "git_hooks")
                    # Ensure git hooks check is not skipped
                    SKIP_OPTIONAL=false
                    ;;
                "quality_gates")
                    # Ensure quality gates run
                    FAST_MODE=false
                    ;;
            esac
        fi
    done <<< "$common_failures"
}

# Main analysis function
main() {
    echo -e "${BLUE}=== Intelligent Preflight Analyzer ===${NC}"
    echo "Session Type: ${SESSION_TYPE:-standard}"
    echo "Fast Mode: $FAST_MODE"
    echo "Skip Optional: $SKIP_OPTIONAL"
    echo ""

    # Collect context data
    log "INFO" "Collecting context data for intelligent analysis"

    local git_state=$(analyze_git_state)
    local session_history=$(analyze_session_history)
    local system_resources=$(analyze_system_resources)
    local task_context=$(analyze_task_context)

    # Build complete context
    local context=$(cat <<EOF
{
  "git_state": $git_state,
  "session_history": $session_history,
  "system_resources": $system_resources,
  "task_context": $task_context,
  "session_type": "$SESSION_TYPE",
  "fast_mode": $FAST_MODE,
  "skip_optional": $SKIP_OPTIONAL
}
EOF
)

    if [[ "$VERBOSE" == "true" ]]; then
        log "DEBUG" "Context analysis complete"
        echo "$context" | jq .
    fi

    # Adapt check selection based on learning
    adapt_check_selection "$session_history"

    # Define available checks
    declare -A checks=(
        ["git_status"]="check_git_status.sh|critical|core"
        ["git_hooks"]="install_git_hooks.sh|critical|core"
        ["resource_allocation"]="allocate_safe_resources.sh|critical|core"
        ["symlink_health"]="validate_symlink_health.sh|important|core"
        ["tdd_gates"]="validate_tdd_compliance.sh|important|core"
        ["quality_gates"]="tdd_gate_validator.py|optional|quality"
        ["branch_protection"]="main_branch_protection.sh|important|git"
        ["version_consistency"]="validate_version_consistency.py|optional|quality"
        ["session_locks"]="enhanced_session_locks.sh|critical|core"
        ["markdown_integrity"]="verify_markdown_duplicates.sh|optional|cleanup"
    )

    # Determine which checks to run
    log "INFO" "Determining necessary checks based on context"

    for check_name in "${!checks[@]}"; do
        local check_info="${checks[$check_name]}"
        local check_script=$(echo "$check_info" | cut -d'|' -f1)
        local criticality=$(echo "$check_info" | cut -d'|' -f2)
        local category=$(echo "$check_info" | cut -d'|' -f3)

        local necessity=$(determine_check_necessity "$check_name" "$category" "$criticality" "$context")

        case "$necessity" in
            "run")
                case "$criticality" in
                    "critical")
                        CRITICAL_CHECKS+=("$check_name|$check_script")
                        ;;
                    "important")
                        REQUIRED_CHECKS+=("$check_name|$check_script")
                        ;;
                    "optional")
                        OPTIONAL_CHECKS+=("$check_name|$check_script")
                        ;;
                esac
                ;;
            "skip")
                SKIPPED_CHECKS+=("$check_name")
                log "DEBUG" "Skipping check: $check_name (context: $category, $criticality)"
                ;;
        esac
    done

    # Show analysis results
    echo -e "${CYAN}=== Analysis Results ===${NC}"
    echo "Critical Checks (${#CRITICAL_CHECKS[@]}):"
    for check in "${CRITICAL_CHECKS[@]}"; do
        local name=$(echo "$check" | cut -d'|' -f1)
        echo "  ✓ $name"
    done

    echo ""
    echo "Required Checks (${#REQUIRED_CHECKS[@]}):"
    for check in "${REQUIRED_CHECKS[@]}"; do
        local name=$(echo "$check" | cut -d'|' -f1)
        echo "  ✓ $name"
    done

    if [[ ${#OPTIONAL_CHECKS[@]} -gt 0 ]]; then
        echo ""
        echo "Optional Checks (${#OPTIONAL_CHECKS[@]}):"
        for check in "${OPTIONAL_CHECKS[@]}"; do
            local name=$(echo "$check" | cut -d'|' -f1)
            echo "  ○ $name"
        done
    fi

    if [[ ${#SKIPPED_CHECKS[@]} -gt 0 ]]; then
        echo ""
        echo "Skipped Checks (${#SKIPPED_CHECKS[@]}):"
        for check in "${SKIPPED_CHECKS[@]}"; do
            echo "  ⊘ $check"
        done
    fi

    # Run checks if not dry run
    if [[ "$DRY_RUN" != "true" ]]; then
        echo ""
        log "INFO" "Running critical and required checks..."

        local failed_checks=()

        # Run critical checks first
        for check in "${CRITICAL_CHECKS[@]}"; do
            local name=$(echo "$check" | cut -d'|' -f1)
            local script=$(echo "$check" | cut -d'|' -f2)

            if ! run_check "$name" "$script"; then
                failed_checks+=("$name")
                record_session_outcome "failed" "$name" "$context"
                log "CRITICAL" "Critical check failed: $name"
                exit 1
            fi
        done

        # Run required checks
        for check in "${REQUIRED_CHECKS[@]}"; do
            local name=$(echo "$check" | cut -d'|' -f1)
            local script=$(echo "$check" | cut -d'|' -f2)

            if ! run_check "$name" "$script"; then
                failed_checks+=("$name")
            fi
        done

        # Run optional checks if not skipped
        if [[ "$SKIP_OPTIONAL" != "true" ]]; then
            for check in "${OPTIONAL_CHECKS[@]}"; do
                local name=$(echo "$check" | cut -d'|' -f1)
                local script=$(echo "$check" | cut -d'|' -f2)

                run_check "$name" "$script"
            done
        fi

        # Record successful outcome
        if [[ ${#failed_checks[@]} -eq 0 ]]; then
            record_session_outcome "success" "" "$context"
            echo ""
            log "INFO" "All critical checks passed successfully!"
        else
            echo ""
            log "WARN" "Some checks failed: ${failed_checks[*]}"
            record_session_outcome "partial" "${failed_checks[0]}" "$context"
        fi
    else
        echo ""
        log "INFO" "Dry run complete. No checks executed."
    fi

    # Store analysis for other scripts
    ANALYSIS_RESULT="$context"
}

# Run main function
main "$@"
