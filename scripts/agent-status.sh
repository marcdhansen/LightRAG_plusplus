#!/bin/bash
#
# Agent Status Script
# Shows current active agents and their status
#

set -e

# Configuration
LOCKS_DIR=".agent/session_locks"
STALE_THRESHOLD=600  # 10 minutes in seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to parse JSON field (simple grep-based)
get_json_field() {
    local file="$1"
    local field="$2"
    grep "\"${field}\":" "$file" | sed 's/.*: "\([^"]*\)".*/\1/' | head -1
}

# Function to get integer field
get_json_int() {
    local file="$1"
    local field="$2"
    grep "\"${field}\":" "$file" | sed 's/.*: \([0-9]*\).*/\1/' | head -1
}

# Function to check if lock is stale
is_lock_stale() {
    local lock_file="$1"
    local now=$(date +%s)
    local last_heartbeat=$(get_json_field "$lock_file" "last_heartbeat")

    # Parse timestamp to epoch
    local hb_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_heartbeat" +%s 2>/dev/null || echo "0")

    local age=$((now - hb_epoch))

    if [ $age -gt $STALE_THRESHOLD ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to format duration
format_duration() {
    local seconds=$1
    local mins=$((seconds / 60))
    local hours=$((mins / 60))
    local days=$((hours / 24))

    if [ $days -gt 0 ]; then
        echo "${days}d ${hours}h ${mins}m"
    elif [ $hours -gt 0 ]; then
        echo "${hours}h ${mins}m"
    else
        echo "${mins}m"
    fi
}

# Function to display agent info
display_agent() {
    local lock_file="$1"
    local status="$2"

    local agent_name=$(get_json_field "$lock_file" "agent_name")
    local agent_id=$(get_json_field "$lock_file" "agent_id")
    local task=$(get_json_field "$lock_file" "current_task")
    local task_desc=$(get_json_field "$lock_file" "task_description")
    local started=$(get_json_field "$lock_file" "started_at")
    local last_hb=$(get_json_field "$lock_file" "last_heartbeat")
    local pid=$(get_json_int "$lock_file" "pid")

    # Calculate durations
    local start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$started" +%s 2>/dev/null || echo "0")
    local hb_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_hb" +%s 2>/dev/null || echo "0")
    local now=$(date +%s)

    local session_duration=$((now - start_epoch))
    local last_seen=$((now - hb_epoch))

    # Status color
    if [ "$status" = "stale" ]; then
        printf "${RED}⚠️  STALE${NC}"
    else
        printf "${GREEN}🟢 ACTIVE${NC}"
    fi

    echo "  Agent: ${agent_name}"
    echo "     ID: ${agent_id}"
    echo "     Task: ${task}"
    if [ "$task_desc" != "unknown" ]; then
        echo "     Description: ${task_desc}"
    fi
    echo "     Session Duration: $(format_duration $session_duration)"
    echo "     Last Heartbeat: $(format_duration $last_seen) ago"
    echo "     Started: ${started}"
    echo "     PID: ${pid}"
    echo "     Lock File: $(basename "$lock_file")"
    echo ""
}

# Main execution
echo "👥 Agent Status Dashboard"
echo "========================"
echo ""

# Check if locks directory exists
if [ ! -d "$LOCKS_DIR" ]; then
    echo "No session locks directory found."
    echo "Run './scripts/agent-start.sh' to create a session lock."
    exit 0
fi

# Count locks
lock_count=0
active_count=0
stale_count=0

# First pass: count and categorize
for lock in "${LOCKS_DIR}"/*.json; do
    [ -e "$lock" ] || continue
    lock_count=$((lock_count + 1))

    if [ "$(is_lock_stale "$lock")" = "true" ]; then
        stale_count=$((stale_count + 1))
    else
        active_count=$((active_count + 1))
    fi
done

# Show summary
echo "Summary: ${lock_count} total lock(s)"
if [ $active_count -gt 0 ]; then
    echo -e "  ${GREEN}${active_count} active${NC}"
fi
if [ $stale_count -gt 0 ]; then
    echo -e "  ${RED}${stale_count} stale${NC}"
fi
echo ""

# Display active agents first
if [ $active_count -gt 0 ]; then
    echo "🟢 Active Agents"
    echo "----------------"
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue
        if [ "$(is_lock_stale "$lock")" = "false" ]; then
            display_agent "$lock" "active"
        fi
    done
fi

# Display stale agents
if [ $stale_count -gt 0 ]; then
    echo "⚠️  Stale Agents (No heartbeat > 10 minutes)"
    echo "--------------------------------------------"
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue
        if [ "$(is_lock_stale "$lock")" = "true" ]; then
            display_agent "$lock" "stale"
        fi
    done
    echo ""
    echo "💡 Stale locks can be cleaned up with:"
    echo "   find ${LOCKS_DIR} -name '*.json' -mtime +1 -delete"
fi

# If no locks found
if [ $lock_count -eq 0 ]; then
    echo "${YELLOW}No active agent sessions found.${NC}"
    echo ""
    echo "💡 To start a new session:"
    echo "   ./scripts/agent-start.sh --task-id <issue-id> --task-desc 'description'"
fi

echo ""
echo "💡 Tips:"
echo "   - Run this command anytime to check agent activity"
echo "   - Stale locks (>10 min) may indicate crashed sessions"
echo "   - Each agent should update heartbeat every 5 minutes"
