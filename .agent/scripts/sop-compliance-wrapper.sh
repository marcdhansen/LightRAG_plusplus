#!/bin/bash
# CI SKIP HEADER - defense in depth
# Pre-commit hooks are local development tools, not CI tools
if [[ "$GITHUB_ACTIONS" == "true" ]] || [[ "$CI" == "true" ]]; then
    echo "ℹ️ Skipping in CI (pre-commit hooks are local development tools)"
    exit 0
fi

# SOP Compliance Wrapper for Pre-commit
# Runs full check locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_PATH="/Users/marchansen/.gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py"

# Check if orchestrator script exists
if [[ ! -f "$ORCHESTRATOR_PATH" ]]; then
    echo "⚠️  Orchestrator script not found at: $ORCHESTRATOR_PATH"
    echo "💡 Install from: ~/.gemini/antigravity/skills/Orchestrator/"
    exit 0
fi

# Local: run full check
exec python3 "$ORCHESTRATOR_PATH" --finalize --turbo
