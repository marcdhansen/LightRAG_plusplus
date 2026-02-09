#!/bin/bash

# Multi-Phase Hand-off Compliance Integration Bridge
# Connects all existing components into cohesive enforcement loop
# Prevents SOP bypass incidents like CI_CD_P0_RESOLUTION_PLAYBOOK.md

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HANDOFF_DIR="${HANDOFF_DIR:-.agent/handoffs}"
INTEGRATION_LOG=".agent/logs/integration_bridge.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CRITICAL='\033[0;91m'  # Bright red for critical issues
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INTEGRATION]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" >> "$INTEGRATION_LOG"
}

log_success() {
    echo -e "${GREEN}[INTEGRATION]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$INTEGRATION_LOG"
}

log_warning() {
    echo -e "${YELLOW}[INTEGRATION]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" >> "$INTEGRATION_LOG"
}

log_error() {
    echo -e "${RED}[INTEGRATION]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$INTEGRATION_LOG"
}

log_critical() {
    echo -e "${CRITICAL}[CRITICAL]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRITICAL] $1" >> "$INTEGRATION_LOG"
}

# Usage
usage() {
    cat << EOF
Multi-Phase Hand-off Compliance Integration Bridge

Usage: $0 [OPTIONS]

OPTIONS:
  --verify              Run complete verification workflow
  --detect-only         Run multi-phase detection only
  --handoff-only        Run hand-off verification only
  --bypass-check        Run bypass incident check only
  --enforce             Run enforcement mode (blocks on violations)
  --report              Generate detailed compliance report
  --help                Show this help

EXAMPLES:
  $0 --verify           # Complete verification workflow
  $0 --enforce          # Enforcement mode for RTB
  $0 --bypass-check     # Check for bypass incident patterns

EOF
}

# Initialize log directory
mkdir -p "$(dirname "$INTEGRATION_LOG")"

# Function to run multi-phase detection
run_multi_phase_detection() {
    log_info "Running enhanced multi-phase detection..."
    
    local detector_script=".agent/scripts/multi_phase_detector.py"
    if [ ! -f "$detector_script" ]; then
        log_error "Enhanced multi-phase detector not found: $detector_script"
        echo "0"
        return 1
    fi
    
    # Run enhanced detector and capture output
    local detection_result
    detection_result=$(python3 "$detector_script" 2>/dev/null)
    local detector_exit_code=$?
    
    # Parse enhanced detection results
    local weighted_score=0
    local risk_level="UNKNOWN"
    local bypass_detected=false
    
    if [ $detector_exit_code -eq 1 ]; then
        # Extract weighted score and risk level
        if [[ "$detection_result" == *"Weighted Score:"* ]]; then
            weighted_score=$(echo "$detection_result" | grep "Weighted Score:" | awk '{print $3}')
        fi
        if [[ "$detection_result" == *"Risk Level:"* ]]; then
            risk_level=$(echo "$detection_result" | grep "Risk Level:" | awk '{print $3}')
        fi
        if [[ "$detection_result" == *"Bypass Incident Detected: True"* ]]; then
            bypass_detected=true
        fi
        
        log_critical "🚨 ENHANCED MULTI-PHASE DETECTION TRIGGERED"
        log_info "   Weighted Score: $weighted_score"
        log_info "   Risk Level: $risk_level"
        
        if [ "$bypass_detected" = true ]; then
            log_critical "🚨 BYPASS INCIDENT PATTERNS DETECTED - IMMEDIATE BLOCK REQUIRED"
            echo "bypass_incident"
            return 1
        fi
        
        echo "multi_phase"
        return 1
    else
        log_success "✅ No multi-phase patterns detected"
        echo "clear"
        return 0
    fi
}

