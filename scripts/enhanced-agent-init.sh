#!/usr/bin/env zsh

# 🚀 Enhanced Agent Init Wrapper (SMP Bootstrapper with Service Orchestration)
# Purpose: Automate Pre-Flight Check, service startup, and comprehensive verification

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AUTOMEM_PATH="${AUTOMEM_PATH:-$HOME/GitHub/verygoodplugins/automem}"
LANGFUSE_PATH="${LANGFUSE_PATH:-$PWD/langfuse_docker}"
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=5
HEALTH_CHECK_TIMEOUT=30

echo -e "${BLUE}🛫 Initiating Enhanced Standard Mission Protocol (SMP) Bootstrap...${NC}"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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
# SERVICE VERIFICATION FUNCTIONS
# ============================================================================

check_port_conflicts() {
    log_step "Checking for port conflicts..."

    local ports=(
        "3000:Langfuse Web UI"
        "3001:Memgraph Web UI"
        "3002:Automem FalkorDB Browser"
        "6379:Langfuse Redis"
        "6380:Automem FalkorDB"
        "8000:OpenViking API"
        "8001:Automem Flask API"
        "9621:LightRAG API"
        "9622:OpenViking LightRAG"
    )

    local conflicts=0

    for port_info in "${ports[@]}"; do
        local port=${port_info%:*}
        local service=${port_info#*:}

        if lsof -i :$port >/dev/null 2>&1; then
            local process=$(lsof -ti:$port | xargs ps -p 2>/dev/null | tail -1 | awk '{print $4}' || echo "unknown")
            echo -e "  ⚠️  Port $port ($service): in use by $process"
            conflicts=$((conflicts + 1))
        else
            echo -e "  ✅ Port $port ($service): available"
        fi
    done

    if [[ $conflicts -gt 0 ]]; then
        log_warning "Port conflicts detected: $conflicts service(s) affected"
        return 1
    else
        log_success "No port conflicts detected"
        return 0
    fi
}

verify_service_health() {
    local service_name=$1
    local health_url=$2
    local expected_field=${3:-"status"}
    local expected_values=${4:-"healthy|OK"}
    local timeout=${5:-$HEALTH_CHECK_TIMEOUT}
    local auth_token=${6:-""}

    echo -e "\n🔍 Verifying ${BLUE}${service_name}${NC} health..."

    local curl_cmd="curl -s --max-time $timeout"
    if [[ -n "$auth_token" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $auth_token'"
    fi

    local response
    local retries=0
    local max_retries=$MAX_RETRY_ATTEMPTS

    while [[ $retries -lt $max_retries ]]; do
        response=$($curl_cmd "$health_url" 2>/dev/null)

        if [[ -n "$response" ]]; then
            # Extract JSON field if response looks like JSON
            if echo "$response" | grep -q '"'"$expected_field"'"'; then
                local status=$(echo "$response" | grep -o "\"${expected_field}\":\s*\"[^\"]*\"" | cut -d'"' -f4)

                if [[ -n "$status" ]]; then
                    if echo "$status" | grep -E "^($expected_values)$" >/dev/null; then
                        log_success "${service_name}: $status"
                        return 0
                    else
                        log_warning "${service_name}: $status (expected: $expected_values)"
                        echo -e "     Full response: $response"
                        return 1
                    fi
                fi
            else
                # Fallback for non-JSON or different format
                if echo "$response" | grep -E "$expected_values" >/dev/null; then
                    log_success "${service_name}: responding"
                    return 0
                fi
            fi
        fi

        retries=$((retries + 1))
        if [[ $retries -lt $max_retries ]]; then
            echo -e "  ⏳ Attempt $((retries + 1))/$max_retries..."
            sleep $RETRY_DELAY
        fi
    done

    log_error "${service_name}: health check failed after $max_retries attempts"
    if [[ -n "$response" ]]; then
        echo -e "     Response: $response"
    else
        echo -e "     No response received"
    fi
    return 1
}

restart_service_if_needed() {
    local service_name=$1
    local container_name=$2
    local health_url=$3
    local max_retries=1

    echo -e "\n🔄 Attempting to restart ${BLUE}${service_name}${NC}..."

    for ((i=1; i<=max_retries; i++)); do
        echo -e "  🔄 Restart attempt $i/$max_retries..."

        # Restart the service
        if docker restart "$container_name" >/dev/null 2>&1; then
            echo -e "  ⏳ Waiting for service to be ready..."
            sleep 10

            # Check if health endpoint responds
            if verify_service_health "$service_name" "$health_url"; then
                log_success "${service_name} recovery successful"
                return 0
            fi
        else
            echo -e "  ❌ Failed to restart container: $container_name"
        fi
    done

    log_error "${service_name} recovery failed after $max_retries attempts"
    return 1
}

# ============================================================================
# SERVICE STARTUP FUNCTIONS
# ============================================================================

start_automem_service() {
    log_step "Starting Automem service..."

    if [[ ! -d "$AUTOMEM_PATH" ]]; then
        log_error "Automem not found at $AUTOMEM_PATH"
        echo -e "     Set AUTOMEM_PATH environment variable or clone repository"
        return 1
    fi

    cd "$AUTOMEM_PATH" || return 1

    # Check if already running
    if docker ps --filter "name=automem-flask-api-1" --filter "status=running" | grep -q automem-flask-api-1; then
        log_info "Automem service already running"
        return 0
    fi

    echo -e "🚀 Starting Automem with 'make dev'..."
    if make dev >/dev/null 2>&1 & then
        local make_pid=$!
        echo -e "⏳ Waiting for Automem service to initialize..."

        # Wait for containers to start
        local wait_time=0
        local max_wait=60

        while [[ $wait_time -lt $max_wait ]]; do
            if docker ps --filter "name=automem-flask-api-1" --filter "status=running" | grep -q automem-flask-api-1; then
                log_success "Automem service started successfully"
                wait $make_pid >/dev/null 2>&1
                return 0
            fi
            sleep 2
            wait_time=$((wait_time + 2))
            echo -n "."
        done

        echo -e "\n"
        kill $make_pid >/dev/null 2>&1
        log_error "Automem service failed to start within $max_wait seconds"
        return 1
    else
        log_error "Failed to start Automem service"
        return 1
    fi
}

start_langfuse_service() {
    log_step "Starting Langfuse service..."

    if [[ ! -d "$LANGFUSE_PATH" ]]; then
        log_error "Langfuse Docker configuration not found at $LANGFUSE_PATH"
        return 1
    fi

    cd "$LANGFUSE_PATH" || return 1

    # Check if already running
    if docker ps --filter "name=langfuse_docker-langfuse-web-1" --filter "status=running" | grep -q langfuse_docker-langfuse-web-1; then
        log_info "Langfuse service already running"
        return 0
    fi

    echo -e "🚀 Starting Langfuse with Docker Compose..."
    if docker-compose up -d >/dev/null 2>&1; then
        echo -e "⏳ Waiting for Langfuse service to initialize..."

        # Wait for containers to start
        local wait_time=0
        local max_wait=90  # Langfuse takes longer to initialize

        while [[ $wait_time -lt $max_wait ]]; do
            if docker ps --filter "name=langfuse_docker-langfuse-web-1" --filter "status=running" | grep -q langfuse_docker-langfuse-web-1; then
                log_success "Langfuse service started successfully"
                return 0
            fi
            sleep 3
            wait_time=$((wait_time + 3))
            echo -n "."
        done

        echo -e "\n"
        log_error "Langfuse service failed to start within $max_wait seconds"
        return 1
    else
        log_error "Failed to start Langfuse service"
        return 1
    fi
}

# ============================================================================
# INTEGRATION TESTING
# ============================================================================

verify_automem_integration() {
    log_step "Testing Automem API integration..."

    # Test health endpoint first
    if ! verify_service_health "Automem" "http://localhost:8001/health" "status" "healthy"; then
        log_error "Automem health check failed"
        return 1
    fi

    # Test authenticated API operations
    local api_token="${AUTOMEM_API_TOKEN:-test-token}"
    echo -e "\n🔐 Testing authenticated API operations..."

    # Test memory storage
    local test_content="Bootstrap integration test at $(date)"
    local test_memory_response=$(curl -s -H "Authorization: Bearer $api_token" \
                           -X POST \
                           -H "Content-Type: application/json" \
                           -d "{\"content\": \"$test_content\", \"tags\": [\"bootstrap-test\"]}" \
                           "http://localhost:8001/memory" 2>/dev/null)

    if echo "$test_memory_response" | grep -E '"status":\s*"success"' >/dev/null; then
        log_success "Memory storage test passed"

        # Extract memory ID for retrieval test
        local memory_id=$(echo "$test_memory_response" | grep -o '"id":\s*"[^"]*"' | cut -d'"' -f4)

        if [[ -n "$memory_id" ]]; then
            # Test memory retrieval
            echo -e "🔍 Testing memory retrieval..."
            local recall_response=$(curl -s -H "Authorization: Bearer $api_token" \
                                 -G -d "query=bootstrap test" \
                                 "http://localhost:8001/recall" 2>/dev/null)

            if echo "$recall_response" | grep -E '"status":\s*"success"' >/dev/null && \
               echo "$recall_response" | grep -q "$memory_id"; then
                log_success "Memory retrieval test passed"
            else
                log_warning "Memory retrieval test failed"
                echo -e "     Response: $recall_response"
            fi

            # Cleanup test memory
            echo -e "🧹 Cleaning up test memory..."
            curl -s -H "Authorization: Bearer $api_token" \
                 -X DELETE \
                 "http://localhost:8001/memory/$memory_id" >/dev/null
        else
            log_warning "Could not extract memory ID from storage response"
        fi

        return 0
    else
        log_error "Memory storage test failed"
        echo -e "     Response: $test_memory_response"
        return 1
    fi
}

verify_langfuse_integration() {
    log_step "Testing Langfuse integration..."

    if ! verify_service_health "Langfuse" "http://localhost:3000/api/public/health" "status" "OK"; then
        log_error "Langfuse health check failed"
        return 1
    fi

    # Test web UI accessibility
    local web_response=$(curl -s --max-time 5 "http://localhost:3000" 2>/dev/null)
    if echo "$web_response" | grep -q "Langfuse\|langfuse"; then
        log_success "Langfuse web UI accessible"
        return 0
    else
        log_warning "Langfuse web UI may not be fully loaded"
        return 1
    fi
}

verify_openviking_integration() {
    log_step "Testing OpenViking API integration..."

    # Test main API health
    if ! verify_service_health "OpenViking API" "http://localhost:8000/health" "status" "healthy"; then
        log_error "OpenViking API health check failed"
        return 1
    fi

    # Test LightRAG component health
    if ! verify_service_health "OpenViking LightRAG" "http://localhost:9622/health" "status" "healthy"; then
        log_warning "OpenViking LightRAG health check failed (optional component)"
    fi

    # Test slash command integration (Phase 0 check)
    echo -e "🔍 Testing slash command discovery..."

    # 1. API check
    local cmd_response=$(curl -s http://localhost:8000/commands 2>/dev/null)
    if echo "$cmd_response" | grep -q '"count":'; then
        local cmd_count=$(echo "$cmd_response" | grep -o '"count":\s*[0-9]*' | grep -o '[0-9]*')
        log_success "OpenViking slash commands discovered (API): $cmd_count"
    else
        log_warning "OpenViking API slash commands endpoint not responding"
    fi

    # 2. Local file sync (Integration fix)
    echo -e "🔄 Synchronizing local slash commands..."
    if python3 openviking/commands.py --sync .agent/workflows >/dev/null 2>&1; then
        local local_count=$(ls .agent/workflows/*.md 2>/dev/null | wc -l | xargs)
        log_success "Synced $local_count OpenViking commands to .agent/workflows/"
        return 0
    else
        log_error "Failed to synchronize local slash commands"
        return 1
    fi
}

# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

validate_environment() {
    log_step "Validating development environment..."

    local errors=0

    # Check required tools
    local tools=("docker" "docker-compose" "make" "curl" "lsof" "git" "python" "uv" "bd")
    for tool in "${tools[@]}"; do
        if ! command -v $tool >/dev/null 2>&1; then
            log_error "Missing required tool: $tool"
            errors=$((errors + 1))
        else
            echo -e "  ✅ $tool: $(which $tool)"
        fi
    done

    # Check Docker Desktop is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker Desktop is not running"
        errors=$((errors + 1))
    else
        log_success "Docker Desktop is running"
    fi

    # Check required paths
    if [[ ! -d "$AUTOMEM_PATH" ]]; then
        log_error "Automem path not found: $AUTOMEM_PATH"
        errors=$((errors + 1))
    else
        log_success "Automem path found: $AUTOMEM_PATH"
    fi

    if [[ ! -d "$LANGFUSE_PATH" ]]; then
        log_error "Langfuse path not found: $LANGFUSE_PATH"
        errors=$((errors + 1))
    else
        log_success "Langfuse path found: $LANGFUSE_PATH"
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Environment validation failed with $errors errors"
        return 1
    else
        log_success "Environment validation passed"
        return 0
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    local errors=0

    # 1. Environment validation
    if ! validate_environment; then
        log_error "Environment validation failed. Please fix issues before proceeding."
        exit 1
    fi

    # 2. Port conflict detection
    if ! check_port_conflicts; then
        log_warning "Port conflicts detected. Services may have startup issues."
        echo -e "     Continue anyway? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # 3. Start services
    if ! start_automem_service; then
        log_error "Failed to start Automem service"
        errors=$((errors + 1))

        # Try recovery
        if ! restart_service_if_needed "Automem" "automem-flask-api-1" "http://localhost:8001/health"; then
            errors=$((errors + 1))
        fi
    fi

    if ! start_langfuse_service; then
        log_error "Failed to start Langfuse service"
        errors=$((errors + 1))

        # Try recovery
        if ! restart_service_if_needed "Langfuse" "langfuse_docker-langfuse-web-1" "http://localhost:3000/api/public/health"; then
            errors=$((errors + 1))
        fi
    fi

    # 4. Integration testing
    if ! verify_automem_integration; then
        log_error "Automem integration testing failed"
        errors=$((errors + 1))
    fi

    if ! verify_langfuse_integration; then
        log_error "Langfuse integration testing failed"
        errors=$((errors + 1))
    fi

    # Check OpenViking if enabled
    if [[ -n "$OPENVIKING_ENABLED" || "$1" == "--openviking" ]]; then
        if ! verify_openviking_integration; then
            log_error "OpenViking integration testing failed"
            errors=$((errors + 1))
        fi
    fi

    # 5. Run original PFC and task discovery
    echo -e "\n${BLUE}📋 Running Flight Director Pre-Flight Check...${NC}"
    python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc

    if [[ $? -ne 0 ]]; then
        log_error "PFC FAILED. Check planning documents and Beads state."
        exit 1
    fi

    echo -e "\n${BLUE}🐚 Discovering Ready Tasks (Beads)...${NC}"
    bd ready

    # 6. Final summary
    echo -e "\n${BLUE}📊 Enhanced Bootstrap Summary${NC}"
    if [[ $errors -eq 0 ]]; then
        log_success "All services started and verified successfully"
        log_success "Agent environment ready for takeoff"
        echo -e "\n🚀 You are clear for takeoff!"
        return 0
    else
        log_error "Bootstrap completed with $errors error(s)"
        echo -e "\n🔧 Please check service logs and configuration"
        echo -e "   Automem logs: cd $AUTOMEM_PATH && make logs"
        echo -e "   Langfuse logs: cd $LANGFUSE_PATH && docker-compose logs"
        return 1
    fi
}

# Execute main function
main "$@"
