#!/usr/bin/env zsh

# 🏁 LightRAG Session Cleanup Script
# Purpose: Clean session shutdown with data preservation and status saving
# Usage: Run at end of every work session

set -e  # Exit on any error

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LIGHTRAG_ROOT="$PWD"
SESSION_END=$(date '+%Y-%m-%d %H:%M:%S')

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${BLUE}🔸 $1${NC}"
}

# ============================================================================
# SESSION SUMMARY
# ============================================================================

generate_session_summary() {
    log_step "Generating Session Summary"

    if [[ -f "$LIGHTRAG_ROOT/.session_active" ]]; then
        local session_start=$(cat "$LIGHTRAG_ROOT/.session_active")
        echo -e "  🕐 Session Start: $session_start"
        echo -e "  🕐 Session End: $SESSION_END"

        # Calculate duration (basic calculation)
        echo -e "  ⏱️  Session Duration: $(echo "$session_start" | grep -o '\d\d:\d\d:\d\d') → $(date '+%H:%M:%S')"
    fi

    # Count completed Beads (if possible)
    if command -v bd >/dev/null 2>&1; then
        local completed_tasks=$(bd list --status done --quiet 2>/dev/null | wc -l || echo "0")
        echo -e "  📋 Completed Tasks: $completed_tasks"
    fi
}

# ============================================================================
# SERVICE HEALTH CHECK
# ============================================================================

check_service_health() {
    log_step "Checking Service Health Before Shutdown"

    # Check Automem health one last time
    local automem_health=$(curl -s --max-time 3 "http://localhost:8001/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [[ -n "$automem_health" ]]; then
        echo -e "  🧠 Automem: $automem_health"
    else
        echo -e "  🧠 Automem: offline"
    fi

    # Check Langfuse health
    local langfuse_health=$(curl -s --max-time 3 "http://localhost:3000/api/public/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [[ -n "$langfuse_health" ]]; then
        echo -e "  🔭 Langfuse: $langfuse_health"
    else
        echo -e "  🔭 Langfuse: offline"
    fi
}

# ============================================================================
# DATA SYNCHRONIZATION
# ============================================================================

synchronize_data() {
    log_step "Synchronizing Project Data"

    # Update Beads status
    if command -v bd >/dev/null 2>&1; then
        log_info "Synchronizing Beads..."
        if bd sync; then
            log_success "Beads synchronized"
        else
            log_warning "Beads synchronization failed"
        fi
    fi

    # Git operations
    log_info "Synchronizing Git repository..."

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "  📝 Uncommitted changes detected"

        # Show summary of changes
        git status --porcelain | head -5

        echo -e "  💡 Consider committing changes:"
        echo -e "     git add ."
        echo -e "     git commit -m 'Session work: $(date '+%Y-%m-%d')'"
    else
        log_success "Git repository clean"
    fi
}

# ============================================================================
# SERVICE SHUTDOWN OPTIONS
# ============================================================================

shutdown_services() {
    log_step "Service Shutdown Options"

    echo -e "${YELLOW}🤔 Do you want to stop services?${NC}"
    echo -e "  1) Stop all services (Automem + Langfuse)"
    echo -e "  2) Keep services running (for next session)"
    echo -e "  3) Check service status only"
    echo -e ""
    echo -ne "  Choice (1-3): "
    read -r choice

    case "$choice" in
        1)
            log_info "Stopping all services..."

            # Stop Automem
            if [[ -d "${AUTOMEM_PATH:-$HOME/GitHub/verygoodplugins/automem}" ]]; then
                cd "${AUTOMEM_PATH:-$HOME/GitHub/verygoodplugins/automem}"
                if make down >/dev/null 2>&1; then
                    log_success "Automem services stopped"
                else
                    log_warning "Automem services may still be running"
                fi
            fi

            # Stop Langfuse
            if [[ -d "$LIGHTRAG_ROOT/langfuse_docker" ]]; then
                cd "$LIGHTRAG_ROOT/langfuse_docker"
                if docker-compose down >/dev/null 2>&1; then
                    log_success "Langfuse services stopped"
                else
                    log_warning "Langfuse services may still be running"
                fi
            fi

            cd "$LIGHTRAG_ROOT"
            ;;
        2)
            log_info "Keeping services running for next session"
            echo -e "  💡 Services will be available on next startup"
            ;;
        3)
            log_info "Service status only - no changes made"
            ;;
        *)
            log_warning "Invalid choice - no changes made"
            ;;
    esac
}

# ============================================================================
# SESSION REFLECTION (Simplified)
# ============================================================================

session_reflection() {
    log_step "Session Reflection"

    # Create simple session log
    local session_log="$LIGHTRAG_ROOT/.session_logs"
    mkdir -p "$session_log"

    local log_file="$session_log/session_$(date '+%Y%m%d_%H%M%S').md"

    cat > "$log_file" << EOF
# Session Log - $(date '+%Y-%m-%d %H:%M:%S')

## Session Summary
- **Start**: $(cat "$LIGHTRAG_ROOT/.session_active" 2>/dev/null || echo "Unknown")
- **End**: $SESSION_END
- **Project**: $LIGHTRAG_ROOT

## Service Status
- **Automem**: $(curl -s --max-time 3 "http://localhost:8001/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'offline')
- **Langfuse**: $(curl -s --max-time 3 "http://localhost:3000/api/public/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'offline')

## Tasks Completed
\`\`\`bash
bd list --status done --quiet | head -10
\`\`\`

## Notes for Next Session
-
EOF

    log_success "Session log created: $log_file"
    echo -e "  📝 Add notes for your next session"
}

# ============================================================================
# CLEANUP
# ============================================================================

cleanup_session() {
    log_step "Cleaning Up Session"

    # Remove session marker
    if [[ -f "$LIGHTRAG_ROOT/.session_active" ]]; then
        rm "$LIGHTRAG_ROOT/.session_active"
        log_success "Session marker removed"
    fi

    # Optional: Clean up temporary files
    find "$LIGHTRAG_ROOT" -name "*.tmp" -type f -mtime +1 -delete 2>/dev/null || true
    find "$LIGHTRAG_ROOT" -name ".DS_Store" -delete 2>/dev/null || true

    log_success "Session cleanup completed"
}

# ============================================================================
# NEXT SESSION PREPARATION
# ============================================================================

prepare_next_session() {
    log_step "Preparing for Next Session"

    echo -e "${GREEN}🎯 Session Summary${NC}"
    echo -e "  Session ended: $SESSION_END"
    echo -e "  Project ready for next session"
    echo -e ""
    echo -e "${BLUE}🚀 Next Session Commands${NC}"
    echo -e "  • Start session: ./scripts/start-session.sh"
    echo -e "  • Check tasks: bd ready"
    echo -e "  • Test services: ./scripts/test-services.sh"
    echo -e "  • View session logs: ls -la .session_logs/"
    echo -e ""
    echo -e "${YELLOW}📚 Additional Resources${NC}"
    echo -e "  • Service issues: SERVICE_SETUP.md"
    echo -e "  • Project status: .agent/rules/ROADMAP.md"
    echo -e "  • Current phase: .agent/rules/ImplementationPlan.md"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo -e "${BLUE}🏁 LightRAG Session Cleanup${NC}"
    echo -e "Ending session at $SESSION_END"
    echo -e ""

    # Execute cleanup phases
    generate_session_summary
    check_service_health
    synchronize_data
    shutdown_services
    session_reflection
    cleanup_session
    prepare_next_session

    echo -e "\n${GREEN}✨ Session cleanup complete!${NC}"
    return 0
}

# Execute main function
main "$@"
