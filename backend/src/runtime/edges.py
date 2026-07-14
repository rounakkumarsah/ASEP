"""
ASEP — Edge Registry and Conditional Routing Edges
"""

import logging
from typing import Callable

from src.runtime.state import AgentState

logger = logging.getLogger(__name__)

# Edge router function type: takes AgentState, returns the name of the next node
EdgeRouter = Callable[[AgentState], str]


class EdgeRegistry:
    """Generic registry to map and fetch graph conditional edge routing functions."""

    def __init__(self) -> None:
        self._routers: dict[str, EdgeRouter] = {}

    def register(self, name: str, router: EdgeRouter) -> None:
        """Register an edge routing function by name."""
        logger.debug(f"Registering edge router: '{name}'")
        self._routers[name] = router

    def get_router(self, name: str) -> EdgeRouter:
        """Fetch a registered edge router callback."""
        if name not in self._routers:
            raise KeyError(f"Edge router '{name}' is not registered.")
        return self._routers[name]


# --- Default Router Implementations ---

def human_validation_router_default(state: AgentState) -> str:
    """Routes based on human input. Returns next node name."""
    human_input = state.get("human_input")
    logger.info(f"Conditional routing edge checking human_input: '{human_input}'")
    
    if human_input == "approve":
        return "end"
    else:
        # Loop back to processing node if operator rejects or writes anything else
        return "process"
