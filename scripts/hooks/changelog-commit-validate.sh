#!/usr/bin/env bash
set -euo pipefail

# Commit-msg hook: ensure CHANGELOG.md changes are accompanied by an explicit changelog mention in the commit message
MSG_FILE=${1:-}
MSG=""
if [[ -n "$MSG_FILE" && -f "$MSG_FILE" ]]; then
  MSG=$(cat "$MSG_FILE")
fi

if git diff --cached --name-only | grep -qE '^CHANGELOG.md$'; then
  if ! echo "$MSG" | grep -qiE 'CHANGELOG|CHANGE LOG|Changelog'; then
    echo "ERROR: CHANGELOG.md was modified but the commit message does not mention CHANGELOG."
    echo "Please include a note about the CHANGELOG changes in your commit message."
    exit 1
  fi
fi

exit 0
