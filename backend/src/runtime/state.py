"""
ASEP — Typed LangGraph State
"""

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    """The central state schema for the agent execution graph."""

    # Core input
    goal: str

    # Message history list, accumulated on each state transition
    messages: Annotated[list[dict[str, Any]], operator.add]

    # Decomposed subtasks / plan
    plan: list[str]

    # Current status of the runner (e.g. "started", "planning", "researching", "rag", "coding", "paused", "completed")
    status: str

    # Next node or routing instruction
    next_action: str | None

    # Execution ID linking to AgentRun/Task
    run_id: str

    # Model choice
    model: str

    # Transient variables and outputs (MCP results, RAG chunks, code artifacts)
    variables: dict[str, Any]

    # Human input / interrupt response payload
    human_input: str | None
