---
name: Flight Director
description: Automates Standard Mission Protocol (SMP) validation for Pre-Flight Checks (PFC) and Return To Base (RTB) procedures.
---

# 👮 Flight Director Skill

## Purpose

The Flight Director ensures strict adherence to the Standard Mission Protocol (SMP). It acts as a gatekeeper, verifying that all administrative and procedural steps are completed before the agent proceeds with planning or execution.

## 🛠️ Tools & Scripts

### 1. `check_ready` (PFC)

Verifies that the "Pre-Flight" conditions are met:

- **Beads Issue**: A Beads issue must be creating/selected for the current task.
- **Task Artifact**: `task.md` must be initialized.
- **Plan Artifact**: `ImplementationPlan.md` and `ROADMAP.md` must exist.
- **Plan Approval**: `task.md` must contain the `## Approval:` marker showing user sign-off.

**Usage**:

```bash
python scripts/check_flight_readiness.py --pfc
```

### 2. `check_landed` (RTB)

Verifies that "Return To Base" conditions are met:

- **Git Status**: Repository must be clean (synced).
- **Cleanup**: Checks for temporary artifacts (`rag_storage_*`, `test_output.txt`, etc.).
- **Linting**: Runs `markdownlint` on task and planning documents.
- **Beads Status**: Issue for current task should be updated/closed.

**Usage**:

```bash
# Check status
python scripts/check_flight_readiness.py --rtb

# Purge temporary artifacts
python scripts/check_flight_readiness.py --clean
```

## 📋 Protocols

### Pre-Flight Check (PFC)

**WHEN**: At the very beginning of a new task, immediately after the user request is understood but PRIOR to writing code.

**STEPS**:

1. Run `check_ready` script.
2. If it fails (Red Code), STOP.
3. Fix the missing administrative step (e.g., `bd create`).
4. Re-run `check_ready`.
5. Proceed only when Green.

### Return To Base (RTB)

**WHEN**: When the user signals "Wrap This Up", "I'm done", or the task is theoretically complete.

**STEPS**:

1. Run `check_landed` script.
2. If it flags uncommitted changes, run `bd sync`.
3. If it flags open issues, ask user if they should be closed.
4. Provide the "Handoff" summary only after checks pass.
