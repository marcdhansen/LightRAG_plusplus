# Task: lightrag-nfb - Implement enhanced show-next-task script

## Objective

Create a robust Python script to implement the `show-next-task` skill instructions. This script should optimize the agent's cognitive load by providing a pre-formatted, comprehensive view of ready and in-progress tasks.

## Success Criteria

- [x] Python script `scripts/show_next_tasks.py` implemented.
- [x] Displays ALL ready tasks (unlimited or high limit).
- [x] Explicitly identifies and highlights tasks with `status: in_progress`.
- [x] Groups tasks by priority (P0, P1, P2, etc.).
- [x] Output is Markdown-formatted for easy AI parsing.
- [x] Includes total count and breakdown by priority.
- [x] Verified via `pytest` with mock Beads output.

## Proposed Strategy

1. **Test-First**: Create `tests/test_show_next_tasks.py` with mock Beads data.
2. **Implementation**:
    - Use `subprocess` to run `bd list --ready --limit 0 --json`. (Actually, `bd list --status in_progress --json` and `bd ready --json` might be better).
    - Parse JSON output.
    - Format into a clean Markdown table/list.
3. **Integration**: Update the `show-next-task` skill or provide this as a standard tool.

## Approval

## Plan

- [x] Create failing test case for task categorization.
- [x] Implement `scripts/show_next_tasks.py` logic.
- [x] Verify with tests.
- [x] RTB.
