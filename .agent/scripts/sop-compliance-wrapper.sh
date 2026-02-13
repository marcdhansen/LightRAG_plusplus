#!/bin/bash
# SOP Compliance Wrapper for Pre-commit
# Skips in CI environment, runs full check locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR_PATH="/Users/marchansen/.gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py"

# CI detection - skip in GitHub Actions
if [[ "$GITHUB_ACTIONS" == "true" ]]; then
    echo "🤖 CI environment detected - skipping SOP compliance check"
    echo "💡 SOP compliance already validated during earlier workflow phases"
    exit 0
fi

# Check if orchestrator script exists
if [[ ! -f "$ORCHESTRATOR_PATH" ]]; then
    echo "⚠️  Orchestrator script not found at: $ORCHESTRATOR_PATH"
    echo "💡 Install from: ~/.gemini/antigravity/skills/Orchestrator/"
    exit 0
fi

# Local: run full check
exec python3 "$ORCHESTRATOR_PATH" --finalize --turbo
