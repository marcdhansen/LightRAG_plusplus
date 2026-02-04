#!/bin/bash

# LightRAG Services Manager
# Usage: ./scripts/lightrag-services.sh [start|stop|status|restart]

LIGHTTRAG_DIR="/Users/marchansen/antigravity_lightrag/LightRAG"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check service status
check_status() {
    print_header "LightRAG Services Status"

    echo "🐋 Colima:"
    if colima status >/dev/null 2>&1; then
        echo "  ✅ Running"
    else
        echo "  ❌ Not running"
    fi

    echo ""
    echo "🧠 OpenViking:"
    if curl -sf http://localhost:8002/health >/dev/null 2>&1; then
        echo "  ✅ Running (http://localhost:8002)"
    else
        echo "  ❌ Not running"
    fi

    echo ""
    echo "🐰 Ollama:"
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "  ✅ Running (http://localhost:11434)"
    else
        echo "  ❌ Not running"
    fi
}

# Start services
start_services() {
    print_header "Starting LightRAG Services"

    # Start Colima
    if ! colima status >/dev/null 2>&1; then
        print_status "Starting Colima..."
        colima start
        if [ $? -eq 0 ]; then
            print_status "Colima started successfully"
        else
            print_error "Failed to start Colima"
            exit 1
        fi
    else
        print_status "Colima already running"
    fi

    # Set Docker host for Colima
    if [ -S "$HOME/.colima/docker.sock" ]; then
        export DOCKER_HOST="unix://$HOME/.colima/docker.sock"
        print_status "Docker host set to Colima"
    fi

    # Start OpenViking
    if ! curl -sf http://localhost:8002/health >/dev/null 2>&1; then
        print_status "Starting OpenViking..."
        cd "$LIGHTTRAG_DIR"
        ./openviking/scripts/manage.sh start >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_status "OpenViking started successfully"
        else
            print_error "Failed to start OpenViking"
        fi
    else
        print_status "OpenViking already running"
    fi

    # Start Ollama
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_status "Starting Ollama..."
        ollama serve >/dev/null 2>&1 &
        sleep 3
        print_status "Ollama started"
    else
        print_status "Ollama already running"
    fi

    print_status "All services started!"
    echo ""
    check_status
}

# Stop services
stop_services() {
    print_header "Stopping LightRAG Services"

    print_status "Stopping OpenViking..."
    cd "$LIGHTTRAG_DIR"
    ./openviking/scripts/manage.sh stop >/dev/null 2>&1

    print_status "Stopping Colima..."
    colima stop

    print_status "Services stopped"
}

# Restart services
restart_services() {
    stop_services
    sleep 3
    start_services
}

# Main script logic
case "${1:-status}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        check_status
        ;;
    restart)
        restart_services
        ;;
    *)
        echo "LightRAG Services Manager"
        echo ""
        echo "Usage: $0 [start|stop|status|restart]"
        echo ""
        echo "Commands:"
        echo "  start   - Start all LightRAG services (Colima, OpenViking, Ollama)"
        echo "  stop    - Stop all LightRAG services"
        echo "  status  - Show status of all services"
        echo "  restart - Restart all services"
        echo ""
        echo "Examples:"
        echo "  $0 start    # Start all services"
        echo "  $0 status   # Check current status"
        echo "  $0 stop     # Stop all services"
        exit 1
        ;;
esac
