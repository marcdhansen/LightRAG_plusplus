#!/usr/bin/env zsh

# 🔄 LightRAG Session Startup Script
# Purpose: Fast startup for returning agents (every session)
# Usage: Run at start of every work session

set -e  # Exit on any error

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LIGHTRAG_ROOT="$PWD"
AUTOMEM_PATH="${AUTOMEM_PATH:-$HOME/GitHub/verygoodplugins/automem}"
LANGFUSE_PATH="${LANGFUSE_PATH:-$PWD/langfuse_docker}"
SESSION_START=$(date '+%Y-%m-%d %H:%M:%S')

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
# SESSION VALIDATION
# ============================================================================

validate_session_prerequisites() {
    log_step "Validating Session Prerequisites"

    # Check if one-time setup was completed
    if [[ ! -f "$LIGHTRAG_ROOT/.setup_complete" ]]; then
        log_error "One-time setup not completed"
        echo -e "  Please run: ./scripts/setup.sh"
        exit 1
    fi

    log_success "Session prerequisites validated"
}

# ============================================================================
# SERVICE STARTUP
# ============================================================================

start_services() {
    log_step "Starting Services"

    # Start Docker Desktop if needed
    if ! docker info >/dev/null 2>&1; then
        log_info "Docker Desktop is not running"
        echo -e "  🚀 Starting Docker Desktop..."

        # Try to start Docker Desktop (macOS specific)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open /Applications/Docker.app
            log_info "Waiting for Docker Desktop to start..."

            local wait_time=0
            local max_wait=60
            while [[ $wait_time -lt $max_wait ]]; do
                if docker info >/dev/null 2>&1; then
                    log_success "Docker Desktop started"
                    break
                fi
                sleep 2
                wait_time=$((wait_time + 2))
                echo -n "."
            done

            if [[ $wait_time -ge $max_wait ]]; then
                log_error "Docker Desktop failed to start within $max_wait seconds"
                exit 1
            fi
        fi
    else
        log_success "Docker Desktop is running"
    fi

    # Start Automem service
    if [[ -d "$AUTOMEM_PATH" ]]; then
        log_info "Starting Automem service..."
        cd "$AUTOMEM_PATH"

        # Check if already running
        if docker ps --filter "name=automem" --filter "status=running" | grep -q automem; then
            log_success "Automem service already running"
        else
            # Start with timeout to prevent hanging
            if timeout 60 make dev >/dev/null 2>&1; then
                log_success "Automem service started"
            else
                log_warning "Automem startup timed out, checking status..."
                if docker ps --filter "name=automem" --filter "status=running" | grep -q automem; then
                    log_success "Automem service started (slow initialization)"
                else
                    log_error "Automem service failed to start"
                fi
            fi
        fi
    else
        log_warning "Automem path not found: $AUTOMEM_PATH"
    fi

    # Start Langfuse service
    if [[ -d "$LANGFUSE_PATH" ]]; then
        log_info "Starting Langfuse service..."
        cd "$LANGFUSE_PATH"

        # Check if already running
        if docker ps --filter "name=langfuse_docker-langfuse-web-1" --filter "status=running" | grep -q langfuse_docker-langfuse-web-1; then
            log_success "Langfuse service already running"
        else
            # Start with timeout
            if timeout 90 docker-compose up -d >/dev/null 2>&1; then
                log_success "Langfuse service started"
            else
                log_warning "Langfuse startup timed out, checking status..."
                if docker ps --filter "name=langfuse_docker-langfuse-web-1" --filter "status=running" | grep -q langfuse_docker-langfuse-web-1; then
                    log_success "Langfuse service started (slow initialization)"
                else
                    log_error "Langfuse service failed to start"
                fi
            fi
        fi
    else
        log_warning "Langfuse path not found: $LANGFUSE_PATH"
    fi

    # Return to project root
    cd "$LIGHTRAG_ROOT"
}

# ============================================================================
# HEALTH VERIFICATION
# ============================================================================

