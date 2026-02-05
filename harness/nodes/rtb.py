import subprocess
from datetime import datetime
from pathlib import Path

from harness.state import SMPState


def return_to_base_node(state: SMPState) -> SMPState:
    """
    Node for performing the Return To Base (RTB) checks.
    """
    blockers = []

    # 1. Git Status Check
    try:
        status_out = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        if status_out:
            blockers.append("Uncommitted changes detected in repository")
    except Exception as e:
        blockers.append(f"Failed to check git status: {str(e)}")

    # 2. Reflection Check (look for recent reflection in brain or logs)
    reflection_found = False
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        # Look for reflect_history.json or similar in recent session dirs
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            if (d / "reflect_history.json").exists() or (d / "debrief.md").exists():
                reflection_found = True
                break

    if not reflection_found:
        blockers.append("No recent reflection found. Invoke /reflect before RTB.")

    rtb_passed = len(blockers) == 0

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "RTB",
        "action": "Run Return To Base check",
        "outcome": f"Passed: {rtb_passed}. Blockers: {len(blockers)}",
        "status": "success" if rtb_passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "rtb_passed": rtb_passed,
        "blockers": blockers,
        "current_phase": "DEBRIEF" if rtb_passed else "RTB_BLOCKED",
        "steps_completed": [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }


def mission_debrief_node(state: SMPState) -> SMPState:
    """
    Node for generating the mission debrief and syncing to memory.
    """
    print(f"🎖️ Mission Debrief for {state['mission_id']}")

    # Placeholder for actual debrief generation logic
    # In a real system, this would call specialized agents or tools

    return {
        **state,
        "current_phase": "COMPLETE",
        "last_updated": datetime.now().isoformat(),
    }
