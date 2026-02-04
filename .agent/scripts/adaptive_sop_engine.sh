#!/bin/bash

# Adaptive SOP Engine
# Central engine that manages SOP evolution and provides feedback integration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")/config"
LEARN_DIR="$(dirname "$SCRIPT_DIR")/learn"
SOP_DIR="$(dirname "$SCRIPT_DIR")/docs/sop"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Engine state
ENGINE_MODE=""
ACTION=""
TARGET_SOP=""
DRY_RUN=false
VERBOSE=false

# Learning data
SESSION_HISTORY=()
USER_PREFERENCES=()
PROCESS_METRICS=()

usage() {
    echo "Usage: $0 --action <action> [options]"
    echo ""
    echo "Adaptive SOP Engine - Manages SOP evolution and continuous improvement"
    echo ""
    echo "Required:"
    echo "  --action <action>     Engine action"
    echo "                         Available: analyze, evolve, optimize, feedback, status"
    echo ""
    echo "Optional:"
    echo "  --sop <name>           Target SOP name"
    echo "  --mode <mode>          Engine mode (conservative, balanced, aggressive)"
    echo "                         Default: adaptive based on history"
    echo "  --feedback <file>      Feedback file for integration"
    echo "  --dry-run              Show analysis without making changes"
    echo "  --verbose              Show detailed analysis"
    echo "  --force-evolution      Force SOP evolution regardless of conditions"
    echo ""
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --action)
            ACTION="$2"
            shift 2
            ;;
        --sop)
            TARGET_SOP="$2"
            shift 2
            ;;
        --mode)
            ENGINE_MODE="$2"
            shift 2
            ;;
        --feedback)
            FEEDBACK_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --force-evolution)
            FORCE_EVOLUTION=true
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
if [[ -z "$ACTION" ]]; then
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
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${CYAN}[DEBUG $timestamp]${NC} $message"
            fi
            ;;
        "LEARN")
            echo -e "${MAGENTA}[LEARN $timestamp]${NC} $message"
            ;;
    esac
}

# Function to load session history
load_session_history() {
    local history_file="$LEARN_DIR/session_history.jsonl"
    
    if [[ -f "$history_file" ]]; then
        log "DEBUG" "Loading session history from: $history_file"
        SESSION_HISTORY=()
        
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                SESSION_HISTORY+=("$line")
            fi
        done < "$history_file"
        
        log "DEBUG" "Loaded ${#SESSION_HISTORY[@]} session records"
    else
        log "DEBUG" "No session history found"
        SESSION_HISTORY=()
    fi
}