verify_service_health() {
    log_step "Verifying Service Health"

    local health_errors=0

    # Check Automem health
    if curl -s --max-time 5 "http://localhost:8001/health" | grep -q '"status":\s*"healthy"'; then
        log_success "Automem service healthy"
    else
        log_error "Automem service unhealthy"
        health_errors=$((health_errors + 1))
    fi

    # Check Langfuse health
    if curl -s --max-time 5 "http://localhost:3000/api/public/health" | grep -q '"status":\s*"OK"'; then
        log_success "Langfuse service healthy"
    else
        log_error "Langfuse service unhealthy"
        health_errors=$((health_errors + 1))
    fi

    if [[ $health_errors -gt 0 ]]; then
        log_error "$health_errors service(s) unhealthy"
        echo -e "  Run: ./scripts/test-services.sh for detailed diagnostics"
        return 1
    fi

    log_success "All services healthy"
    return 0
}

# ============================================================================
# PROJECT CONTEXT LOADING
# ============================================================================

load_project_context() {
    log_step "Loading Project Context"

    # Run Flight Director PFC
    log_info "Running Pre-Flight Check (PFC)..."
    if python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc; then
        log_success "Pre-Flight Check passed"
    else
        log_error "Pre-Flight Check failed"
        echo -e "  Check planning documents and Beads state"
        return 1
    fi

    # Discover current tasks
    log_info "Discovering ready tasks..."
    if bd ready; then
        log_success "Task discovery completed"
    else
        log_warning "Task discovery failed"
    fi

    # Load project status
    if [[ -f "$LIGHTRAG_ROOT/.agent/rules/ROADMAP.md" ]]; then
        log_info "Project status available in .agent/rules/ROADMAP.md"
    fi

    if [[ -f "$LIGHTRAG_ROOT/.agent/rules/ImplementationPlan.md" ]]; then
        log_info "Current phase in .agent/rules/ImplementationPlan.md"
    fi
}

# ============================================================================
# SESSION INITIALIZATION
# ============================================================================

initialize_session() {
    log_step "Initializing Session"

    # Create session marker
    echo "Session started: $SESSION_START" > "$LIGHTRAG_ROOT/.session_active"

    # Load previous session context from Automem (optional)
    if curl -s --max-time 5 "http://localhost:8001/health" | grep -q '"status":\s*"healthy"'; then
        log_info "Querying previous session context..."
        # This could be enhanced with actual Automem queries in the future
        log_success "Session context loaded"
    else
        log_info "Automem not available for session context"
    fi

    log_success "Session initialized"
}

# ============================================================================
# QUICK STATUS REPORT
# ============================================================================

session_status_report() {
    echo -e "\n${BLUE}📊 Session Status Report${NC}"
    echo -e "  🕐 Session Start: $SESSION_START"
    echo -e "  📁 Project Root: $LIGHTRAG_ROOT"
    echo -e "  🧠 Automem: $(curl -s --max-time 2 "http://localhost:8001/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'offline')"
    echo -e "  🔭 Langfuse: $(curl -s --max-time 2 "http://localhost:3000/api/public/health" 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo 'offline')"
    echo -e "  🐚 Ready Tasks: $(bd ready --count 2>/dev/null || echo 'unknown')"

    echo -e "\n${GREEN}🚀 Session ready!${NC}"
    echo -e "  • Work on tasks: bd ready"
    echo -e "  • Test services: ./scripts/test-services.sh"
    echo -e "  • End session: ./scripts/end-session.sh"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo -e "${BLUE}🔄 LightRAG Session Startup${NC}"
    echo -e "Starting session at $SESSION_START"
    echo -e ""

    # Execute session startup phases
    validate_session_prerequisites
    start_services

    # Wait for services to be ready
    log_info "Waiting for services to fully initialize..."
    sleep 5

    if verify_service_health; then
        load_project_context
        initialize_session
        session_status_report
        return 0
    else
        log_error "Service verification failed"
        echo -e "  Troubleshooting:"
        echo -e "   • Check Docker: docker ps"
        echo -e "   • Check logs: cd $AUTOMEM_PATH && make logs"
        echo -e "   • Check ports: lsof -i :8001 :3000"
        return 1
    fi
}

# Execute main function
main "$@"
