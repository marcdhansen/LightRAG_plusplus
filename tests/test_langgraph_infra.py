import os

from langgraph.graph import END, StateGraph

from harness.persistence import get_sqlite_checkpointer
from harness.state import SMPState


def test_node(state: SMPState) -> SMPState:
    return {**state, "current_phase": "PFC_START"}


def test_langgraph_infrastructure():
    # 1. Setup State
    initial_state = {
        "mission_id": "TEST-001",
        "mission_description": "Testing Infrastructure",
        "current_phase": "INIT",
        "goals": ["Verify graph works"],
        "tasks": [],
        "facts_discovered": [],
        "educated_guesses": [],
        "steps_completed": [],
        "current_step_index": 0,
        "stall_count": 0,
        "pfc_passed": False,
        "rtb_passed": False,
        "blockers": [],
        "warnings": [],
        "awaiting_approval": False,
        "approval_request": None,
        "user_feedback": None,
        "last_updated": "2026-02-05",
    }

    # 2. Build Graph
    builder = StateGraph(SMPState)
    builder.add_node("start", test_node)
    builder.set_entry_point("start")
    builder.add_edge("start", END)

    # 3. Setup Persistence
    db_path = "test_harness_state.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    checkpointer = get_sqlite_checkpointer(db_path)
    graph = builder.compile(checkpointer=checkpointer)

    # 4. Run Graph
    config = {"configurable": {"thread_id": "test-thread"}}
    result = graph.invoke(initial_state, config)

    # 5. Verify
    assert result["current_phase"] == "PFC_START"

    # 6. Verify Persistence (Resume)
    resumed_result = graph.get_state(config)
    assert resumed_result.values["current_phase"] == "PFC_START"

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


if __name__ == "__main__":
    test_langgraph_infrastructure()
    print("✅ LangGraph Infrastructure Test Passed!")
