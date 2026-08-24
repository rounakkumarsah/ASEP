"""
ASEP — Node Registry and Generic Graph Nodes
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.types import interrupt

from src.runtime.state import AgentState

logger = logging.getLogger(__name__)

# Node function type: takes AgentState, returns updates dictionary
NodeFunc = Callable[[AgentState], dict[str, Any] | Awaitable[dict[str, Any]]]


class NodeRegistry:
    """Generic registry to map and fetch workflow node callback functions."""

    def __init__(self) -> None:
        self._nodes: dict[str, NodeFunc] = {}

    def register(self, name: str, func: NodeFunc) -> None:
        """Register a node callback function by name."""
        logger.debug(f"Registering node handler: '{name}'")
        self._nodes[name] = func

    def get_node(self, name: str) -> NodeFunc:
        """Fetch a registered node callback by name."""
        if name not in self._nodes:
            raise KeyError(f"Node handler '{name}' is not registered.")
        return self._nodes[name]

    def get_all(self) -> dict[str, NodeFunc]:
        """Fetch all registered node callbacks."""
        return self._nodes


# --- Default Lifecycle Node Implementations ---


def start_node_default(state: AgentState) -> dict[str, Any]:
    """Initializes run and updates status."""
    logger.info(f"Start node executed for run {state.get('run_id')}")
    return {
        "status": "running",
        "messages": [{"role": "system", "content": "Graph execution started."}],
    }


def process_node_default(state: AgentState) -> dict[str, Any]:
    """Simulates processing work."""
    logger.info(f"Process node executed for run {state.get('run_id')}")
    return {
        "status": "processing",
        "messages": [{"role": "system", "content": "Processing task steps."}],
    }


async def human_validation_node_default(state: AgentState) -> dict[str, Any]:
    """Pauses execution using LangGraph's native interrupt, enqueuing it in the HITLEngine."""
    run_id = state.get("run_id") or "unknown"

    import uuid

    from src.governance.hitl import get_hitl_engine

    engine = get_hitl_engine()

    # Note: Because LangGraph resumes from the interrupt() call, this block
    # only runs once when the node is first entered.
    session = await engine.create_session(
        request_id=str(uuid.uuid4()),
        execution_id=run_id,
        correlation_id=run_id,
        requesting_agent="graph_node",
        requesting_tool="human_validation",
        requested_permissions=["approve"],
        arguments={},
        justification="StateGraph requires human approval before terminating.",
    )

    # LangGraph interrupt halts execution, presenting the session details
    resume_payload = interrupt(
        {"session_id": session.session_id, "prompt": "Requesting operator approval."}
    )

    # Resolve resume payload value safely if it's an Enum or dict representation
    payload_val = resume_payload.value if hasattr(resume_payload, "value") else str(resume_payload)
    if isinstance(resume_payload, dict) and "action" in resume_payload:
        payload_val = resume_payload["action"]

    return {
        "status": "resumed",
        "human_input": str(payload_val).lower(),
        "messages": [{"role": "system", "content": f"Operator responded with: {payload_val}"}],
    }


def end_node_default(state: AgentState) -> dict[str, Any]:
    """Finalizes run and sets terminal status."""
    logger.info(f"End node executed for run {state.get('run_id')}")
    return {
        "status": "completed",
        "messages": [{"role": "system", "content": "Graph execution completed."}],
    }
