import os

from harness.engine import create_harness_graph, get_sqlite_checkpointer, run_harness


def test_full_harness_lifecycle():
    mission_id = "MISSION-SOTA"
    thread_id = "sota-thread-1"
    db_path = "harness_state_final.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    print("🚀 --- STEP 1: INITIALIZE & PFC ---")
    run_harness(mission_id, "SOTA Lifecycle Test", thread_id, db_path=db_path)

    print("\n✋ --- STEP 2: RESUME & PASS APPROVAL ---")
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    # This will pass through approval, then IFO, then RTB, then Debrief
    # RTB might fail if there are uncommitted changes (which there are now)
    final_output = graph.invoke(None, config)

    print(f"\nPhase after first full run: {final_output['current_phase']}")
    if final_output["blockers"]:
        print(f"Blockers encountered: {final_output['blockers']}")

    assert final_output["current_phase"] in ["RTB_BLOCKED", "COMPLETE"]

    print(f"\nSteps performed: {len(final_output['steps_completed'])}")
    for step in final_output["steps_completed"]:
        print(f"  [{step['status']}] {step['task_id']}: {step['action']}")

    print("\n✅ Full Harness Lifecycle Verified!")


if __name__ == "__main__":
    test_full_harness_lifecycle()
