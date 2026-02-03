#!/bin/bash
# SOP Evaluation Script - mandatory for RTB process
# Evaluates effectiveness of Standard Operating Procedures

echo "📊 SOP Effectiveness Evaluation"
echo "================================"

# Configuration
LOG_DIR=".agent/logs"
EVALUATION_FILE="$LOG_DIR/sop_evaluation.json"
FAIL_THRESHOLD=${FAIL_THRESHOLD:-15}  # >15% failure rate triggers BLOCKER
COMPLIANCE_MINIMUM=${COMPLIANCE_MINIMUM:-85}  # <85% compliance triggers BLOCKER

# Create log directory
mkdir -p "$LOG_DIR"

# Initialize evaluation results
cat > "$EVALUATION_FILE" << EOF
{
  "evaluation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "session_id": "$(date +%s)",
  "metrics": {},
  "friction_points": [],
  "recommendations": [],
  "status": "in_progress"
}
EOF

# Function to calculate PFC compliance
calculate_pfc_compliance() {
    echo "   🔍 Analyzing PFC compliance..."
    
    local pfc_issues=0
    local pfc_checks=0
    
    # Check for common PFC failures
    if [ ! -f ".agent/rules/ROADMAP.md" ]; then
        echo "     ❌ Missing ROADMAP.md"
        pfc_issues=$((pfc_issues + 1))
    fi
    pfc_checks=$((pfc_checks + 1))
    
    if [ ! -f ".agent/rules/ImplementationPlan.md" ]; then
        echo "     ❌ Missing ImplementationPlan.md"
        pfc_issues=$((pfc_issues + 1))
    fi
    pfc_checks=$((pfc_checks + 1))
    
    # Check bd ready status
    if ! bd ready >/dev/null 2>&1; then
        echo "     ❌ Beads not ready"
        pfc_issues=$((pfc_issues + 1))
    fi
    pfc_checks=$((pfc_checks + 1))
    
    local compliance_rate=$((100 - (pfc_issues * 100 / pfc_checks)))
    
    if [ $compliance_rate -lt $COMPLIANCE_MINIMUM ]; then
        echo "     ❌ PFC compliance: ${compliance_rate}% (below ${COMPLIANCE_MINIMUM}%)"
    else
        echo "     ✅ PFC compliance: ${compliance_rate}%"
    fi
    
    # Return the numeric value (not captured by echo)
    echo $compliance_rate
}

# Function to analyze process friction
analyze_process_friction() {
    echo "   🔍 Analyzing process friction..."
    
    local friction_count=0
    
    # Check for session lock issues
    local stale_locks=$(find .agent/session_locks -name "*.json" -mmin +10 2>/dev/null | wc -l)
    if [ $stale_locks -gt 0 ]; then
        echo "     ⚠️  Found $stale_locks stale session locks"
        jq --arg msg "Found $stale_locks stale session locks" '.friction_points += [{"type": "session_locks", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        friction_count=$((friction_count + 1))
    fi
    
    # Check for broken symlinks
    local broken_links=$(find .agent -type l -exec test ! -e {} \; -print | wc -l)
    if [ $broken_links -gt 0 ]; then
        echo "     ⚠️  Found $broken_links broken symbolic links"
        jq --arg msg "Found $broken_links broken symbolic links" '.friction_points += [{"type": "documentation", "description": $msg, "severity": "high"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        friction_count=$((friction_count + 1))
    fi
    
    # Check git issues
    local git_issues=$(git status --porcelain 2>/dev/null | wc -l)
    if [ $git_issues -gt 10 ]; then
        echo "     ⚠️  High number of git changes: $git_issues"
        jq --arg msg "High number of git changes: $git_issues" '.friction_points += [{"type": "git_workflow", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        friction_count=$((friction_count + 1))
    fi
    
    # Return the numeric value
    echo $friction_count
}

