#!/bin/bash
#
# Enhanced Session Heartbeat with SOP Compliance Integration
# Extends agent-heartbeat.sh to include SOP compliance monitoring
# This script should be called periodically (e.g., every 5 minutes) during active sessions
#

set -e

# Configuration
LOCKS_DIR=".agent/session_locks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOP_MONITOR_SCRIPT="$SCRIPT_DIR/realtime_sop_monitor.py"
COMPLIANCE_CACHE="$SCRIPT_DIR/../cache/compliance_cache.json"

# Get agent info
AGENT_ID="${OPENCODE_AGENT_ID:-unknown}"
SESSION_ID="${OPENCODE_SESSION_ID:-$(date +%s)}"

# Ensure cache directory exists
mkdir -p "$(dirname "$COMPLIANCE_CACHE")"

# Function to find lock file
find_lock_file() {
    # First, check if AGENT_LOCK_FILE is set and exists
    if [ -n "$AGENT_LOCK_FILE" ] && [ -f "$AGENT_LOCK_FILE" ]; then
        echo "$AGENT_LOCK_FILE"
        return 0
    fi

    # Otherwise, search for lock file matching agent and session
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue

        if [[ "$(basename "$lock")" == *"${AGENT_ID}"* ]] && [[ "$(basename "$lock")" == *"${SESSION_ID}"* ]]; then
            echo "$lock"
            return 0
        fi
    done

    return 1
}

# Function to update heartbeat with compliance data
update_heartbeat_with_compliance() {
    local lock_file="$1"
    local new_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local compliance_data=""
    local monitoring_active="false"
    local compliance_percentage="unknown"
    local recent_violations="unknown"

    # Check if SOP monitor is available and running
    if [ -f "$SOP_MONITOR_SCRIPT" ]; then
        # Get compliance status from monitor
        if python3 "$SOP_MONITOR_SCRIPT" --status > /tmp/sop_status_$$ 2>/dev/null; then
            compliance_data=$(cat /tmp/sop_status_$$ 2>/dev/null || echo "{}")
            
            # Extract key metrics (using python for JSON parsing)
            if command -v python3 >/dev/null 2>&1; then
                monitoring_active=$(echo "$compliance_data" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('monitoring_active', False))
except:
    print('false')
" 2>/dev/null || echo "false")

                recent_violations=$(echo "$compliance_data" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('recent_violations', 0))
except:
    print('0')
" 2>/dev/null || echo "0")
            fi
            
            rm -f /tmp/sop_status_$$
        fi
    fi

    # Calculate compliance percentage from violations
    if [ "$recent_violations" != "unknown" ] && [ "$recent_violations" -ge 0 ]; then
        if [ "$recent_violations" -eq 0 ]; then
            compliance_percentage="100"
        elif [ "$recent_violations" -le 2 ]; then
            compliance_percentage="80"
        elif [ "$recent_violations" -le 5 ]; then
            compliance_percentage="60"
        else
            compliance_percentage="40"
        fi
    fi

    # Update lock file with enhanced heartbeat data
    local temp_file="/tmp/heartbeat_update_$$.json"
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import json, sys, os

try:
    # Read existing lock file
    with open('$lock_file', 'r') as f:
        lock_data = json.load(f)
    
    # Update heartbeat and compliance data
    lock_data['last_heartbeat'] = '$new_timestamp'
    lock_data['sop_monitoring'] = {
        'active': $monitoring_active,
        'compliance_percentage': '$compliance_percentage',
        'recent_violations': $recent_violations,
        'heartbeat_timestamp': '$new_timestamp'
    }
    
    # Write updated data
    with open('$temp_file', 'w') as f:
        json.dump(lock_data, f, indent=2)
        
except Exception as e:
    print(f'Error updating heartbeat: {e}', file=sys.stderr)
    sys.exit(1)
"
        
        # Replace original file with updated one
        if [ -f "$temp_file" ]; then
            mv "$temp_file" "$lock_file"
        fi
    else
        # Fallback: update only heartbeat timestamp without compliance data
        sed -i '' 's/"last_heartbeat": "[^"]*"/"last_heartbeat": "'"$new_timestamp"'"/' "$lock_file"
    fi
}

# Function to log compliance status for multi-agent coordination
log_compliance_status() {
    local compliance_log="$LOCKS_DIR/../logs/compliance_status.log"
    mkdir -p "$(dirname "$compliance_log")"
    
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local agent_session="$AGENT_ID:$SESSION_ID"
    
    echo "[$timestamp] $agent_session - SOP Monitoring: Active=$monitoring_active, Compliance=$compliance_percentage%, Violations=$recent_violations" >> "$compliance_log"
}

