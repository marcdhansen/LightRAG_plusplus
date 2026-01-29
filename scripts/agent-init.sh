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

# 2. Run PFC
echo -e "\n📋 Running Flight Director Pre-Flight Check..."
python ~/.gemini/antigravity/skills/FlightDirector/scripts/check_flight_readiness.py --pfc

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ PFC FAILED. Check planning documents and Beads state.${NC}"
    exit 1
fi

# 3. Discover Ready Tasks
echo -e "\n🐚 Discovering Ready Tasks (Beads)..."
bd ready

echo -e "\n${GREEN}✅ Bootstrap Complete. You are clear for takeoff.${NC}"
