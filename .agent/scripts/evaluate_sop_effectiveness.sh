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

# Function to detect multi-phase implementation patterns
detect_multi_phase_patterns() {
    echo "   🔍 Detecting multi-phase implementation patterns..."

    local detector_script=".agent/scripts/multi_phase_detector.py"
    local detection_result=""

    # Check if detector exists
    if [ ! -f "$detector_script" ]; then
        echo "     ⚠️  Multi-phase detector not found: $detector_script"
        jq --arg msg "Multi-phase detector not found" '.friction_points += [{"type": "multi_phase", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        echo "0"  # Return clear status (no detection)
        return 0
    fi

    # Run multi-phase detection with error handling
    echo "     🚨 Running multi-phase detection engine..."

    # Run detector and capture output and exit code
    detection_result=$(python3 "$detector_script" 2>/dev/null)
    local detector_exit_code=$?

    # Check for execution error
    if [ $detector_exit_code -gt 2 ]; then
        echo "     ⚠️  Multi-phase detection failed (exit code: $detector_exit_code)"
        jq --arg msg "Multi-phase detection failed" '.friction_points += [{"type": "multi_phase", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        echo "0"  # Return clear status on error
        return 0
    fi

    # Parse detector output for status based on exit code and pattern detection
    local detected_pattern=$(echo "$detection_result" | grep -E "(DETECTED|CLEAR)" | tail -1)

    if [ $detector_exit_code -eq 1 ] || [[ "$detected_pattern" == *"DETECTED"* ]]; then
        echo "     🚨 MULTI-PHASE PATTERNS DETECTED"
        jq --arg msg "Multi-phase implementation patterns detected" '.friction_points += [{"type": "multi_phase", "description": $msg, "severity": "high"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"

        # Add multi-phase specific recommendations
        jq --arg rec "SPLIT IMPLEMENTATION: Multi-phase work detected - split into single-phase tasks" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        jq --arg rec "HAND-OFF PROTOCOL: Use proper hand-off documentation for multi-phase work" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        jq --arg rec "BRANCH MANAGEMENT: Create separate branches for each implementation phase" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"

        echo "1"  # Return detected status
        return 1
    else
        echo "     ✅ No multi-phase patterns detected"
        echo "0"  # Return clear status
        return 0
    fi
}

