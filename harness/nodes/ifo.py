from datetime import datetime

from harness.agents.sisyphus import sisyphus_orchestrator
from harness.state import SMPState


def in_flight_operations_node(state: SMPState) -> SMPState:
    """
    In-Flight Operations node delegating to the Sisyphus team.
    """
    return sisyphus_orchestrator(state)


def human_approval_node(state: SMPState) -> SMPState:
    """
    Node that explicitly requests human approval.
    LangGraph will interrupt BEFORE this node.
    """
    print(f"✋ Awaiting manual approval for {state['mission_id']}")

    # Once continued, we assume approved (or user edited state)
    return {
        **state,
        "awaiting_approval": False,
        "current_phase": "APPROVED",
        "last_updated": datetime.now().isoformat(),
    }
