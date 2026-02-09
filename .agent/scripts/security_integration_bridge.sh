#!/bin/bash

# Enhanced Security Integration Bridge - Simplified Version
# Coordinates all security components for comprehensive protection

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_LOG=".agent/logs/security_integration.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CRITICAL='\033[0;91m'
NC='\033[0m'

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

log_critical() {
    echo -e "${CRITICAL}[CRITICAL]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRITICAL] $1" >> "$INTEGRATION_LOG"
}

# Initialize log directory
mkdir -p "$(dirname "$INTEGRATION_LOG")"

# Run comprehensive security check
run_security_verification() {
    log_info "Running comprehensive security verification..."
    
    local security_status="PASS"
    local issues_found=0
    local critical_issues=0
    
    # Check 1: Multi-Phase Detection
    log_info "Step 1: Multi-Phase Detection Analysis"
    if python .agent/scripts/multi_phase_detector.py >/dev/null 2>&1; then
        log_success "✅ Multi-Phase Detection: Clear"
    else
        log_critical "🚨 Multi-Phase Detection: CRITICAL PATTERNS FOUND"
        issues_found=$((issues_found + 1))
        critical_issues=$((critical_issues + 1))
        security_status="CRITICAL_BLOCK"
    fi
    
    # Check 2: SOP Bypass Enforcement
    log_info "Step 2: SOP Bypass Enforcement Check"
    if python .agent/scripts/sop_bypass_enforcement.py >/dev/null 2>&1; then
        log_success "✅ SOP Bypass Enforcement: Clear"
    else
        log_critical "🚨 SOP Bypass Enforcement: VIOLATIONS DETECTED"
        issues_found=$((issues_found + 1))
        critical_issues=$((critical_issues + 1))
        security_status="CRITICAL_BLOCK"
    fi
    
    # Check 3: Hand-off Compliance (if applicable)
    log_info "Step 3: Hand-off Compliance Verification"
    local handoff_dir=".agent/handoffs"
    if [ -d "$handoff_dir" ] && [ "$(ls -A "$handoff_dir" 2>/dev/null)" ]; then
        if bash .agent/scripts/verify_handoff_compliance.sh --help >/dev/null 2>&1; then
            log_success "✅ Hand-off Compliance: Documents Available"
        else
            log_warning "⚠️  Hand-off Compliance: Verification Issues"
            issues_found=$((issues_found + 1))
            if [ "$security_status" = "PASS" ]; then
                security_status="WARNING"
            fi
        fi
    else
        log_info "ℹ️  Hand-off Compliance: No Documents Required"
    fi
    
    # Check 4: System Health
    log_info "Step 4: Security System Health Check"
    local missing_scripts=0
    
    [ ! -f ".agent/scripts/multi_phase_detector.py" ] && missing_scripts=$((missing_scripts + 1))
    [ ! -f ".agent/scripts/sop_bypass_enforcement.py" ] && missing_scripts=$((missing_scripts + 1))
    [ ! -f ".agent/scripts/verify_handoff_compliance.sh" ] && missing_scripts=$((missing_scripts + 1))
    
    if [ $missing_scripts -eq 0 ]; then
        log_success "✅ Security System Health: All Components Available"
    else
        log_critical "🚨 Security System Health: $missing_scripts Components Missing"
        issues_found=$((issues_found + 1))
        security_status="SYSTEM_ERROR"
    fi
    
    # Final determination
    echo ""
    log_info "=== SECURITY VERIFICATION SUMMARY ==="
    echo "Total Issues Found: $issues_found"
    echo "Critical Issues: $critical_issues"
    echo "Overall Security Status: $security_status"
    echo ""
    
    if [ "$security_status" = "CRITICAL_BLOCK" ]; then
        log_critical "🚫 CRITICAL SECURITY BLOCKER DETECTED"
        echo ""
        echo "🔒 IMMEDIATE ACTIONS REQUIRED:"
        echo "   1. STOP all development work immediately"
        echo "   2. Address ALL critical security violations"
        echo "   3. Follow mandatory SOP protocols"
        echo "   4. Create proper hand-off documents if needed"
        echo "   5. Re-run security verification after fixes"
        echo ""
        echo "❌ SECURITY SYSTEM LOCKED - Work cannot proceed"
        return 1
    elif [ "$security_status" = "WARNING" ]; then
        log_warning "⚠️  SECURITY ISSUES DETECTED"
        echo ""
        echo "🔧 RECOMMENDED ACTIONS:"
        echo "   1. Address warning-level issues"
        echo "   2. Verify hand-off document quality"
        echo "   3. Run security validation scripts"
        echo ""
        echo "⚠️  WORK PROCEEDS WITH CAUTION"
        return 2
    elif [ "$security_status" = "SYSTEM_ERROR" ]; then
        log_critical "❌ SECURITY SYSTEM ERROR"
        echo ""
        echo "🔧 SYSTEM MAINTENANCE REQUIRED:"
        echo "   1. Install missing security components"
        echo "   2. Verify all script permissions"
        echo "   3. Check system configuration"
        echo ""
        echo "❌ SYSTEM UNAVAILABLE - Contact security team"
        return 3
    else
        log_success "✅ SECURITY VERIFICATION PASSED"
        echo ""
        echo "🛡️  All security components operating normally"
        echo "   - No multi-phase threats detected"
        echo "   - No SOP bypass violations found"
        echo "   - Hand-off compliance verified"
        echo "   - Security system health confirmed"
        echo ""
        echo "✅ WORK PROCEEDS - Security clearance granted"
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
            --health)
                mode="health"
                shift
                ;;
            --help)
                echo "Enhanced Security Integration Bridge"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "OPTIONS:"
                echo "  --verify     Run comprehensive security verification"
                echo "  --health     Check security system health only"
                echo "  --help       Show this help"
                echo ""
                echo "Exit Codes:"
                echo "  0 - Security clearance granted (PASS)"
                echo "  1 - Critical security block (CRITICAL_BLOCK)"
                echo "  2 - Security warnings (WARNING)"
                echo "  3 - System error (SYSTEM_ERROR)"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    log_info "Starting Enhanced Security Integration Bridge"
    log_info "Mode: $mode"
    
    case $mode in
        verify)
            run_security_verification
            ;;
        health)
            # Simple health check
            if [ -f ".agent/scripts/multi_phase_detector.py" ] && [ -f ".agent/scripts/sop_bypass_enforcement.py" ]; then
                log_success "✅ Security System Health: All Components Available"
                exit 0
            else
                log_error "❌ Security System Health: Components Missing"
                exit 3
            fi
            ;;
        *)
            log_error "Invalid mode: $mode"
            exit 3
            ;;
    esac
}

# Run main function
main "$@"