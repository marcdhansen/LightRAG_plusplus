#!/usr/bin/env zsh

# 🚀 Agent Init Wrapper (SMP Bootstrapper)
# Purpose: Automate the Pre-Flight Check and Task Discovery for session starts.

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Enable OpenViking by default (SMP deprecated)
export OPENVIKING_ENABLED=1
echo -e "${BLUE}🧠 OpenViking enabled by default (SMP replaced)${NC}"

# Set up Docker for Colima (lightweight alternative to Docker Desktop)
if [ -S "$HOME/.colima/docker.sock" ]; then
    export DOCKER_HOST="unix://$HOME/.colima/docker.sock"
    echo -e "${BLUE}🐳 Using Colima Docker runtime (lightweight)${NC}"
fi

# Verify Ollama is running
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama not detected - starting Ollama...${NC}"
    ollama serve &
    sleep 5
fi

echo -e "${BLUE}🛫 Initiating OpenViking Bootstrap (SMP deprecated)...${NC}"

# 1. Verify environment
echo -e "\n🔍 Checking Toolchain..."
for tool in bd uv python git docker; do
    if which $tool > /dev/null; then
        echo -e "  ✅ $tool: $(which $tool)"
    else
        echo -e "  ❌ $tool: NOT FOUND"
        EXIT_CODE=1
    fi
done

# Check Docker daemon specifically
if ! docker info >/dev/null 2>&1; then
    echo -e "  ❌ Docker daemon not running"
    echo -e "     Please start Docker Desktop and retry"
    EXIT_CODE=1
else
    echo -e "  ✅ Docker daemon running"
fi

if [ "$EXIT_CODE" = "1" ]; then
    echo -e "${RED}🛑 Missing required tools. Please fix before proceeding.${NC}"
    exit 1
fi

# 2. Check for Active Agents
echo -e "\n👥 Checking Agent Status..."
./scripts/agent-status.sh

# 3. Session Registration
echo -e "\n🔐 Session Registration..."
if [[ -n "$ZSH_VERSION" ]]; then
    read "TASK_ID?Enter Task ID (e.g., lightrag-123) [unknown]: "
    read "TASK_DESC?Enter brief work description [unknown]: "
else
    read -p "Enter Task ID (e.g., lightrag-123) [unknown]: " TASK_ID
    read -p "Enter brief work description [unknown]: " TASK_DESC
fi

TASK_ID=${TASK_ID:-unknown}
TASK_DESC=${TASK_DESC:-unknown}

./scripts/agent-start.sh --task-id "$TASK_ID" --task-desc "$TASK_DESC"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Session registration failed.${NC}"
    exit 1
fi

# 4. Run OpenViking Pre-Flight Check
echo -e "\n📋 Running OpenViking Pre-Flight Check..."
# TODO: Replace with OpenViking PFC API when available
echo -e "  ⚠️  OpenViking PFC not yet implemented - skipping validation"

# For now, just check basic prerequisites
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "  ❌ Ollama not running - required for OpenViking"
    exit 1
fi

# 5. Discover Ready Tasks
echo -e "\n🐚 Discovering Ready Tasks (Beads)..."
if command -v bd >/dev/null 2>&1; then
    bd ready
else
    echo -e "  ⚠️  Beads not available - task discovery disabled"
fi

# 6. Start OpenViking Services (MANDATORY)
echo -e "\n🚀 Starting OpenViking services (MANDATORY)..."
if ./openviking/scripts/manage.sh start >/dev/null 2>&1; then
    echo -e "  ✅ OpenViking services started successfully"

    # Verify OpenViking health
    if curl -sf http://localhost:8002/health >/dev/null 2>&1; then
        echo -e "  ✅ OpenViking API healthy (port 8002)"
    else
        echo -e "  ❌ OpenViking API not responding. Memory is MANDATORY."
        exit 1
    fi

    # Sync OpenViking commands for local workflows
    if python3 openviking/commands.py --sync .agent/workflows >/dev/null 2>&1; then
        echo -e "  ✅ OpenViking commands synced to .agent/workflows/"
    else
        echo -e "  ⚠️  Failed to sync OpenViking commands"
    fi
else
    echo -e "  ❌ Failed to start OpenViking services. Memory is MANDATORY."
    echo -e "     Run manually: ./openviking/scripts/manage.sh start"
    exit 1
fi

echo -e "\n${GREEN}✅ OpenViking Bootstrap Complete. You are clear for takeoff.${NC}"
echo -e "${BLUE}💡 Use OpenViking API at http://localhost:8002 for enhanced capabilities${NC}"
