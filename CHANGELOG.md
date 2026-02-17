# Changelog
## [2026-02-17] - Marc Hansen

fix(ci): add multi-layer CHANGELOG validation to prevent corruption

- Fix root cause: awk variable passing in changelog-update.yml (use -v)
- Add debug logging to track empty DATE/AUTHOR/MESSAGE variables
- Add pre-commit validation hook (changelog-validate.sh)
- Add commit-msg hook (changelog-commit-validate.sh)
- Reorder CI jobs: validate-changelog runs first (fail-fast)
- Reset corrupted CHANGELOG.md to clean state

This implements 5 validation layers:
1. Pre-commit hook (catches corruption before commit)
2. Commit-msg hook (validates staged changes)
3. CI validate-changelog job (runs first, ~5 seconds)
4. Branch protection (when configured)
5. Root cause fix (proper awk variable passing)
