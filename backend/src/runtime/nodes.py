"""
ASEP — Node Registry and Generic Graph Nodes
"""

import logging
from typing import Any, Callable

from langgraph.types import interrupt

from src.runtime.state import AgentState

logger = logging.getLogger(__name__)

# Node function type: takes AgentState, returns updates dictionary
NodeFunc = Callable[[AgentState], dict[str, Any]]


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
        "messages": [{"role": "system", "content": "Graph execution started."}]
    }


def process_node_default(state: AgentState) -> dict[str, Any]:
    """Simulates processing work."""
    logger.info(f"Process node executed for run {state.get('run_id')}")
    return {
        "status": "processing",
        "messages": [{"role": "system", "content": "Processing task steps."}]
    }


def human_validation_node_default(state: AgentState) -> dict[str, Any]:
    """Pauses execution using LangGraph's native interrupt, prompting for validation."""
    logger.info(f"Human validation node reached for run {state.get('run_id')}. Pausing...")
    
    # LangGraph interrupt halts execution.
    # On resume, this call returns the resume payload passed to the run.
    resume_payload = interrupt("Requesting operator approval.")
    
    logger.info(f"Resumed validation node with payload: {resume_payload}")
    return {
        "status": "resumed",
        "human_input": str(resume_payload),
        "messages": [{"role": "system", "content": f"Operator responded: {resume_payload}"}]
    }


def end_node_default(state: AgentState) -> dict[str, Any]:
    """Finalizes run and sets terminal status."""
    logger.info(f"End node executed for run {state.get('run_id')}")
    return {
        "status": "completed",
        "messages": [{"role": "system", "content": "Graph execution completed."}]
    }
