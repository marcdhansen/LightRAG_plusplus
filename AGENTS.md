# Agent Instructions

See AGENT_INSTRUCTIONS.md for full instructions.

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Key Sections

Issue Tracking - How to use bd for work management
Development Guidelines - Code standards and testing
Visual Design System - Status icons, colors, and semantic styling for CLI output

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Visual Design Anti-Patterns

NEVER use emoji-style icons (🔴🟠🟡🔵⚪) in CLI output. They cause cognitive overload.

ALWAYS use small Unicode symbols with semantic colors:

Status: ○ ◐ ● ✓ ❄
Priority: ● P0 (filled circle with color)

## Agent Warning: Interactive Commands

DO NOT use bd edit - it opens an interactive editor ($EDITOR) which AI agents cannot use.

Use bd update with flags instead:

```
bd update <id> --description "new description"
bd update <id> --title "new title"
bd update <id> --design "design notes"
bd update <id> --notes "additional notes"
bd update <id> --acceptance "acceptance criteria"
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Testing is NOT complete until all tests pass
- Testing needs to include automated unit and integration tests
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If a push fails, resolve and retry until it succeeds
- BEFORE ANYTHING ELSE: run ‘bd onboard’ and follow the instructions
- Run 'bd quickstart' to understand how to use bd
- When creating a beads issue, always add a description like this: `--description="Why this issue exists and what needs to be done"`
- When closing an issue, always add a description describing how the issue was addressed and how the fixes were verified
- When problems are found, the next step is to document them and create a plan to investigate, test, and fix them in beads.  Only then can you proceed.
- Before beginning work, verify that beads is up to date and that the conductor plan is in sync with beads