# Function to generate improvement recommendations
generate_recommendations() {
    local pfc_compliance=$1
    local friction_count=$2
    
    echo "   📋 Generating recommendations..."
    
    local recommendations=()
    
    # PFC compliance recommendations
    if [ $pfc_compliance -lt $COMPLIANCE_MINIMUM ]; then
        recommendations+=("Improve PFC compliance: Automate validation checks")
    fi
    
    # Friction recommendations
    if [ $friction_count -gt 0 ]; then
        recommendations+=("Implement automated session lock cleanup")
        recommendations+=("Fix broken symbolic links and documentation")
        recommendations+=("Add git workflow automation")
    fi
    
    # General improvement
    recommendations+=("Enhance documentation navigation")
    recommendations+=("Strengthen conflict prevention mechanisms")
    
    # Add recommendations to JSON
    for rec in "${recommendations[@]}"; do
        jq --arg rec "$rec" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
    done
    
    echo "     Generated ${#recommendations[@]} recommendations"
}

# Function to finalize evaluation
finalize_evaluation() {
    local pfc_compliance=$1
    local friction_count=$2
    
    echo "   📝 Finalizing evaluation..."
    
    local final_status="pass"
    local block_reason=""
    
    # Determine final status
    if [ $pfc_compliance -lt $COMPLIANCE_MINIMUM ]; then
        final_status="blocked"
        block_reason="PFC compliance below ${COMPLIANCE_MINIMUM}%"
    elif [ $friction_count -gt 3 ]; then
        final_status="blocked"
        block_reason="High process friction detected"
    fi
    
    # Update final status in JSON
    jq --arg status "$final_status" --arg reason "$block_reason" '.status = $status | .block_reason = $reason' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
    
    echo "   Final Status: $final_status"
    
    if [ "$final_status" = "blocked" ]; then
        echo "   🚫 BLOCKER: $block_reason"
        echo ""
        echo "   🔧 Action Required:"
        echo "     1. Address all identified friction points"
        echo "     2. Improve PFC compliance to ${COMPLIANCE_MINIMUM}%+"
        echo "     3. Re-run SOP evaluation"
        echo ""
        echo "   ❌ RTB BLOCKED: Fix issues before proceeding"
        return 1
    else
        echo "   ✅ SOP Evaluation PASSED"
        echo ""
        echo "   📊 Summary:"
        echo "     PFC Compliance: ${pfc_compliance}%"
        echo "     Friction Points: $friction_count"
        echo "     Status: $final_status"
        return 0
    fi
}

# Main evaluation flow
main() {
    echo "Starting comprehensive SOP effectiveness evaluation..."
    echo ""
    
    # Run all evaluation components and capture just the numeric values
    local pfc_compliance_output=$(calculate_pfc_compliance)
    local pfc_compliance=$(echo "$pfc_compliance_output" | tail -1)
    local friction_output=$(analyze_process_friction)
    local friction_count=$(echo "$friction_output" | tail -1)
    generate_recommendations "$pfc_compliance" "$friction_count"
    
    # Finalize and return status
    finalize_evaluation "$pfc_compliance" "$friction_count"
    
    # Capture learnings using reflect system if evaluation passed
    if [ $? -eq 0 ]; then
        echo ""
        echo "💡 Capturing SOP evaluation learnings with reflect system..."
        
        # Check if reflect system is available
        if [ -f "$HOME/.gemini/antigravity/skills/Reflect/scripts/enhanced_reflect_system.py" ]; then
            echo "🧠 Running flight diagnostics to capture learnings..."
            python3 "$HOME/.gemini/antigravity/skills/Reflect/scripts/enhanced_reflect_system.py" --flight-diagnostics || echo "⚠️  Flight diagnostics completed with warnings"
        else
            echo "ℹ️  Note: Run '/reflect' manually to capture SOP evaluation learnings for continuous improvement"
            echo "💡 SOP evaluation results available at: $EVALUATION_FILE"
        fi
    fi
}

# Run evaluation if called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi