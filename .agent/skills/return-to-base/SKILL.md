---
name: return-to-base
description: Performs Return To Base (RTB) checks and completes session workflow. Validates git status, runs quality gates, updates issue status, and ensures proper session cleanup.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# Return To Base (RTB) Execution Skill

The `return-to-base` skill performs the actual RTB workflow execution when called by an agent.

## Usage

```bash
/return-to-base
```

## Purpose

Performs comprehensive Return To Base checks to ensure:
- All work is committed and pushed to remote
- Quality gates have been passed
- Issue status is properly updated
- Session cleanup is complete
- Next session has proper context

## Implementation

The skill executes:

```bash
./.agent/skills/return-to-base/scripts/return-to-base.sh
```

## Workflow Steps

1. **Pre-Flight Validation**
   - Check current git status
   - Identify uncommitted changes
   - Validate branch state

2. **Quality Gates** (if code changed)
   - Run tests (if available)
   - Run linting/typechecking (if configured)
   - Build validation (if applicable)

3. **Issue Management**
   - Check for open beads issues
   - Update issue status via `bd` commands
   - Close completed tasks

4. **Git Operations**
   - Pull latest changes with rebase
   - Sync beads database
   - Push all changes to remote
   - Verify clean git status

5. **Session Cleanup**
   - Clear temporary files
   - Prune stale branches
   - Update session locks

6. **Global Memory Sync**
   - Commit learnings to `~/.gemini`
   - Push global memory changes

## Exit Conditions

RTB is complete when:
- `git status` shows "up to date with origin"
- All beads issues are properly resolved or updated
- No uncommitted changes remain
- Session locks are cleared
- Global memory is synchronized

## Integration

This skill integrates with:
- FlightDirector PFC/RTB system
- Beads task management
- Multi-agent session locks
- Git workflow automation

## Error Handling

If RTB fails:
1. Check for merge conflicts - resolve and retry
2. Verify network connectivity for git operations
3. Check beads daemon status (`bd daemon status`)
4. Review error logs in automation scripts
5. Manual intervention may be required for certain edge cases