# Function to run SOP bypass enforcement
run_sop_bypass_enforcement() {
    log_info "Running SOP bypass enforcement..."
    
    local enforcement_script=".agent/scripts/sop_bypass_enforcement.py"
    if [ ! -f "$enforcement_script" ]; then
        log_error "SOP bypass enforcement script not found: $enforcement_script"
        echo "0"
        return 1
    fi
    
    # Run enforcement and capture output
    local enforcement_result
    enforcement_result=$(python3 "$enforcement_script" 2>/dev/null)
    local enforcement_exit_code=$?
    
    # Parse enforcement results
    local bypass_attempts=0
    local violations_count=0
    local risk_level="UNKNOWN"
    local enforcement_action="UNKNOWN"
    
    if [ $enforcement_exit_code -eq 1 ] || [ $enforcement_exit_code -eq 2 ]; then
        # Extract key metrics - clean up ANSI codes first
        local clean_result=$(echo "$enforcement_result" | sed 's/\x1b\[[0-9;]*m//g')
        
        if [[ "$clean_result" == *"Bypass Attempts:"* ]]; then
            bypass_attempts=$(echo "$clean_result" | grep "Bypass Attempts:" | awk '{print $3}')
        fi
        if [[ "$clean_result" == *"Violations Count:"* ]]; then
            violations_count=$(echo "$clean_result" | grep "Violations Count:" | awk '{print $3}')
        fi
        if [[ "$clean_result" == *"Risk Level:"* ]]; then
            risk_level=$(echo "$clean_result" | grep "Risk Level:" | awk '{print $3}')
        fi
        if [[ "$clean_result" == *"Enforcement Action:"* ]]; then
            enforcement_action=$(echo "$clean_result" | grep "Enforcement Action:" | awk '{print $3}')
        fi
        
        log_critical "🚨 SOP BYPASS VIOLATIONS DETECTED"
        log_info "   Bypass Attempts: $bypass_attempts"
        log_info "   Violations Count: $violations_count"
        log_info "   Risk Level: $risk_level"
        log_info "   Enforcement Action: $enforcement_action"
        
        # Return violation count and enforcement action for processing
        echo "${violations_count}:${enforcement_action}"
        return 1
    else
        log_success "✅ No SOP bypass violations detected"
        echo "0:ALLOW"
        return 0
    fi
}

# Function to run hand-off verification
run_handoff_verification() {
    log_info "Running hand-off verification..."
    
    local handoff_script=".agent/scripts/verify_handoff_compliance.sh"
    if [ ! -f "$handoff_script" ]; then
        log_error "Hand-off verification script not found: $handoff_script"
        echo "0"
        return 1
    fi
    
    # Check if hand-off directory exists and has content
    if [ ! -d "$HANDOFF_DIR" ] || [ -z "$(ls -A "$HANDOFF_DIR" 2>/dev/null)" ]; then
        log_warning "No hand-off documents found - verification skipped"
        echo "0"
        return 0
    fi
    
    # Try to auto-detect feature for verification
    local feature_name=""
    local phase_name=""
    
    # Look for hand-off documents
    for handoff_file in "$HANDOFF_DIR"/*.md "$HANDOFF_DIR"/*/*.md; do
        if [ -f "$handoff_file" ]; then
            local filename=$(basename "$handoff_file" .md)
            if [[ "$filename" =~ phase-([0-9]+)-handoff ]]; then
                phase_name="phase-${BASH_REMATCH[1]}"
                # Extract feature name from directory
                feature_name=$(basename "$(dirname "$handoff_file")")
                break
            fi
        fi
    done
    
    # Run verification with detected parameters
    local verification_result=""
    local verification_issues=0
    
    if [ -n "$phase_name" ] && [ -n "$feature_name" ]; then
        log_info "Verifying hand-off: feature=$feature_name, phase=$phase_name"
        verification_result=$("$handoff_script" --phase "$phase_name" --feature "$feature_name" 2>/dev/null) || {
            verification_issues=$?
            log_error "Hand-off verification failed with exit code: $verification_issues"
        }
        
# Count compliance issues
        verification_issues=$(echo "$verification_result" | grep -c "FAILED\|ERROR" 2>/dev/null || echo "0")
    fi
    
    # Clean up verification_issues to remove newlines
    verification_issues=$(echo "$verification_issues" | tr -d '\n' | tr -d ' ')
    
    if [ "$verification_issues" -gt 0 ]; then
        log_error "❌ Hand-off compliance issues found: $verification_issues"
        echo "$verification_issues"
        return 1
    else
        log_success "✅ Hand-off compliance verified"
        echo "0"
        return 0
    fi
}

