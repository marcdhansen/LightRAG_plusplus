#!/bin/bash
# OpenViking Docker Environment Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Help function
show_help() {
    cat << EOF
OpenViking Docker Environment Manager

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start           Start OpenViking experimental environment
    stop            Stop OpenViking services
    migrate         Run data migration from SMP to OpenViking
    compare         Run A/B performance comparison
    status          Show service status
    logs            Show service logs
    clean           Clean up Docker resources
    help            Show this help message

Environment Variables:
    OPENAI_API_KEY           OpenAI API key for embeddings/VLM
    OPENVIKING_PROFILE       Profile to use (default: experimental)
    LOG_LEVEL                Logging level (default: INFO)

Examples:
    $0 start                    # Start experimental environment
    $0 migrate                   # Run migration only
    $0 compare                   # Run performance comparison
    $0 logs openviking-server      # Show specific service logs
    $0 clean                     # Clean all resources

EOF
}

# Check required environment variables
check_env() {
    # Check if we're using local Ollama or OpenAI
    if [[ -f "./openviking/config/ov-local.conf" ]]; then
        print_status "Using local Ollama configuration"
        # Check if Ollama is running
        if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
            print_warning "Ollama not running. Start with: ollama serve"
            return 1
        fi
    elif [[ -z "$OPENAI_API_KEY" ]]; then
        print_warning "OPENAI_API_KEY not set. Set it or create .env file"
        print_warning "Example: export OPENAI_API_KEY=sk-..."
        return 1
    fi
    return 0
}

# Start OpenViking experimental environment
start_services() {
    print_header "Starting OpenViking Experimental Environment"
    
    check_env || exit 1
    
    print_status "Starting OpenViking server and Redis..."
    docker-compose -f docker-compose.openviking.yml up -d openviking-server openviking-redis
    
    print_status "Waiting for OpenViking to be healthy..."
    timeout 120 bash -c 'until curl -f http://localhost:8000/health 2>/dev/null; do sleep 2; done' || {
        print_error "OpenViking failed to start within 2 minutes"
        docker-compose -f docker-compose.openviking.yml logs openviking-server
        exit 1
    }
    
    print_status "Starting experimental LightRAG with OpenViking integration..."
    docker-compose -f docker-compose.openviking.yml --profile experimental up -d lightrag-experimental
    
    print_status "Starting main LightRAG for comparison..."
    docker-compose -f docker-compose.yml --profile main up -d lightrag-main
    
    print_status "Services started successfully!"
    echo ""
    print_status "OpenViking API: http://localhost:8000"
    print_status "Experimental LightRAG: http://localhost:9622"
    print_status "Main LightRAG: http://localhost:9621"
    echo ""
    print_status "Use '$0 compare' to run A/B performance tests"
}

# Stop services
stop_services() {
    print_header "Stopping OpenViking Services"
    
    print_status "Stopping experimental environment..."
    docker-compose -f docker-compose.openviking.yml --profile experimental down
    
    print_status "Stopping main environment..."
    docker-compose -f docker-compose.yml --profile main down
    
    print_status "Stopping OpenViking server..."
    docker-compose -f docker-compose.openviking.yml down openviking-server openviking-redis
    
    print_status "All services stopped"
}

# Run migration
run_migration() {
    print_header "Running SMP to OpenViking Migration"
    
    check_env || exit 1
    
    print_status "Starting OpenViking server for migration..."
    docker-compose -f docker-compose.openviking.yml up -d openviking-server openviking-redis
    
    print_status "Waiting for OpenViking to be healthy..."
    timeout 120 bash -c 'until curl -f http://localhost:8000/health 2>/dev/null; do sleep 2; done' || {
        print_error "OpenViking failed to start"
        exit 1
    }
    
    print_status "Running migration..."
    docker-compose -f docker-compose.openviking.yml --profile migration up --build openviking-migration
    
    print_status "Migration completed. Check logs for details."
}

# Run performance comparison
run_comparison() {
    print_header "Running A/B Performance Comparison"
    
    print_status "Ensuring both environments are running..."
    docker-compose -f docker-compose.openviking.yml --profile experimental up -d lightrag-experimental
    docker-compose -f docker-compose.yml --profile main up -d lightrag-main
    
    print_status "Starting comparison tests..."
    docker-compose -f docker-compose.openviking.yml --profile comparison up --build performance-comparison
    
    print_status "Comparison running. Results will be saved to volume 'comparison_results'"
    print_status "Use '$0 logs performance-comparison' to monitor progress"
}

# Show service status
show_status() {
    print_header "Service Status"
    
    echo "OpenViking Experimental Services:"
    docker-compose -f docker-compose.openviking.yml ps
    
    echo ""
    echo "Main LightRAG Services:"
    docker-compose -f docker-compose.yml ps
}

# Show logs
show_logs() {
    local service="$1"
    
    if [[ -z "$service" ]]; then
        print_error "Please specify a service name"
        echo "Available services: openviking-server, lightrag-experimental, performance-comparison"
        exit 1
    fi
    
    print_header "Showing logs for $service"
    docker-compose -f docker-compose.openviking.yml logs -f "$service"
}

# Clean up resources
clean_resources() {
    print_header "Cleaning OpenViking Resources"
    
    read -p "This will remove all OpenViking containers, volumes, and images. Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping and removing containers..."
        docker-compose -f docker-compose.openviking.yml down -v --remove-orphans
        
        print_status "Removing Docker images..."
        docker rmi lightrag-openviking openviking-migration lightrag-performance-comparison 2>/dev/null || true
        
        print_status "Removing unused volumes..."
        docker volume prune -f
        
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    migrate)
        run_migration
        ;;
    compare)
        run_comparison
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    clean)
        clean_resources
        ;;
    help|*)
        show_help
        ;;
esac