#!/bin/bash

# Multi-Phase Implementation Hand-off Compliance Verification Script
# Validates hand-off documents meet all SOP requirements

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HANDOFF_DIR="${HANDOFF_DIR:-.agent/handoffs}"
FEATURE_NAME=""
PHASE_ID=""
INTERACTIVE=false
REPORT=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage
usage() {
    cat << EOF
Multi-Phase Implementation Hand-off Compliance Verification

Usage: $0 [OPTIONS] --phase <phase-id> | --feature <feature-name>

REQUIRED:
  --phase <phase-id>     Verify specific phase hand-off (e.g., phase-01)
  --feature <feature>    Verify all hand-offs for feature

OPTIONS:
  --interactive          Interactive review with detailed feedback
  --report              Generate compliance report
  --verbose             Verbose output
  --handoff-dir <dir>   Hand-off directory (default: .agent/handoffs)
  --help                Show this help

EXAMPLES:
  $0 --phase phase-01 --feature feature-name
  $0 --feature citation-generation --report
  $0 --phase phase-02 --interactive

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --phase)
            PHASE_ID="$2"
            shift 2
            ;;
        --feature)
            FEATURE_NAME="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --report)
            REPORT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --handoff-dir)
            HANDOFF_DIR="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validation
if [[ -z "$PHASE_ID" && -z "$FEATURE_NAME" ]]; then
    log_error "Either --phase or --feature must be specified"
    usage
    exit 1
fi

if [[ -n "$PHASE_ID" && -z "$FEATURE_NAME" ]]; then
    log_error "When using --phase, --feature must also be specified"
    usage
    exit 1
fi

