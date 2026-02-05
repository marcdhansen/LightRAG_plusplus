import operator
from typing import Annotated, TypedDict


class SMPState(TypedDict):
    """
    State definition for the SOTA SMP LangGraph harness.
    Using reducers to allow append-only logic for lists.
    """

    # Mission Context
    mission_id: str
    mission_description: str
    current_phase: str  # PFC, IFO, RTB, DEBRIEF, COMPLETE

    # Task Ledger (Magentic-One pattern)
    goals: Annotated[list[str], operator.add]
    tasks: Annotated[list[dict], operator.add]
    facts_discovered: Annotated[list[str], operator.add]
    educated_guesses: Annotated[list[str], operator.add]

    # Progress Ledger
    steps_completed: Annotated[list[dict], operator.add]
    current_step_index: int
    stall_count: int

    # Compliance State
    pfc_passed: bool
    rtb_passed: bool
    blockers: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]

    # Human-in-Loop
    awaiting_approval: bool
    approval_request: str | None
    user_feedback: str | None

    # Meta
    last_updated: str