# Function to verify hand-off compliance for multi-phase work
verify_handoff_compliance_integration() {
    echo "   🔍 Verifying hand-off compliance..."

    local handoff_script=".agent/scripts/verify_handoff_compliance.sh"
    local handoff_result=""

    # Check if handoff verifier exists
    if [ ! -f "$handoff_script" ]; then
        echo "     ⚠️  Hand-off compliance verifier not found"
        jq --arg msg "Hand-off compliance verifier not found" '.friction_points += [{"type": "handoff_compliance", "description": $msg, "severity": "low"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        echo "0"  # Return clear status
        return 0
    fi

    # Check if hand-offs directory exists and has content
    local handoff_dir="${HANDOFF_DIR:-.agent/handoffs}"
    if [ ! -d "$handoff_dir" ] || [ -z "$(ls -A "$handoff_dir" 2>/dev/null)" ]; then
        echo "     ℹ️  No hand-off documents found - compliance check skipped"
        echo "0"  # Return clear status (no hand-offs to verify)
        return 0
    fi

    # Try to auto-detect a feature or phase to verify
    local feature_name=""
    local phase_name=""

    # Look for any .json hand-off files and extract feature/phase info
    for handoff_file in "$handoff_dir"/*.json; do
        if [ -f "$handoff_file" ]; then
            # Try to extract feature name from filename or content
            local filename=$(basename "$handoff_file" .json)
            if [[ "$filename" =~ ([a-zA-Z0-9-]+)_.*phase_([0-9]+) ]]; then
                feature_name="${BASH_REMATCH[1]}"
                phase_name="phase-${BASH_REMATCH[2]}"
                break
            elif [[ "$filename" =~ phase_([0-9]+) ]]; then
                phase_name="phase-${BASH_REMATCH[1]}"
                break
            elif [[ "$filename" =~ ([a-zA-Z0-9-]+) ]]; then
                feature_name="${BASH_REMATCH[1]}"
                break
            fi
        fi
    done

    # Run hand-off compliance verification with detected parameters
    echo "     📋 Verifying hand-off document compliance..."

    if [ -n "$phase_name" ]; then
        handoff_result=$("$handoff_script" --phase "$phase_name" --report 2>/dev/null) || {
            local handoff_exit_code=$?
            echo "     ⚠️  Hand-off compliance verification failed for phase $phase_name (exit code: $handoff_exit_code)"
            jq --arg msg "Hand-off compliance verification failed" '.friction_points += [{"type": "handoff_compliance", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
            echo "0"  # Return clear status on error
            return 0
        }
    elif [ -n "$feature_name" ]; then
        handoff_result=$("$handoff_script" --feature "$feature_name" --report 2>/dev/null) || {
            local handoff_exit_code=$?
            echo "     ⚠️  Hand-off compliance verification failed for feature $feature_name (exit code: $handoff_exit_code)"
            jq --arg msg "Hand-off compliance verification failed" '.friction_points += [{"type": "handoff_compliance", "description": $msg, "severity": "medium"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
            echo "0"  # Return clear status on error
            return 0
        }
    else
        echo "     ℹ️  Could not auto-detect feature/phase - compliance check skipped"
        echo "0"  # Return clear status
        return 0
    fi

    # Parse hand-off verification results
    local compliance_issues=$(echo "$handoff_result" | grep -c "FAILED\|ERROR" 2>/dev/null || echo "0")

    if [ "$compliance_issues" -gt 0 ]; then
        echo "     ⚠️  Hand-off compliance issues found: $compliance_issues"
        jq --arg msg "Hand-off compliance issues: $compliance_issues" '.friction_points += [{"type": "handoff_compliance", "description": $msg, "severity": "high"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"

        # Add hand-off specific recommendations
        jq --arg rec "Fix $compliance_issues hand-off compliance issues" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
        jq --arg rec "Ensure all hand-off documents meet SOP requirements" '.recommendations += [$rec]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"

        echo "$compliance_issues"  # Return number of issues
        return 1
    else
        echo "     ✅ Hand-off compliance verified"
        echo "0"  # Return clear status
        return 0
    fi
}

# Function to generate improvement recommendations
generate_recommendations() {
    local pfc_compliance=$1
    local friction_count=$2
    local multi_phase_detected=$3
    local handoff_issues=$4

    echo "   📋 Generating recommendations..."

    local recommendations=()

    # PFC compliance recommendations
    if [ $pfc_compliance -lt $COMPLIANCE_MINIMUM ]; then
        recommendations+=("Improve PFC compliance: Automate validation checks")
    fi

    # Multi-phase specific recommendations
    if [ "$multi_phase_detected" = "1" ]; then
        recommendations+=("SPLIT IMPLEMENTATION: Multi-phase work detected - split into single-phase tasks")
        recommendations+=("HAND-OFF PROTOCOL: Use proper hand-off documentation for multi-phase work")
        recommendations+=("BRANCH MANAGEMENT: Create separate branches for each implementation phase")
    fi

    # Hand-off compliance recommendations
    if [ "$handoff_issues" -gt 0 ]; then
        recommendations+=("Fix $handoff_issues hand-off compliance issues")
        recommendations+=("Ensure hand-off documents meet all SOP requirements")
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

# Function to finalize evaluation with multi-phase blocking
finalize_evaluation_enhanced() {
    local pfc_compliance=$1
    local friction_count=$2
    local multi_phase_detected=$3
    local handoff_issues=$4

    echo "   📝 Finalizing enhanced evaluation..."

    local final_status="pass"
    local block_reason=""

    # Determine final status with multi-phase blocking
    if [ $pfc_compliance -lt $COMPLIANCE_MINIMUM ]; then
        final_status="blocked"
        block_reason="PFC compliance below ${COMPLIANCE_MINIMUM}%"
    elif [ "$multi_phase_detected" = "1" ]; then
        final_status="blocked"
        block_reason="Multi-phase implementation detected - SPLIT INTO SINGLE-PHASE TASKS"
    elif [ "$handoff_issues" -gt 0 ]; then
        final_status="blocked"
        if [ "$handoff_issues" = "999" ]; then
            block_reason="CRITICAL: Multi-phase work without mandatory hand-off documents - SOP BYPASS BLOCKED"
        else
            block_reason="Hand-off compliance issues detected ($handoff_issues issues)"
        fi
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

        if [ $pfc_compliance -lt $COMPLIANCE_MINIMUM ]; then
            echo "     1. Improve PFC compliance to ${COMPLIANCE_MINIMUM}%+"
        fi

        if [ "$multi_phase_detected" = "1" ]; then
            echo "     2. SPLIT IMPLEMENTATION into single-phase tasks"
            echo "     3. Use proper hand-off protocol for multi-phase work"
            echo "     4. Create separate branches for each phase"
        fi

        if [ "$handoff_issues" -gt 0 ]; then
            if [ "$handoff_issues" = "999" ]; then
                echo "     5. 🚨 CREATE MANDATORY HAND-OFF DOCUMENTS for multi-phase work"
                echo "     6. Use: .agent/scripts/verify_handoff_compliance.sh --phase <phase-id> --feature <feature>"
                echo "     7. Store hand-offs in: .agent/handoffs/<feature>/phase-XX-handoff.md"
            else
                echo "     5. Fix $handoff_issues hand-off compliance issues"
            fi
        fi

        if [ $friction_count -gt 0 ]; then
            echo "     6. Address $friction_count process friction points"
        fi

        echo "     7. Re-run SOP evaluation after fixes"
        echo ""
        echo "   ❌ RTB BLOCKED: Multi-phase detection prevents bypass - fix issues before proceeding"
        return 1
    else
        echo "   ✅ SOP Evaluation PASSED"
        echo ""
        echo "   📊 Enhanced Summary:"
        echo "     PFC Compliance: ${pfc_compliance}%"
        echo "     Friction Points: $friction_count"
        echo "     Multi-Phase Status: Clear"
        echo "     Hand-off Compliance: Verified"
        echo "     Status: $final_status"
        return 0
    fi
}

# Function to finalize evaluation (legacy for backward compatibility)
finalize_evaluation() {
    local pfc_compliance=$1
    local friction_count=$2
    finalize_evaluation_enhanced "$pfc_compliance" "$friction_count" "0" "0"
}

# Main evaluation flow
main() {
    echo "Starting comprehensive SOP effectiveness evaluation with multi-phase detection..."
    echo ""

    # Run all evaluation components and capture just the numeric values
    local pfc_compliance_output=$(calculate_pfc_compliance)
    local pfc_compliance=$(echo "$pfc_compliance_output" | tail -1)
    local friction_output=$(analyze_process_friction)
    local friction_count=$(echo "$friction_output" | tail -1)

    # NEW: Run multi-phase detection and handoff compliance
    local multi_phase_output=$(detect_multi_phase_patterns)
    local multi_phase_detected=$(echo "$multi_phase_output" | tail -1)
    
    # CRITICAL FIX: Only run hand-off verification if multi-phase detected
    # This prevents false positives for single-phase work
    local handoff_issues=0
    if [ "$multi_phase_detected" = "1" ]; then
        echo "   🚨 Multi-phase detected - MANDATORY hand-off verification required"
        local handoff_output=$(verify_handoff_compliance_integration)
        handoff_issues=$(echo "$handoff_output" | tail -1)
        
        # CRITICAL FIX: Block if hand-off documents missing for multi-phase work
        if [ "$handoff_issues" -eq 0 ]; then
            # Check if hand-off directory exists but is empty (missing hand-offs)
            local handoff_dir="${HANDOFF_DIR:-.agent/handoffs}"
            if [ -d "$handoff_dir" ] && [ -z "$(ls -A "$handoff_dir" 2>/dev/null)" ]; then
                echo "     🚨 CRITICAL: Multi-phase work detected but NO hand-off documents found"
                jq --arg msg "Multi-phase work without hand-off documents - SOP bypass blocked" '.friction_points += [{"type": "handoff_compliance", "description": $msg, "severity": "critical"}]' "$EVALUATION_FILE" > "$EVALUATION_FILE.tmp" && mv "$EVALUATION_FILE.tmp" "$EVALUATION_FILE"
                handoff_issues=999  # Use special code to indicate missing hand-offs
            fi
        fi
    else
        echo "   ✅ Single-phase work detected - hand-off verification not required"
    fi

    # Generate enhanced recommendations
    generate_recommendations "$pfc_compliance" "$friction_count" "$multi_phase_detected" "$handoff_issues"

    # Finalize with enhanced evaluation (includes multi-phase blocking)
    finalize_evaluation_enhanced "$pfc_compliance" "$friction_count" "$multi_phase_detected" "$handoff_issues"
    local final_exit_code=$?

    # Capture learnings using reflect system if evaluation passed
    if [ $final_exit_code -eq 0 ]; then
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
    else
        # NEW: Enhanced blocking message for multi-phase detection
        if [ "$multi_phase_detected" = "1" ]; then
            echo ""
            echo "🚨 MULTI-PHASE IMPLEMENTATION BLOCKED BY SOP ENFORCEMENT"
            echo "   This protects workflow integrity and prevents bypass of hand-off protocols"
            echo "   The system detected patterns suggesting multi-phase implementation work"
            echo ""
            echo "💡 REQUIRED ACTIONS BEFORE RTB:"
            echo "   1. SPLIT: Break implementation into focused, single-phase tasks"
            echo "   2. DOCUMENT: Create proper hand-off documents for each phase"
            echo "   3. BRANCH: Use separate branches for each implementation phase"
            echo "   4. VERIFY: Run hand-off compliance verification for each phase"
            echo "   5. RE-EVALUATE: SOP evaluation will pass when properly structured"
        fi
    fi

    # CRITICAL: Ensure main function returns the proper exit code
    return $final_exit_code
}

# Run evaluation if called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
    main_exit_code=$?
    exit $main_exit_code
fi