# Function to check for bypass incident patterns
run_bypass_incident_check() {
    log_info "Running bypass incident check..."
    
    # Check for the specific playbook file
    if [ -f "CI_CD_P0_RESOLUTION_PLAYBOOK.md" ]; then
        log_critical "🚨 BYPASS INCIDENT PLAYBOOK FOUND"
        
        # Check for specific bypass evidence
        local bypass_evidence=0
        
        if grep -q "Hybrid Approach" "CI_CD_P0_RESOLUTION_PLAYBOOK.md"; then
            log_critical "   Evidence: Hybrid Approach documented"
            bypass_evidence=$((bypass_evidence + 1))
        fi
        
        if grep -q "PR groups" "CI_CD_P0_RESOLUTION_PLAYBOOK.md"; then
            log_critical "   Evidence: PR groups documented"
            bypass_evidence=$((bypass_evidence + 1))
        fi
        
        if grep -q "3 PR groups" "CI_CD_P0_RESOLUTION_PLAYBOOK.md"; then
            log_critical "   Evidence: 3 PR groups documented"
            bypass_evidence=$((bypass_evidence + 1))
        fi
        
        if [ $bypass_evidence -ge 2 ]; then
            log_critical "🚨 BYPASS INCIDENT CONFIRMED - This is the exact incident that caused the P0"
            return 1
        fi
    fi
    
    log_success "✅ No bypass incident patterns found"
    return 0
}

# Function to generate compliance report
generate_compliance_report() {
    log_info "Generating compliance report..."
    
    local report_file=".agent/logs/compliance_report_$(date +%s).md"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
# Multi-Phase Hand-off Compliance Report

**Generated**: $(date)
**System**: LightRAG Integration Bridge

## Executive Summary

This report provides a comprehensive analysis of multi-phase implementation compliance and hand-off verification status.

## Detection Results

EOF

    # Run detection and capture results
    local detection_status=$(run_multi_phase_detection)
    local handoff_issues=$(run_handoff_verification)
    local bypass_status=$(run_bypass_incident_check && echo "clear" || echo "detected")
    
    cat >> "$report_file" << EOF
- **Multi-Phase Detection**: $detection_status
- **Hand-off Compliance**: $handoff_issues issues found
- **Bypass Incident Check**: $bypass_status

## Risk Assessment

EOF

    if [ "$detection_status" = "bypass_incident" ] || [ "$bypass_status" = "detected" ]; then
        cat >> "$report_file" << EOF
🚨 **CRITICAL RISK**: Bypass incident patterns detected. Immediate action required.

### Required Actions
1. STOP all work immediately
2. Create mandatory hand-off documents
3. Follow proper multi-phase protocol
4. Re-run compliance verification

EOF
    elif [ "$detection_status" = "multi_phase" ] && [ "$handoff_issues" -gt 0 ]; then
        cat >> "$report_file" << EOF
⚠️ **HIGH RISK**: Multi-phase work without proper hand-off compliance.

### Required Actions
1. Fix $handoff_issues hand-off compliance issues
2. Ensure all required sections are complete
3. Verify document quality and accuracy

EOF
    else
        cat >> "$report_file" << EOF
✅ **LOW RISK**: No critical compliance issues detected.

### Status
- Multi-phase detection: Clear
- Hand-off compliance: Verified
- Bypass incident risk: None detected

EOF
    fi
    
    cat >> "$report_file" << EOF
## Recommendations

1. **Prevention**: Always create hand-off documents for multi-phase work
2. **Detection**: Run this integration bridge before RTB completion
3. **Compliance**: Follow Multi-Phase Hand-off Protocol strictly
4. **Monitoring**: Regular checks for bypass incident patterns

## Technical Details

- **Integration Bridge Version**: 1.0.0
- **Detection Engine**: multi_phase_detector.py
- **Verification Engine**: verify_handoff_compliance.sh
- **Log Location**: $INTEGRATION_LOG

---

*This report was generated automatically by the LightRAG Integration Bridge system.*
EOF

    log_success "Compliance report generated: $report_file"
    echo "$report_file"
}