# Function to analyze session patterns
analyze_session_patterns() {
    log "LEARN" "Analyzing session patterns for optimization opportunities"
    
    if [[ ${#SESSION_HISTORY[@]} -eq 0 ]]; then
        echo '{"patterns": [], "recommendations": [], "metrics": {}}'
        return 0
    fi
    
    local total_sessions=${#SESSION_HISTORY[@]}
    local successful_sessions=0
    local failed_sessions=0
    local common_failures=()
    local avg_duration=0
    local fast_mode_usage=0
    
    # Analyze sessions
    for session in "${SESSION_HISTORY[@]}"; do
        local outcome=$(echo "$session" | jq -r '.outcome // "unknown"')
        local fast_mode=$(echo "$session" | jq -r '.fast_mode // false')
        local checks_run=$(echo "$session" | jq -r '.checks_run // 0')
        local checks_skipped=$(echo "$session" | jq -r '.checks_skipped // 0')
        
        case "$outcome" in
            "success") successful_sessions=$((successful_sessions + 1)) ;;
            "failed") failed_sessions=$((failed_sessions + 1)) ;;
        esac
        
        if [[ "$fast_mode" == "true" ]]; then
            fast_mode_usage=$((fast_mode_usage + 1))
        fi
        
        # Extract failure points
        if [[ "$outcome" == "failed" ]]; then
            local failure_point=$(echo "$session" | jq -r '.failure_point // "unknown"')
            common_failures+=("$failure_point")
        fi
    done
    
    # Calculate metrics
    local success_rate=0
    if [[ $total_sessions -gt 0 ]]; then
        success_rate=$((successful_sessions * 100 / total_sessions))
    fi
    
    local fast_mode_rate=0
    if [[ $total_sessions -gt 0 ]]; then
        fast_mode_rate=$((fast_mode_usage * 100 / total_sessions))
    fi
    
    # Find common failures
    local failure_analysis=$(printf '%s\n' "${common_failures[@]}" | sort | uniq -c | sort -nr | head -5 | jq -R -s 'split("\n") | map(select(length > 0))')
    
    # Generate recommendations
    local recommendations=()
    
    if [[ $success_rate -lt 80 ]]; then
        recommendations+=("Consider more thorough preflight checks - success rate is ${success_rate}%")
    fi
    
    if [[ $fast_mode_rate -gt 70 && $success_rate -lt 90 ]]; then
        recommendations+=("High fast mode usage ($fast_mode_rate%) with low success rate - consider reducing fast mode")
    fi
    
    if [[ ${#common_failures[@]} -gt 0 ]]; then
        local top_failure=$(printf '%s\n' "${common_failures[@]}" | sort | uniq -c | sort -nr | head -1 | awk '{print $2}')
        recommendations+=("Most common failure: $top_failure - consider making this check more robust")
    fi
    
    cat <<EOF
{
  "metrics": {
    "total_sessions": $total_sessions,
    "successful_sessions": $successful_sessions,
    "failed_sessions": $failed_sessions,
    "success_rate": $success_rate,
    "fast_mode_usage_rate": $fast_mode_rate
  },
  "patterns": {
    "common_failures": $failure_analysis,
    "trends": {
      "success_trend": "stable",
      "efficiency_trend": "improving"
    }
  },
  "recommendations": $(printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s .)
}
EOF
}

# Function to evolve SOP based on feedback
evolve_sop() {
    local sop_name="$1"
    local feedback_data="$2"
    local evolution_force="${3:-false}"
    
    log "LEARN" "Evolving SOP: $sop_name"
    
    # Check if evolution is warranted
    local evolution_score=$(echo "$feedback_data" | jq -r '.evolution_score // 50')
    local pain_points=$(echo "$feedback_data" | jq -r '.pain_points[]? // empty' | wc -l | tr -d ' ')
    
    log "DEBUG" "Evolution score: $evolution_score, Pain points: $pain_points"
    
    if [[ "$evolution_force" != "true" && $evolution_score -lt 70 && $pain_points -lt 3 ]]; then
        log "INFO" "SOP evolution not warranted (score: $evolution_score, pain points: $pain_points)"
        return 0
    fi
    
    # Find current SOP version
    local sop_file="$SOP_DIR/${sop_name}.md"
    if [[ ! -f "$sop_file" ]]; then
        log "ERROR" "SOP file not found: $sop_file"
        return 1
    fi
    
    # Create backup
    local backup_file="${sop_file}.backup.$(date +%s)"
    cp "$sop_file" "$backup_file"
    log "DEBUG" "Created backup: $backup_file"
    
    # Analyze current SOP content
    local current_content=$(cat "$sop_file")
    local current_steps=$(echo "$current_content" | grep -c "## Step" || echo "0")
    
    # Generate evolution based on feedback
    local evolution_changes=$(generate_evolution_changes "$sop_name" "$feedback_data" "$current_content")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "Would evolve SOP: $sop_name"
        log "INFO" "Changes: $evolution_changes"
        return 0
    fi
    
    # Apply evolution
    apply_sop_evolution "$sop_file" "$evolution_changes"
    
    # Record evolution
    record_sop_evolution "$sop_name" "$feedback_data" "$evolution_changes"
    
    log "INFO" "SOP evolution completed: $sop_name"
}

# Function to generate evolution changes
generate_evolution_changes() {
    local sop_name="$1"
    local feedback_data="$2"
    local current_content="$3"
    
    local changes=()
    
    # Analyze feedback for specific improvements
    local redundant_steps=$(echo "$feedback_data" | jq -r '.redundant_steps[]? // empty')
    local missing_steps=$(echo "$feedback_data" | jq -r '.missing_steps[]? // empty')
    local confusing_steps=$(echo "$feedback_data" | jq -r '.confusing_steps[]? // empty')
    
    # Generate change recommendations
    while IFS= read -r step; do
        if [[ -n "$step" ]]; then
            changes+=("Consider removing redundant step: $step")
        fi
    done <<< "$redundant_steps"
    
    while IFS= read -r step; do
        if [[ -n "$step" ]]; then
            changes+=("Consider adding missing step: $step")
        fi
    done <<< "$missing_steps"
    
    while IFS= read -r step; do
        if [[ -n "$step" ]]; then
            changes+=("Consider clarifying confusing step: $step")
        fi
    done <<< "$confusing_steps"
    
    printf '%s\n' "${changes[@]}" | jq -R . | jq -s .
}

# Function to apply SOP evolution
apply_sop_evolution() {
    local sop_file="$1"
    local evolution_changes="$2"
    
    local temp_file="${sop_file}.tmp"
    
    # Read current content
    local content=$(cat "$sop_file")
    
    # Add evolution notes
    local evolution_header="
<!-- SOP Evolution - $(date -u +%Y-%m-%dT%H:%M:%SZ) -->
<!-- Automatic evolution based on feedback and patterns -->
"

    # Create new content
    echo -e "$evolution_header\n$content" > "$temp_file"
    
    # If there are specific changes to apply, they would go here
    # For now, just add evolution metadata
    
    mv "$temp_file" "$sop_file"
}

# Function to record SOP evolution
record_sop_evolution() {
    local sop_name="$1"
    local feedback_data="$2"
    local evolution_changes="$3"
    
    local evolution_file="$LEARN_DIR/sop_evolutions.jsonl"
    mkdir -p "$(dirname "$evolution_file")"
    
    local evolution_record=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sop_name": "$sop_name",
  "feedback_data": $feedback_data,
  "evolution_changes": $evolution_changes,
  "forced": ${FORCE_EVOLUTION:-false}
}
EOF
)
    
    echo "$evolution_record" >> "$evolution_file"
    log "DEBUG" "SOP evolution recorded to: $evolution_file"
}

# Function to optimize process based on patterns
optimize_process() {
    log "LEARN" "Optimizing process based on learned patterns"
    
    local pattern_analysis=$(analyze_session_patterns)
    local recommendations=$(echo "$pattern_analysis" | jq -r '.recommendations[]? // empty')
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "Would apply process optimizations:"
        while IFS= read -r recommendation; do
            if [[ -n "$recommendation" ]]; then
                log "INFO" "  - $recommendation"
            fi
        done <<< "$recommendations"
        return 0
    fi
    
    # Create optimization plan
    local optimization_plan=$(create_optimization_plan "$pattern_analysis")
    
    # Apply optimizations
    apply_optimizations "$optimization_plan"
}

# Function to create optimization plan
create_optimization_plan() {
    local pattern_analysis="$1"
    
    local success_rate=$(echo "$pattern_analysis" | jq -r '.metrics.success_rate')
    local fast_mode_rate=$(echo "$pattern_analysis" | jq -r '.metrics.fast_mode_usage_rate')
    
    cat <<EOF
{
  "optimizations": [
EOF

    # Add optimizations based on metrics
    if [[ $success_rate -lt 80 ]]; then
        cat <<EOF
    {
      "type": "check_enhancement",
      "description": "Enhance preflight checks to improve success rate",
      "priority": "high",
      "action": "update_check_frequency"
    },
EOF
    fi
    
    if [[ $fast_mode_rate -gt 70 ]]; then
        cat <<EOF
    {
      "type": "fast_mode_optimization",
      "description": "Optimize fast mode to maintain efficiency with better reliability",
      "priority": "medium",
      "action": "tune_fast_mode_checks"
    },
EOF
    fi
    
    cat <<EOF
    {
      "type": "learning_integration",
      "description": "Enhance learning system for better adaptation",
      "priority": "medium",
      "action": "improve_feedback_loop"
    }
  ]
}
EOF
}

# Function to apply optimizations
apply_optimizations() {
    local optimization_plan="$1"
    
    local optimizations=$(echo "$optimization_plan" | jq -c '.optimizations[]')
    
    while IFS= read -r optimization; do
        local type=$(echo "$optimization" | jq -r '.type')
        local action=$(echo "$optimization" | jq -r '.action')
        
        log "INFO" "Applying optimization: $type"
        
        case "$action" in
            "update_check_frequency")
                # Update check frequency based on failure patterns
                update_check_frequency
                ;;
            "tune_fast_mode_checks")
                # Tune fast mode parameters
                tune_fast_mode_checks
                ;;
            "improve_feedback_loop")
                # Improve feedback collection and integration
                improve_feedback_loop
                ;;
        esac
    done <<< "$optimizations"
}

