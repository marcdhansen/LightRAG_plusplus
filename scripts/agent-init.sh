#!/usr/bin/env zsh

# 🚀 Agent Init Wrapper (SMP Bootstrapper)
# Purpose: Automate the Pre-Flight Check and Task Discovery for session starts.

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛫 Initiating Standard Mission Protocol (SMP) Bootstrap...${NC}"

# 1. Verify environment
echo -e "\n🔍 Checking Toolchain..."
for tool in bd uv python git; do
    if which $tool > /dev/null; then
        echo -e "  ✅ $tool: $(which $tool)"
    else
        echo -e "  ❌ $tool: NOT FOUND"
        EXIT_CODE=1
    fi
done

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

# 4. Run PFC
echo -e "\n📋 Running Flight Director Pre-Flight Check..."
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ PFC FAILED. Check planning documents and Beads state.${NC}"
    exit 1
fi

# 5. Discover Ready Tasks
echo -e "\n🐚 Discovering Ready Tasks (Beads)..."
bd ready

echo -e "\n${GREEN}✅ Bootstrap Complete. You are clear for takeoff.${NC}"
