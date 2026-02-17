#!/usr/bin/env bash
set -euo pipefail

MAX_SIZE=1048576

if [[ ! -f CHANGELOG.md ]]; then
  echo "CHANGELOG.md not found; skipping validation."
  exit 0
fi

SIZE=$(wc -c < CHANGELOG.md)
if (( SIZE > MAX_SIZE )); then
  echo "CHANGELOG.md too large: ${SIZE} bytes (max ${MAX_SIZE})"
  exit 1
fi

if grep -qE '^## \[\] - ' CHANGELOG.md; then
  echo "CHANGELOG.md contains an empty author/date entry (## [] - )."
  exit 1
fi

echo "CHANGELOG.md validation passed."
exit 0
