#!/usr/bin/env zsh

# 🚀 LightRAG One-Time Setup Script
# Purpose: First-time environment setup for new agents/IDEs
# Usage: Run once per new development environment

set -e  # Exit on any error

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LIGHTRAG_ROOT="$PWD"
AUTOMEM_PATH="${AUTOMEM_PATH:-$HOME/GitHub/verygoodplugins/automem}"

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
# ONE-TIME GLOBAL SETUP
# ============================================================================

setup_global_tools() {
    log_step "Installing Global Tools"

    local tools_missing=()

    # Check for Docker Desktop
    if ! command -v docker >/dev/null 2>&1; then
        tools_missing+=("docker")
        echo -e "  📋 Install Docker Desktop from https://docker.com/"
    else
        echo -e "  ✅ Docker: $(which docker)"
    fi

    # Check for uv
    if ! command -v uv >/dev/null 2>&1; then
        tools_missing+=("uv")
        echo -e "  📋 Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    else
        echo -e "  ✅ uv: $(which uv)"
    fi

    # Check for git
    if ! command -v git >/dev/null 2>&1; then
        tools_missing+=("git")
        echo -e "  📋 Install git: xcode-select --install (macOS) or brew install git"
    else
        echo -e "  ✅ git: $(which git)"
    fi

    # Check for bd (Beads CLI)
    if ! command -v bd >/dev/null 2>&1; then
        tools_missing+=("bd")
        echo -e "  📋 Install bd: bd onboard"
    else
        echo -e "  ✅ bd: $(which bd)"
    fi

    if [[ ${#tools_missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${tools_missing[*]}"
        echo -e "\nPlease install missing tools and run this script again."
        exit 1
    fi

    log_success "All global tools installed"
}

setup_global_memory() {
    log_step "Setting Up Global Memory System"

    # Initialize Beads if not already done
    if [[ ! -d ~/.beads ]]; then
        log_info "Initializing Beads..."
        bd init
        log_success "Beads initialized"
    else
        log_info "Beads already initialized"
    fi

    # Read global configuration
    if [[ -f ~/.gemini/GEMINI.md ]]; then
        log_info "Global Agent Rules found at ~/.gemini/GEMINI.md"
    else
        log_warning "Global Agent Rules not found at ~/.gemini/GEMINI.md"
    fi

    if [[ -f ~/.gemini/GLOBAL_INDEX.md ]]; then
        log_info "Global Index found at ~/.gemini/GLOBAL_INDEX.md"
    else
        log_warning "Global Index not found at ~/.gemini/GLOBAL_INDEX.md"
    fi
}

# ============================================================================
# PROJECT-SPECIFIC ONE-TIME SETUP
# ============================================================================

setup_project_environment() {
    log_step "Setting Up Project Environment"

    # Check if we're in LightRAG directory
    if [[ ! -f "$LIGHTRAG_ROOT/pyproject.toml" ]] || [[ ! -d "$LIGHTRAG_ROOT/.git" ]]; then
        log_error "Not in LightRAG project directory"
        echo -e "  Please run this script from the LightRAG repository root"
        exit 1
    fi

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    if [[ -f "$LIGHTRAG_ROOT/pyproject.toml" ]]; then
        cd "$LIGHTRAG_ROOT"
        uv sync
        log_success "Dependencies installed"
    else
        log_error "pyproject.toml not found"
        exit 1
    fi

    # Create environment file if missing
    if [[ ! -f "$LIGHTRAG_ROOT/.env" ]]; then
        if [[ -f "$LIGHTRAG_ROOT/.env.example" ]]; then
            log_info "Creating .env from template..."
            cp "$LIGHTRAG_ROOT/.env.example" "$LIGHTRAG_ROOT/.env"
            log_warning "Please edit .env with your configuration"
        else
            log_warning "No .env.example found, creating basic .env..."
            cat > "$LIGHTRAG_ROOT/.env" << EOF
# LightRAG Environment Configuration
AUTOMEM_API_TOKEN=test-token
ADMIN_API_TOKEN=test-admin-token
OPENAI_API_KEY=your-openai-key-here
EOF
        fi
    else
        log_info ".env file already exists"
    fi
}

setup_automem_repository() {
    log_step "Setting Up Automem Repository"

    if [[ ! -d "$AUTOMEM_PATH" ]]; then
        log_info "Cloning Automem repository..."
        git clone https://github.com/verygoodplugins/automem.git "$AUTOMEM_PATH"
        log_success "Automem repository cloned"
    else
        log_info "Automem repository already exists"
    fi

    # Create Automem environment file if missing
    if [[ ! -f "$AUTOMEM_PATH/.env" ]]; then
        log_info "Creating Automem environment file..."
        cat > "$AUTOMEM_PATH/.env" << EOF
# Automem Environment Configuration
AUTOMEM_API_TOKEN=test-token
ADMIN_API_TOKEN=test-admin-token
OPENAI_API_KEY=
EMBEDDING_PROVIDER=auto
EOF
        log_success "Automem environment created"
    else
        log_info "Automem environment already exists"
    fi
}

# ============================================================================
# FIRST-TIME SERVICE INITIALIZATION
# ============================================================================

initialize_services() {
    log_step "Initializing Services for First Time"

    # Start Automem for first time (creates databases)
    if [[ -d "$AUTOMEM_PATH" ]]; then
        log_info "Starting Automem for first-time initialization..."
        cd "$AUTOMEM_PATH"
        timeout 120 make dev >/dev/null 2>&1 || {
            log_warning "Automem first-time startup timed out (expected)"
        }

        # Wait a moment for containers to initialize
        sleep 10

        # Check if containers started
        if docker ps --filter "name=automem" --filter "status=running" | grep -q automem; then
            log_success "Automem services initialized"

            # Stop them after initialization (user will start them per session)
            log_info "Stopping services (they will be started per session)..."
            make down >/dev/null 2>&1
        else
            log_warning "Automem initialization may have failed"
        fi
    fi

    # Start Langfuse for first time (creates databases)
    if [[ -d "$LIGHTRAG_ROOT/langfuse_docker" ]]; then
        log_info "Starting Langfuse for first-time initialization..."
        cd "$LIGHTRAG_ROOT/langfuse_docker"
        timeout 180 docker-compose up -d >/dev/null 2>&1 || {
            log_warning "Langfuse first-time startup timed out (expected)"
        }

        # Wait for services to initialize
        sleep 15

        # Check if containers started
        if docker ps --filter "name=langfuse" --filter "status=running" | grep -q langfuse; then
            log_success "Langfuse services initialized"

            # Stop them after initialization
            log_info "Stopping services (they will be started per session)..."
            docker-compose down >/dev/null 2>&1
        else
            log_warning "Langfuse initialization may have failed"
        fi
    fi
}

# ============================================================================
# FINAL VALIDATION
# ============================================================================

validate_setup() {
    log_step "Validating One-Time Setup"

    local validation_errors=0

    # Validate toolchain
    local tools=("docker" "uv" "git" "bd")
    for tool in "${tools[@]}"; do
        if ! command -v $tool >/dev/null 2>&1; then
            log_error "Tool not found: $tool"
            validation_errors=$((validation_errors + 1))
        fi
    done

    # Validate project structure
    if [[ ! -f "$LIGHTRAG_ROOT/pyproject.toml" ]]; then
        log_error "Project pyproject.toml not found"
        validation_errors=$((validation_errors + 1))
    fi

    if [[ ! -d "$LIGHTRAG_ROOT/.venv" ]]; then
        log_error "Python virtual environment not found"
        validation_errors=$((validation_errors + 1))
    fi

    if [[ ! -f "$LIGHTRAG_ROOT/.env" ]]; then
        log_error "Environment file not found"
        validation_errors=$((validation_errors + 1))
    fi

    # Validate Automem setup
    if [[ ! -d "$AUTOMEM_PATH" ]]; then
        log_error "Automem repository not found"
        validation_errors=$((validation_errors + 1))
    fi

    if [[ $validation_errors -eq 0 ]]; then
        log_success "One-time setup validation passed"
        return 0
    else
        log_error "Setup validation failed with $validation_errors errors"
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo -e "${BLUE}🚀 LightRAG One-Time Setup${NC}"
    echo -e "This script performs first-time setup for new agents/IDEs"
    echo -e ""

    # Check if this is first-time setup
    if [[ -f "$LIGHTRAG_ROOT/.setup_complete" ]]; then
        log_warning "One-time setup already completed"
        echo -e "   To re-run setup: rm .setup_complete"
        echo -e "   For session startup: ./scripts/start-session.sh"
        exit 0
    fi

    # Execute setup phases
    setup_global_tools
    setup_global_memory
    setup_project_environment
    setup_automem_repository
    initialize_services

    # Final validation
    if validate_setup; then
        # Mark setup as complete
        touch "$LIGHTRAG_ROOT/.setup_complete"
        log_success "One-time setup completed successfully"

        echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
        echo -e "  Next steps:"
        echo -e "  • For session startup: ./scripts/start-session.sh"
        echo -e "  • Read documentation: .agent/SESSION.md"
        echo -e "  • Quick reference: .agent/QUICK_START.md"
        return 0
    else
        log_error "Setup validation failed"
        echo -e "  Please resolve errors and re-run this script"
        return 1
    fi
}

# Execute main function
main "$@"