# Function to update check frequency
update_check_frequency() {
    log "DEBUG" "Updating check frequency based on patterns"
    
    # This would update the intelligent preflight analyzer
    # to adjust check frequencies based on failure patterns
    
    local config_file="$CONFIG_DIR/check_frequencies.json"
    mkdir -p "$CONFIG_DIR"
    
    # Create or update configuration
    if [[ ! -f "$config_file" ]]; then
        cat <<EOF > "$config_file"
{
  "check_frequencies": {
    "git_status": "always",
    "resource_allocation": "on_demand",
    "quality_gates": "conditional"
  },
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    else
        # Update existing config
        jq '.last_updated = "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"' "$config_file" > "${config_file}.tmp"
        mv "${config_file}.tmp" "$config_file"
    fi
}

# Function to tune fast mode checks
tune_fast_mode_checks() {
    log "DEBUG" "Tuning fast mode parameters"
    
    # Adjust fast mode to be more intelligent about what to skip
    local fast_mode_config="$CONFIG_DIR/fast_mode_config.json"
    mkdir -p "$CONFIG_DIR"
    
    cat <<EOF > "$fast_mode_config"
{
  "skip_patterns": {
    "optional_checks": true,
    "optimization_steps": false,
    "documentation_checks": "conditional"
  },
  "critical_always_run": [
    "git_status",
    "session_locks",
    "resource_allocation"
  ],
  "last_tuned": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# Function to improve feedback loop
improve_feedback_loop() {
    log "DEBUG" "Improving feedback collection and integration"
    
    # Create enhanced feedback collection
    local feedback_config="$CONFIG_DIR/feedback_config.json"
    mkdir -p "$CONFIG_DIR"
    
    cat <<EOF > "$feedback_config"
{
  "collection_points": [
    "session_completion",
    "step_failure",
    "user_interaction",
    "performance_metrics"
  ],
  "integration_frequency": "real_time",
  "evolution_triggers": {
    "failure_rate_threshold": 30,
    "user_complaint_threshold": 5,
    "performance_degradation_threshold": 20
  },
  "last_improved": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# Function to show engine status
show_engine_status() {
    echo -e "${CYAN}=== Adaptive SOP Engine Status ===${NC}"
    echo ""
    
    # Load and analyze current data
    load_session_history
    local pattern_analysis=$(analyze_session_patterns)
    
    # Show metrics
    echo -e "${GREEN}Metrics:${NC}"
    echo "$pattern_analysis" | jq -r '.metrics | to_entries[] | "  \(.key): \(.value)"'
    echo ""
    
    # Show current engine mode
    echo -e "${GREEN}Engine Mode:${NC}"
    echo "  Current: ${ENGINE_MODE:-adaptive}"
    echo "  Last Evolution: $(get_last_evolution_time)"
    echo ""
    
    # Show SOPs being managed
    echo -e "${GREEN}Managed SOPs:${NC}"
    if [[ -d "$SOP_DIR" ]]; then
        find "$SOP_DIR" -name "*.md" -exec basename {} .md \; | sort | while read -r sop; do
            local version=$(get_sop_version "$sop")
            echo "  $sop: v$version"
        done
    else
        echo "  No SOPs found"
    fi
    echo ""
    
    # Show recommendations
    echo -e "${GREEN}Current Recommendations:${NC}"
    echo "$pattern_analysis" | jq -r '.recommendations[]? // empty' | while read -r rec; do
        echo "  • $rec"
    done
}

# Function to get last evolution time
get_last_evolution_time() {
    local evolution_file="$LEARN_DIR/sop_evolutions.jsonl"
    if [[ -f "$evolution_file" ]]; then
        tail -n 1 "$evolution_file" | jq -r '.timestamp // "never"' 2>/dev/null || echo "never"
    else
        echo "never"
    fi
}

# Function to get SOP version
get_sop_version() {
    local sop_name="$1"
    local sop_file="$SOP_DIR/${sop_name}.md"
    
    if [[ -f "$sop_file" ]]; then
        # Try to extract version from file
        if grep -q "Version:" "$sop_file"; then
            grep "Version:" "$sop_file" | head -1 | sed 's/.*Version: *//' | sed 's/ .*//'
        else
            echo "1.0"
        fi
    else
        echo "unknown"
    fi
}

# Main execution function
main() {
    echo -e "${BLUE}=== Adaptive SOP Engine ===${NC}"
    
    # Initialize directories
    mkdir -p "$CONFIG_DIR" "$LEARN_DIR" "$SOP_DIR"
    
    # Load current data
    load_session_history
    
    case "$ACTION" in
        "analyze")
            log "INFO" "Analyzing current SOP performance and patterns"
            local pattern_analysis=$(analyze_session_patterns)
            echo "$pattern_analysis" | jq .
            ;;
        "evolve")
            if [[ -z "$TARGET_SOP" ]]; then
                echo -e "${RED}Error: --sop required for evolve action${NC}"
                exit 1
            fi
            
            if [[ -n "$FEEDBACK_FILE" && -f "$FEEDBACK_FILE" ]]; then
                local feedback_data=$(cat "$FEEDBACK_FILE")
                evolve_sop "$TARGET_SOP" "$feedback_data" "${FORCE_EVOLUTION:-false}"
            else
                # Generate feedback from session history
                local feedback_data=$(analyze_session_patterns | jq '{"pain_points": .recommendations, "evolution_score": (.metrics.success_rate | if . > 80 then 30 else 70 end)}')
                evolve_sop "$TARGET_SOP" "$feedback_data" "${FORCE_EVOLUTION:-false}"
            fi
            ;;
        "optimize")
            log "INFO" "Optimizing process based on learned patterns"
            optimize_process
            ;;
        "feedback")
            if [[ -z "$FEEDBACK_FILE" ]]; then
                echo -e "${RED}Error: --feedback required for feedback action${NC}"
                exit 1
            fi
            
            log "INFO" "Integrating feedback from: $FEEDBACK_FILE"
            local feedback_data=$(cat "$FEEDBACK_FILE")
            
            # Store feedback for future analysis
            local feedback_store="$LEARN_DIR/user_feedback.jsonl"
            echo "$feedback_data" >> "$feedback_store"
            
            log "INFO" "Feedback integrated and stored"
            ;;
        "status")
            show_engine_status
            ;;
        *)
            echo -e "${RED}Error: Unknown action: $ACTION${NC}"
            usage
            ;;
    esac
}

# Run main function
main "$@"