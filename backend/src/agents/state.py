"""
ASEP - LangGraph Agent State
==============================
Defines the typed state schema shared across all graph nodes.

The state is the single source of truth that flows through every
node in the LangGraph execution graph.
"""

from __future__ import annotations

# Import langgraph operator to reduce/append items if needed
import operator
from typing import Annotated, Any, TypedDict
from uuid import UUID


class MemoryContext(TypedDict, total=False):
    working: dict[str, Any]
    episodic: list[dict[str, Any]]
    semantic: list[dict[str, Any]]
    procedural: list[dict[str, Any]]

class CostTracker(TypedDict, total=False):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float

class ToolCall(TypedDict, total=False):
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    error: str | None


class AgentState(TypedDict, total=False):
    """
    TypedDict-style LangGraph state container.
    """

    # Identity
    run_id: UUID
    session_id: str

    # Task / goal
    goal: str
    plan: Annotated[list[str], operator.add]

    # Execution
    current_step: int
    messages: Annotated[list[dict[str, Any]], operator.add]

    # Results
    tool_results: Annotated[list[dict[str, Any]], operator.add]
    final_output: str | None

    # Control flow
    is_complete: bool
    error: str | None

    # Tracking
    memory: MemoryContext
    cost_tracker: CostTracker
    tool_call_history: Annotated[list[ToolCall], operator.add]
