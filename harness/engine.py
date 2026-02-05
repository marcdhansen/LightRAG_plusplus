from langgraph.graph import END, StateGraph

from harness.nodes.ifo import human_approval_node, in_flight_operations_node
from harness.nodes.pfc import pre_flight_check_node
from harness.nodes.rtb import mission_debrief_node, return_to_base_node
from harness.persistence import get_sqlite_checkpointer
from harness.state import SMPState


def create_harness_graph(checkpointer=None):
    """
    Creates and compiles the SMP harness graph.
    """
    builder = StateGraph(SMPState)

    # Add nodes
    builder.add_node("pfc", pre_flight_check_node)
    builder.add_node("approval", human_approval_node)
    builder.add_node("ifo", in_flight_operations_node)
    builder.add_node("rtb", return_to_base_node)
    builder.add_node("debrief", mission_debrief_node)

    # Define workflow
    builder.set_entry_point("pfc")

    # After PFC, if passed, go to approval. If failed, end (blocked).
    def route_after_pfc(state: SMPState):
        if state["pfc_passed"]:
            return "approval"
        return END

    builder.add_conditional_edges("pfc", route_after_pfc)

    # After approval (which has an interrupt), go to IFO
    builder.add_edge("approval", "ifo")

    # After IFO, go to RTB
    builder.add_edge("ifo", "rtb")

    # After RTB, go to Debrief if passed
    def route_after_rtb(state: SMPState):
        if state["rtb_passed"]:
            return "debrief"
        return END

    builder.add_conditional_edges("rtb", route_after_rtb)
    builder.add_edge("debrief", END)

    # Compile with checkpointer and interrupt
    return builder.compile(checkpointer=checkpointer, interrupt_before=["approval"])


def run_harness(
    mission_id: str, description: str, thread_id: str, db_path: str = "harness_state.db"
):
    """
    Run the compiled harness graph.
    """
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)

    initial_state = {
        "mission_id": mission_id,
        "mission_description": description,
        "current_phase": "INIT",
        "goals": [],
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
        "awaiting_approval": True,
        "approval_request": f"Approve start of mission {mission_id}",
        "user_feedback": None,
        "last_updated": "",
    }

    config = {"configurable": {"thread_id": thread_id}}

    # Check if we have existing state (resume)
    state = graph.get_state(config)
    if state and state.values:
        print(f"🔄 Resuming mission {mission_id} from {state.values['current_phase']}")
        return graph.invoke(None, config)
    else:
        print(f"🚀 Starting mission {mission_id}")
        return graph.invoke(initial_state, config)
