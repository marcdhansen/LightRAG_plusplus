from datetime import datetime

from harness.agents.hephaestus import create_forge_graph
from harness.state import SMPState


def sisyphus_orchestrator(state: SMPState) -> SMPState:
    """
    Sisyphus: Lead Orchestrator.
    Delegates work to specialists like Hephaestus.
    """
    print(f"🏛️ Sisyphus: Orchestrating tasks for mission {state['mission_id']}")

    # In a real system, we would iterate over state['tasks']
    # For this demo, we'll delegate one task to Hephaestus
    task_desc = "Implement Pydantic schema for state"

    forge = create_forge_graph()
    agent_initial_state = {
        "task": task_desc,
        "context": [state["mission_description"]],
        "logs": [],
        "result": "",
        "status": "init",
    }

    agent_output = forge.invoke(agent_initial_state)

    # Update main state with agent results
    fact = f"Hephaestus completed: {task_desc} (Status: {agent_output['status']})"

    return {
        **state,
        "facts_discovered": [fact],
        "steps_completed": [
            {
                "index": state["current_step_index"],
                "task_id": "ORCHESTRATION",
                "action": f"Sisyphus delegated to Hephaestus: {task_desc}",
                "outcome": agent_output["result"],
                "status": agent_output["status"],
                "timestamp": datetime.now().isoformat(),
            }
        ],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }
