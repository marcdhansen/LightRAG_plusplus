#!/bin/bash
#
# Agent Heartbeat Script
# Updates the session lock file heartbeat timestamp
# This should be called periodically (e.g., every 5 minutes) during active sessions
#

set -e

# Configuration
LOCKS_DIR=".agent/session_locks"

# Get agent info
AGENT_ID="${OPENCODE_AGENT_ID:-unknown}"
SESSION_ID="${OPENCODE_SESSION_ID:-$(date +%s)}"

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

# Function to update heartbeat
update_heartbeat() {
    local lock_file="$1"
    local new_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Update the last_heartbeat field in the JSON file
    # Using sed to replace the timestamp (macOS compatible)
    sed -i '' 's/"last_heartbeat": "[^"]*"/"last_heartbeat": "'"$new_timestamp"'"/' "$lock_file"

    return 0
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

# Update heartbeat
update_heartbeat "$LOCK_FILE"

# Optionally log (can be noisy, so only in debug mode)
if [ "${AGENT_DEBUG:-false}" = "true" ]; then
    echo "💓 Heartbeat updated: $(basename "$LOCK_FILE") at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
fi
