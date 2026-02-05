from datetime import datetime
from pathlib import Path

from harness.compliance import (
    check_approval,
    check_beads_available,
    check_planning_docs,
)
from harness.state import SMPState


def pre_flight_check_node(state: SMPState) -> SMPState:
    """
    Node for performing the Pre-Flight Check (PFC).
    """
    project_root = Path.cwd()
    blockers = []
    warnings = []

    # 1. Check planning docs
    context = check_planning_docs(project_root)
    if not context.roadmap_exists or not context.implementation_plan_exists:
        # These are warnings in our evolved system to allow flexibility
        warnings.append(f"Missing or misplaced planning docs: {context.missing_docs}")

    # 2. Check approval
    approval = check_approval()
    if not approval.approved:
        warnings.append("No explicit plan approval found in task.md")
    elif approval.stale:
        warnings.append(f"Plan approval is stale ({approval.age_hours:.1f} hours old)")

    # 3. Check beads
    if not check_beads_available():
        blockers.append("Beads (bd) CLI not available")

    pfc_passed = len(blockers) == 0

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "PFC",
        "action": "Run Pre-Flight Check",
        "outcome": f"Passed: {pfc_passed}. Blockers: {len(blockers)}, Warnings: {len(warnings)}",
        "status": "success" if pfc_passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "pfc_passed": pfc_passed,
        "blockers": blockers,
        "warnings": warnings,
        "current_phase": "IFO" if pfc_passed else "BLOCKED",
        "steps_completed": [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }
