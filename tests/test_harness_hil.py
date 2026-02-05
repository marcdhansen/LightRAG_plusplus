import os

from harness.engine import create_harness_graph, get_sqlite_checkpointer, run_harness


def test_hil_flow():
    mission_id = "HIL-TEST"
    thread_id = "hil-thread-1"
    db_path = "harness_state.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    print("--- FIRST RUN (Should hit interrupt) ---")
    result = run_harness(mission_id, "Testing Human-in-Loop", thread_id)

    # Check if interrupted
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

    print(f"Current Phase in State: {state.values['current_phase']}")
    print(f"Next Node Expected: {state.next}")

    assert "approval" in state.next
    assert state.values["pfc_passed"] is True

    print("\n--- SECOND RUN (Resuming, should pass interrupt) ---")
    # To pass a node with interrupt_before, we just call invoke(None, config)
    final_result = graph.invoke(None, config)

    print(f"Final Phase: {final_result['current_phase']}")
    assert final_result["current_phase"] == "IFO_ACTIVE"
    print("✅ Human-in-Loop and Checkpointing (Phase 3 & 4) Verified!")


if __name__ == "__main__":
    test_hil_flow()
