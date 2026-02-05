import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """Internal state for an agent subgraph."""

    task: str
    context: list[str]
    logs: Annotated[list[str], operator.add]
    result: str
    status: str


def forge_node(state: AgentState) -> AgentState:
    """Hephaestus: Forge (Implementation)."""
    print(f"🔨 Hephaestus: Working on task '{state['task']}'")
    return {
        **state,
        "logs": [f"Hephaestus implemented: {state['task'][:20]}..."],
        "result": "Code implemented and linted.",
        "status": "success",
    }


def oracle_node(state: AgentState) -> AgentState:
    """Oracle: Validation."""
    print(f"👁️ Oracle: Validating implementation for '{state['task']}'")
    return {
        **state,
        "logs": [f"Oracle validated: {state['result']}"],
        "status": "verified",
    }


def create_forge_graph():
    builder = StateGraph(AgentState)
    builder.add_node("forge", forge_node)
    builder.add_node("oracle", oracle_node)

    builder.set_entry_point("forge")
    builder.add_edge("forge", "oracle")
    builder.add_edge("oracle", END)

    return builder.compile()