# Global variables for tracking compliance
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Increment counters
increment_passed() {
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

increment_failed() {
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

increment_warning() {
    ((WARNINGS++))
}

# Check if file exists and is readable
check_file_exists() {
    local file="$1"
    local description="$2"

    if [[ -f "$file" && -r "$file" ]]; then
        log_success "$description: $file"
        increment_passed
        return 0
    else
        log_error "$description: $file (not found or unreadable)"
        increment_failed
        return 1
    fi
}

# Check if markdown section exists
check_section_exists() {
    local file="$1"
    local section_pattern="$2"
    local description="$3"

    if grep -q "^#* $section_pattern" "$file"; then
        log_success "$description section found"
        increment_passed
        return 0
    else
        log_error "$description section missing"
        increment_failed
        return 1
    fi
}

# Check if section meets minimum word count
check_section_length() {
    local file="$1"
    local section_pattern="$2"
    local min_words="$3"
    local description="$4"

    local content
    content=$(sed -n "/^#* $section_pattern/,/^#/p" "$file" | sed '$d' | wc -w)

    if [[ $content -ge $min_words ]]; then
        log_success "$description meets minimum length ($content words)"
        increment_passed
        return 0
    else
        log_error "$description too short ($content words, minimum $min_words)"
        increment_failed
        return 1
    fi
}

# Check for required subsections
check_subsections() {
    local file="$1"
    local section_pattern="$2"
    local subsections="$3"
    local description="$4"

    local missing_subsections=()
    while IFS= read -r subsection; do
        if ! grep -q "^##* $subsection" "$file"; then
            missing_subsections+=("$subsection")
        fi
    done <<< "$subsections"

    if [[ ${#missing_subsections[@]} -eq 0 ]]; then
        log_success "$description contains all required subsections"
        increment_passed
        return 0
    else
        log_error "$description missing subsections: ${missing_subsections[*]}"
        increment_failed
        return 1
    fi
}

# Check markdown link validity
check_links_valid() {
    local file="$1"
    local description="$2"

    local broken_links=()
    while IFS= read -r line; do
        # Simple markdown link detection
        if echo "$line" | grep -q '\[.*\]([^)]*)'; then
            local link
            link=$(echo "$line" | sed 's/.*\[[^]]*\]([^)]*).*/\1/')
            # Skip external URLs and anchors
            if [[ ! $link =~ ^https?:// ]] && [[ ! $link =~ ^# ]]; then
                local link_path
                link_path=$(dirname "$file")/$link
                if [[ ! -f "$link_path" ]]; then
                    broken_links+=("$link")
                fi
            fi
        fi
    done < "$file"

    if [[ ${#broken_links[@]} -eq 0 ]]; then
        log_success "$description: All links valid"
        increment_passed
        return 0
    else
        log_warning "$description: Broken links: ${broken_links[*]}"
        increment_warning
        return 1
    fi
}

# Check code block formatting
check_code_blocks() {
    local file="$1"
    local description="$2"

    local unformatted_blocks
    unformatted_blocks=$(grep -n '```' "$file" | wc -l)

    # Each code block should have opening and closing ```
    if [[ $((unformatted_blocks % 2)) -eq 0 ]]; then
        log_success "$description: Code blocks properly formatted"
        increment_passed
        return 0
    else
        log_error "$description: Unclosed code blocks detected"
        increment_failed
        return 1
    fi
}

# Comprehensive hand-off verification
verify_handoff_document() {
    local handoff_file="$1"
    local phase_id="$2"
    local feature_name="$3"

    log_info "Verifying hand-off document: $handoff_file"

    # Check file exists and readable
    check_file_exists "$handoff_file" "Hand-off document"

    # Check required sections
    check_section_exists "$handoff_file" "Executive Summary" "Executive Summary"
    check_section_exists "$handoff_file" "Technical Context" "Technical Context"
    check_section_exists "$handoff_file" "Knowledge Transfer" "Knowledge Transfer"
    check_section_exists "$handoff_file" "Navigation & Onboarding" "Navigation & Onboarding"
    check_section_exists "$handoff_file" "Quality & Validation" "Quality & Validation"

    # Check section lengths
    check_section_length "$handoff_file" "Executive Summary" 300 "Executive Summary"

    # Check required subsections
    local technical_subsections="Architecture Changes
Code Modifications
Configuration Updates
API Changes
Database Changes"
    check_subsections "$handoff_file" "Technical Context" "$technical_subsections" "Technical Context"

    local knowledge_subsections="Implementation Patterns
Technical Debt
Testing Strategy
Performance Considerations
Security Implications"
    check_subsections "$handoff_file" "Knowledge Transfer" "$knowledge_subsections" "Knowledge Transfer"

    local navigation_subsections="Entry Points
Critical Files
Dependencies
Environment Setup
Debug Information"
    check_subsections "$handoff_file" "Navigation & Onboarding" "$navigation_subsections" "Navigation & Onboarding"

    # Check formatting
    check_links_valid "$handoff_file" "Hand-off document"
    check_code_blocks "$handoff_file" "Hand-off document"

    # Check for feature context
    if grep -q "$feature_name" "$handoff_file"; then
        log_success "Feature name referenced in document"
        increment_passed
    else
        log_warning "Feature name not found in document"
        increment_warning
    fi

    # Check for phase context
    if grep -q "$phase_id" "$handoff_file"; then
        log_success "Phase ID referenced in document"
        increment_passed
    else
        log_warning "Phase ID not found in document"
        increment_warning
    fi
}

# Generate compliance report
generate_report() {
    local feature_name="$1"
    local report_file="${HANDOFF_DIR}/${feature_name}/compliance_report.md"

    mkdir -p "$(dirname "$report_file")"

    cat > "$report_file" << EOF
# Hand-off Compliance Report

**Feature**: $feature_name
**Generated**: $(date)
**Total Checks**: $TOTAL_CHECKS
**Passed**: $PASSED_CHECKS
**Failed**: $FAILED_CHECKS
**Warnings**: $WARNINGS

## Compliance Score

$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))% compliant

## Status

EOF

    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo "✅ PASSES ALL REQUIREMENTS" >> "$report_file"
    else
        echo "❌ REQUIRES ATTENTION" >> "$report_file"
        echo "" >> "$report_file"
        echo "## Issues Requiring Resolution" >> "$report_file"
        echo "" >> "$report_file"
        echo "Please review the verification output above and fix all failed checks." >> "$report_file"
    fi

    log_success "Compliance report generated: $report_file"
}

# Interactive review
interactive_review() {
    local handoff_file="$1"

    echo ""
    log_info "=== INTERACTIVE REVIEW ==="
    echo ""

    echo "Would you like to view the hand-off document? (y/n)"
    read -r response
    if [[ $response =~ ^[Yy]$ ]]; then
        if command -v less >/dev/null 2>&1; then
            less "$handoff_file"
        else
            more "$handoff_file"
        fi
    fi

    echo ""
    echo "Do you approve this hand-off document? (y/n)"
    read -r approval
    if [[ $approval =~ ^[Yy]$ ]]; then
        log_success "Hand-off document approved interactively"
        return 0
    else
        log_error "Hand-off document rejected interactively"
        return 1
    fi
}

# Main verification function
verify_handoff() {
    local feature_dir="${HANDOFF_DIR}/${FEATURE_NAME}"

    if [[ ! -d "$feature_dir" ]]; then
        log_error "Feature hand-off directory not found: $feature_dir"
        return 1
    fi

    if [[ -n "$PHASE_ID" ]]; then
        local handoff_file="${feature_dir}/${PHASE_ID}-handoff.md"
        verify_handoff_document "$handoff_file" "$PHASE_ID" "$FEATURE_NAME"
    else
        # Verify all hand-offs for feature
        for handoff_file in "${feature_dir}"/phase-*-handoff.md; do
            if [[ -f "$handoff_file" ]]; then
                local phase_id
                phase_id=$(basename "$handoff_file" | sed 's/-handoff.md//')
                verify_handoff_document "$handoff_file" "$phase_id" "$FEATURE_NAME"
            fi
        done
    fi
}

# Main execution
main() {
    log_info "Starting hand-off compliance verification"

    if [[ "$VERBOSE" == true ]]; then
        log_info "Configuration:"
        log_info "  Hand-off directory: $HANDOFF_DIR"
        log_info "  Feature name: $FEATURE_NAME"
        log_info "  Phase ID: $PHASE_ID"
        log_info "  Interactive mode: $INTERACTIVE"
        log_info "  Report mode: $REPORT"
    fi

    # Run verification
    verify_handoff

    # Output summary
    echo ""
    log_info "=== VERIFICATION SUMMARY ==="
    echo "Total checks: $TOTAL_CHECKS"
    echo "Passed: $PASSED_CHECKS"
    echo "Failed: $FAILED_CHECKS"
    echo "Warnings: $WARNINGS"

    local compliance_score=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        compliance_score=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    fi
    echo "Compliance: ${compliance_score}%"

    # Interactive review
    if [[ "$INTERACTIVE" == true && -n "$PHASE_ID" ]]; then
        local handoff_file="${HANDOFF_DIR}/${FEATURE_NAME}/${PHASE_ID}-handoff.md"
        if [[ -f "$handoff_file" ]]; then
            interactive_review "$handoff_file"
        fi
    fi

    # Generate report
    if [[ "$REPORT" == true ]]; then
        generate_report "$FEATURE_NAME"
    fi

    # Final status
    echo ""
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "✅ Hand-off compliance verification PASSED"
        exit 0
    else
        log_error "❌ Hand-off compliance verification FAILED"
        log_error "Please fix all failed checks before proceeding"
        exit 1
    fi
}

# Run main function
main "$@"