# Function to run complete verification workflow
run_complete_verification() {
    log_info "Running enhanced complete verification workflow..."
    
    local detection_status=$(run_multi_phase_detection)
    local sop_enforcement_result=$(run_sop_bypass_enforcement)
    local sop_violations=$(echo "$sop_enforcement_result" | cut -d: -f1)
    local enforcement_action=$(echo "$sop_enforcement_result" | cut -d: -f2)
    local handoff_issues=$(run_handoff_verification)
    local bypass_status=$(run_bypass_incident_check && echo "clear" || echo "detected")
    
    echo ""
    log_info "=== ENHANCED VERIFICATION SUMMARY ==="
    echo "Multi-Phase Detection: $detection_status"
    echo "SOP Bypass Violations: $sop_violations"
    echo "Hand-off Compliance: $handoff_issues issues"
    echo "Bypass Incident Check: $bypass_status"
    echo ""
    
    # Determine final status
    local final_status="PASS"
    local block_reason=""
    
    if [ "$detection_status" = "bypass_incident" ] || [ "$bypass_status" = "detected" ] || [ "$sop_violations" -gt 0 ] || [ "$enforcement_action" = "BLOCK" ]; then
        final_status="CRITICAL_BLOCK"
        block_reason="Critical security violations detected - SYSTEM LOCKED"
    elif [ "$detection_status" = "multi_phase" ] && [ "$handoff_issues" -gt 0 ]; then
        final_status="BLOCK"
        block_reason="Multi-phase work without proper hand-off compliance"
    elif [ "$detection_status" = "multi_phase" ] && [ ! -d "$HANDOFF_DIR" ]; then
        final_status="BLOCK"
        block_reason="Multi-phase work detected but no hand-off directory exists"
    fi
    
    echo "Final Status: $final_status"
    
    if [ "$final_status" != "PASS" ]; then
        echo ""
        log_critical "🚫 ENHANCED SECURITY BLOCKER: $block_reason"
        echo ""
        echo "🔧 MANDATORY SECURITY ACTIONS REQUIRED:"
        
        if [ "$final_status" = "CRITICAL_BLOCK" ]; then
            echo "   1. 🚨 CRITICAL: Security system has detected violations"
            echo "   2. IMMEDIATE STOP of all work activities"
            echo "   3. Address ALL security violations found above"
            echo "   4. Create comprehensive hand-off documents if needed"
            echo "   5. Follow all security protocols strictly"
            echo "   6. Re-run enhanced verification after fixes"
            echo ""
            echo "   🔒 SYSTEM LOCKED - Work cannot proceed until security compliance"
        else
            echo "   1. Create hand-off documents for multi-phase work"
            echo "   2. Use template: .agent/docs/sop/MULTI_PHASE_HANDOFF_PROTOCOL.md"
            echo "   3. Store in: .agent/handoffs/<feature>/phase-XX-handoff.md"
            echo "   4. Verify compliance: .agent/scripts/verify_handoff_compliance.sh"
            echo "   5. Run security validation: .agent/scripts/sop_bypass_enforcement.py"
        fi
        
        echo ""
        echo "❌ ENHANCED VERIFICATION BLOCKED - Fix security issues before proceeding"
        return 1
    else
        log_success "✅ ENHANCED VERIFICATION PASSED - All security requirements met"
        return 0
    fi
}

# Main execution
main() {
    local mode="verify"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verify)
                mode="verify"
                shift
                ;;
            --detect-only)
                mode="detect"
                shift
                ;;
            --handoff-only)
                mode="handoff"
                shift
                ;;
            --bypass-check)
                mode="bypass"
                shift
                ;;
            --enforce)
                mode="enforce"
                shift
                ;;
            --report)
                mode="report"
                shift
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
    
    log_info "Starting Multi-Phase Hand-off Compliance Integration Bridge"
    log_info "Mode: $mode"
    
    case $mode in
        verify)
            run_complete_verification
            ;;
        detect)
            run_multi_phase_detection
            ;;
        handoff)
            run_handoff_verification
            ;;
        bypass)
            run_bypass_incident_check
            ;;
        enforce)
            run_complete_verification
            exit $?
            ;;
        report)
            generate_compliance_report
            ;;
        *)
            log_error "Invalid mode: $mode"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"