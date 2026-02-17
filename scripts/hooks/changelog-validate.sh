#!/usr/bin/env bash
set -euo pipefail

echo "Running CHANGELOG.md validation hooks..."
./scripts/changelog_validation.sh
status=$?
if [ $status -ne 0 ]; then
  echo "CHANGELOG validation failed. Aborting commit/push."
  exit 1
fi
exit 0
