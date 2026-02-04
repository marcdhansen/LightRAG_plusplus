#!/bin/bash

# Beads Issue Validation Script
# MANDATORY: Validates beads issue exists for all feature development work

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_NAME="Beads Issue Validator"
VERSION="1.0.0"
STRICT_MODE=${STRICT_MODE:-true}

# Logging function
log_validation() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}"
            ;;
    esac
}

# Function to check if beads is available
check_beads_availability() {
    if ! command -v bd &> /dev/null; then
        log_validation "ERROR" "Beads (bd) command not available"
        echo "  Required: Install beads to track issues"
        echo "  Installation: npm install -g @beadsdev/beads"
        return 1
    fi
    
    log_validation "SUCCESS" "Beads command available"
    return 0
}

# Function to check if we're in a beads-enabled repository
check_beads_repository() {
    if [[ ! -d ".beads" ]]; then
        log_validation "ERROR" "Not in a beads-enabled repository"
        echo "  Required: Initialize beads in this repository"
        echo "  Command: bd init"
        return 1
    fi
    
    log_validation "SUCCESS" "Beads repository detected"
    return 0
}

# Function to detect feature context from current changes
detect_feature_context() {
    local feature_name=""
    local has_code_changes=false
    local has_test_changes=false
    local has_doc_changes=false
    
    # Analyze git changes to infer feature
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local git_status=$(git status --porcelain=v1 2>/dev/null || echo "")
        
        if [[ -n "$git_status" ]]; then
            # Look for patterns in changed files to infer feature name
            feature_name=$(echo "$git_status" | head -5 | grep -E "\.(py|js|ts|md)$" | head -1 | sed 's/.* //' | sed 's/\.[^.]*$//' | sed 's/.*\///' || echo "")
            
            # Check for different types of changes
            if echo "$git_status" | grep -E "\.(py|js|ts|go|java|cpp|c)$" >/dev/null; then
                has_code_changes=true
            fi
            
            if echo "$git_status" | grep -E "test_.*\.py|.*_test\.py|.*\.test\.js|.*\.spec\.js" >/dev/null; then
                has_test_changes=true
            fi
            
            if echo "$git_status" | grep -E "\.md$" >/dev/null; then
                has_doc_changes=true
            fi
        fi
    fi
    
    # Try to get feature from environment or current task
    if [[ -z "$feature_name" ]]; then
        if [[ -n "${FEATURE_NAME:-}" ]]; then
            feature_name="$FEATURE_NAME"
        elif [[ -f ".beads/current.json" ]]; then
            feature_name=$(jq -r '.title // ""' .beads/current.json 2>/dev/null | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | head -c 30 || echo "")
        fi
    fi
    
    cat <<EOF
{
  "feature_name": "$feature_name",
  "has_code_changes": $has_code_changes,
  "has_test_changes": $has_test_changes,
  "has_doc_changes": $has_doc_changes,
  "has_any_changes": $([[ "$has_code_changes" == "true" || "$has_test_changes" == "true" || "$has_doc_changes" == "true" ]] && echo true || echo false)
}
EOF
}

