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
- **Document Reachability**: All documents must be reachable from GLOBAL_INDEX.md with working links.
- **Cleanup**: Checks for temporary artifacts (`rag_storage_*`, `test_output.txt`, etc.).
- **Linting**: Runs `markdownlint` on task and planning documents.
- **Beads Status**: Issue for current task should be updated/closed.

**Usage**:

```bash
# Check status
python .agent/skills/rtb/scripts/rtb_validator.py

# Or use the skill interface
skill return-to-base

# Run document reachability validation directly
python .agent/skills/FlightDirector/scripts/validate_document_reachability.py

# Purge temporary artifacts (legacy)
python scripts/check_flight_readiness.py --clean
```

### 3. Document Reachability Validator

Critical safety gate that ensures documentation integrity:

- **Link Validation**: Verifies all markdown links are working
- **Reachability Check**: Ensures all documents are reachable from GLOBAL_INDEX.md
- **SOP Compliance**: Enforces documentation standards per SOP requirements
- **Blocking Gate**: Prevents RTB completion if documentation issues are found

**Usage**:

```bash
python .agent/skills/FlightDirector/scripts/validate_document_reachability.py [--verbose] [--workspace-dir PATH]
```

**Exit Codes**:
- `0`: Success - All documents reachable and links working
- `2`: Error - Broken links or unreachable documents found (blocks RTB)

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

1. Run `rtb_validator.py` script (or use `skill return-to-base`).
2. If git status is dirty, run `bd sync` and commit changes.
3. If document reachability fails, fix broken links or add missing links to GLOBAL_INDEX.md.
4. If open issues are flagged, ask user if they should be closed.
5. Provide the "Handoff" summary only after all checks pass.

**CRITICAL**: The document reachability gate will BLOCK RTB completion if:
- Any documents are not reachable from GLOBAL_INDEX.md
- Any markdown links are broken
- Documentation violates SOP requirements