# Function to update global compliance cache for dashboard
update_compliance_cache() {
    local cache_data=""
    
    if [ -f "$COMPLIANCE_CACHE" ]; then
        cache_data=$(cat "$COMPLIANCE_CACHE" 2>/dev/null || echo "{}")
    else
        cache_data="{}"
    fi
    
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import json, sys, os
from datetime import datetime

try:
    # Load existing cache
    cache_file = '$COMPLIANCE_CACHE'
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    else:
        cache = {}
    
    # Update cache with current session data
    session_key = '${AGENT_ID}_${SESSION_ID}'
    cache[session_key] = {
        'agent_id': '${AGENT_ID}',
        'session_id': '${SESSION_ID}',
        'last_heartbeat': '$(date -u +"%Y-%m-%dT%H:%M:%SZ")',
        'sop_monitoring_active': $monitoring_active,
        'compliance_percentage': '$compliance_percentage',
        'recent_violations': $recent_violations,
        'lock_file': '$1'
    }
    
    # Clean old entries (older than 1 hour)
    current_time = datetime.now().isoformat()
    entries_to_remove = []
    for key, data in cache.items():
        if 'last_heartbeat' in data:
            try:
                from datetime import datetime as dt
                heartbeat_time = dt.fromisoformat(data['last_heartbeat'].replace('Z', '+00:00'))
                current_dt = dt.fromisoformat(current_time.replace('Z', '+00:00'))
                if (current_dt - heartbeat_time).total_seconds() > 3600:  # 1 hour
                    entries_to_remove.append(key)
            except:
                entries_to_remove.append(key)
    
    for key in entries_to_remove:
        del cache[key]
    
    # Save updated cache
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
        
except Exception as e:
    print(f'Error updating compliance cache: {e}', file=sys.stderr)
    sys.exit(1)
"
    fi
}

# Function to check for other active agents and coordinate
coordinate_multi_agent() {
    local coordination_log="$LOCKS_DIR/../logs/agent_coordination.log"
    mkdir -p "$(dirname "$coordination_log")"
    
    # Count active sessions
    local active_sessions=0
    local current_task=""
    
    # Get current task from lock file
    if [ -f "$1" ]; then
        current_task=$(python3 -c "
import json, sys
try:
    with open('$1', 'r') as f:
        data = json.load(f)
    print(data.get('task_desc', 'unknown'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")
    fi
    
    # Count other active sessions
    for lock in "${LOCKS_DIR}"/*.json; do
        [ -e "$lock" ] || continue
        [ "$lock" = "$1" ] && continue  # Skip current session
        
        # Check if lock is recent (within 10 minutes)
        if python3 -c "
import json, sys, os
from datetime import datetime, timedelta

try:
    with open('$lock', 'r') as f:
        data = json.load(f)
    
    last_heartbeat = data.get('last_heartbeat', data.get('created_at', ''))
    if last_heartbeat:
        heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
        current_time = datetime.now()
        if (current_time - heartbeat_time).total_seconds() < 600:  # 10 minutes
            print(True)
        else:
            print(False)
    else:
        print(False)
except:
    print(False)
" 2>/dev/null; then
            ((active_sessions++))
        fi
    done
    
    # Log coordination info
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$timestamp] Agent $AGENT_ID:$SESSION_ID on task '$current_task' sees $active_sessions other active agents" >> "$coordination_log"
    
    # If many agents active, reduce monitoring frequency to avoid conflicts
    if [ "$active_sessions" -ge 3 ]; then
        echo "[$timestamp] High agent activity detected - coordination mode enabled" >> "$coordination_log"
        # This could trigger adaptive behavior in the SOP monitor
        echo "coordination_mode" > "$LOCKS_DIR/../cache/coordination_mode"
    fi
}

# Main execution
LOCK_FILE=$(find_lock_file)

if [ -z "$LOCK_FILE" ]; then
    # No lock file found - this is okay, session might not use coordination
    exit 0
fi

if [ ! -f "$LOCK_FILE" ]; then
    exit 0
fi

# Update enhanced heartbeat with compliance data
update_heartbeat_with_compliance "$LOCK_FILE"

# Log compliance status for coordination
log_compliance_status

# Update global compliance cache for dashboard
update_compliance_cache "$LOCK_FILE"

# Coordinate with other agents
coordinate_multi_agent "$LOCK_FILE"

# Optionally log (can be noisy, so only in debug mode)
if [ "${AGENT_DEBUG:-false}" = "true" ]; then
    echo "💓 Enhanced heartbeat updated: $(basename "$LOCK_FILE") at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "   SOP Monitoring: Active=$monitoring_active, Compliance=$compliance_percentage%, Violations=$recent_violations"
fi