# Function to validate beads issue exists
validate_beads_issue() {
    local feature_context=$1
    local feature_name=$(echo "$feature_context" | jq -r '.feature_name // ""')
    local has_changes=$(echo "$feature_context" | jq -r '.has_any_changes // false')
    
    log_validation "INFO" "Validating beads issue for feature context"
    echo "  Feature name: $feature_name"
    echo "  Has changes: $has_changes"
    
    # If no changes detected, this might be a setup/maintenance session
    if [[ "$has_changes" != "true" ]]; then
        log_validation "INFO" "No feature changes detected - beads validation not required"
        return 0
    fi
    
    # Check if there are any open beads issues
    local open_issues=$(bd list --status open 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    local all_issues=$(bd list --all 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    
    echo "  Open issues: $open_issues"
    echo "  Total issues: $all_issues"
    
    if [[ $all_issues -eq 0 ]]; then
        log_validation "ERROR" "No beads issues found in repository"
        echo ""
        echo "MANDATORY ACTIONS:"
        echo "1. Create beads issue for your feature work"
        echo "   Command: bd create -t \"Feature: $feature_name\" -p P0 -c \"Implementation of $feature_name feature\""
        echo "2. Reference issue in commit messages"
        echo ""
        return 1
    fi
    
    # If feature name is available, check for matching issues
    if [[ -n "$feature_name" ]]; then
        local matching_issues=$(bd list --all 2>/dev/null | grep -i "$feature_name" | wc -l | tr -d ' ' || echo "0")
        
        if [[ $matching_issues -eq 0 ]]; then
            log_validation "WARN" "No beads issues found for feature: $feature_name"
            echo "  Consider creating specific issue for this feature"
            echo "  Command: bd create -t \"Feature: $feature_name\" -p P0 -c \"Implementation of $feature_name feature\""
        else
            log_validation "SUCCESS" "Found $matching_issues beads issue(s) for feature: $feature_name"
        fi
    fi
    
    # Check current task
    if [[ -f ".beads/current.json" ]]; then
        local current_issue=$(jq -r '.id // "none"' .beads/current.json 2>/dev/null)
        local current_title=$(jq -r '.title // "none"' .beads/current.json 2>/dev/null)
        
        log_validation "INFO" "Current beads task: $current_issue - $current_title"
        
        if [[ "$current_issue" != "none" ]]; then
            log_validation "SUCCESS" "Active beads task detected"
        else
            log_validation "WARN" "No active beads task set"
            echo "  Consider setting current task: bd current <issue-id>"
        fi
    else
        log_validation "WARN" "No current beads task file found"
    fi
    
    return 0
}

# Function to auto-suggest beads issue creation
suggest_beads_creation() {
    local feature_context=$1
    local feature_name=$(echo "$feature_context" | jq -r '.feature_name // ""')
    
    if [[ -n "$feature_name" ]]; then
        echo ""
        echo "SUGGESTED BEADS ISSUE COMMANDS:"
        echo "================================"
        echo "# Create new issue for feature"
        echo "bd create -t \"Feature: $feature_name\" -p P0 -c \"Implementation of $feature_name with TDD compliance\""
        echo ""
        echo "# Set as current task"
        echo "bd current <new-issue-id>"
        echo ""
        echo "# Reference in commits"
        echo "git commit -m \"feat: implement $feature_name [lightrag-xxx]\""
    fi
}

# Function to block work without beads compliance
block_without_beads() {
    local reason=$1
    
    log_validation "ERROR" "BEADS COMPLIANCE VIOLATION"
    echo "VIOLATION: $reason"
    echo ""
    echo "🚫 BEADS COMPLIANCE IS MANDATORY - CANNOT PROCEED"
    echo ""
    echo "Required Actions:"
    echo "1. Create beads issue for your feature"
    echo "2. Set it as current task"
    echo "3. Reference issue in commits"
    echo "4. Re-run validation when complete"
    echo ""
    echo "This work session is BLOCKED until beads compliance is achieved."
    
    if [[ "$STRICT_MODE" == "true" ]]; then
        log_validation "ERROR" "EXITING due to beads violation - STRICT MODE ENABLED"
        exit 1
    fi
}

# Main validation function
main() {
    echo ""
    echo "🔗 BEADS MANDATORY GATE VALIDATION"
    echo "=================================="
    echo "Timestamp: $(date)"
    echo "Strict Mode: $STRICT_MODE"
    echo ""
    
    # Check beads availability
    if ! check_beads_availability; then
        block_without_beads "Beads command not available"
        return 1
    fi
    
    # Check beads repository
    if ! check_beads_repository; then
        block_without_beads "Not a beads-enabled repository"
        return 1
    fi
    
    # Detect feature context
    local feature_context=$(detect_feature_context)
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Feature Context:"
        echo "$feature_context" | jq .
        echo ""
    fi
    
    # Validate beads issue
    if ! validate_beads_issue "$feature_context"; then
        local has_changes=$(echo "$feature_context" | jq -r '.has_any_changes // false')
        if [[ "$has_changes" == "true" ]]; then
            suggest_beads_creation "$feature_context"
            block_without_beads "No beads issue found for feature work"
            return 1
        fi
    fi
    
    echo ""
    echo "=================================="
    log_validation "SUCCESS" "Beads compliance validation PASSED"
    echo "✅ Beads compliance validated - work may proceed"
    return 0
}

# Help function
show_help() {
    echo ""
    echo "$SCRIPT_NAME v$VERSION"
    echo "==========================="
    echo ""
    echo "USAGE:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --verbose           Show detailed feature context analysis"
    echo "  --strict            Enable strict mode (default: true)"
    echo "  --permissive         Enable permissive mode (DANGEROUS)"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "BEADS REQUIREMENTS (Mandatory):"
    echo "  ✓ Beads command available"
    echo "  ✓ Beads repository initialized"
    echo "  ✓ Beads issue exists for feature work"
    echo "  ✓ Current task set when working on features"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  VERBOSE             Enable verbose output (true|false)"
    echo "  STRICT_MODE         Enable strict enforcement (true|false)"
    echo "  FEATURE_NAME        Feature name being developed"
    echo ""
    echo "EXIT CODES:"
    echo "  0    Success"
    echo "  1    Beads Violation or Validation Error"
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --verbose)
        export VERBOSE=true
        ;;
    --strict)
        export STRICT_MODE=true
        ;;
    --permissive)
        export STRICT_MODE=false
        ;;
esac

# Run main validation
main "$@"