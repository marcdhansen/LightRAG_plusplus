# Task: lightrag-64p - Fix CI dependency issue: sqlite3 in requirements-validation.txt

## Objective

Fix the failing CI/CD pipeline caused by a non-existent PyPI package `sqlite3` being listed in `requirements-validation.txt`. `sqlite3` is a built-in Python module and should not be installed via pip.

## Success Criteria

- [x] `sqlite3` is removed from `requirements-validation.txt`.
- [x] No other built-in modules are incorrectly listed in requirements files.
- [x] Local dependencies can be installed without error.
- [ ] (Optional but recommended) Add a pre-commit or CI check to prevent built-in modules from being added to requirements files.

## Proposed Strategy

1. **Remove sqlite3**: Delete the line containing `sqlite3` in `requirements-validation.txt`.
2. **Scan for other built-ins**: Run a quick check on all `requirements*.txt` files to see if other standard library modules (e.g., `os`, `sys`, `json`, `datetime`) are accidentally listed.
3. **Verification**: Run `pip install -r requirements-validation.txt` (in a dry-run or temporary environment if possible, or just verify the file content).
4. **CI Validation**: Push the changes and verify the GitHub Actions run passes the dependency installation step.

## Approval

Plan Completed: 2026-02-04 04:00
Fixed CI dependency issue by removing sqlite3 from requirements-validation.txt. Verified with uv pip install --dry-run.
