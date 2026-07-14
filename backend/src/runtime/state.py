"""
ASEP — Typed LangGraph State
"""

from typing import Annotated, Any, TypedDict
import operator


class AgentState(TypedDict):
    """The central state schema for the agent execution graph."""

    # Message history list, accumulated on each state transition
    messages: Annotated[list[dict[str, Any]], operator.add]
    
    # Current status of the runner (e.g. "started", "running", "paused", "completed", "error")
    status: str
    
    # Next node or routing instruction
    next_action: str | None
    
    # Execution ID linking to AgentRun/Task
    run_id: str
    
    # Transient variables and outputs (keys to be consolidated or retrieved)
    variables: dict[str, Any]
    
    # Human input / interrupt response payload
    human_input: str | None
