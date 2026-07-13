"""
ASEP — LangGraph Agent State
==============================
Defines the typed state schema shared across all graph nodes.

The state is the single source of truth that flows through every
node in the LangGraph execution graph.

TODO (Phase 0.2):
    - Add memory context fields (episodic, semantic, procedural)
    - Add tool call history
    - Add error / retry tracking
    - Add token usage / cost tracking
    - Add streaming output buffer
    - Implement persistence via LangGraph checkpointers
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Immutable-style LangGraph state container.

    Each node receives a copy and returns mutations.
    LangGraph merges mutations back into the main state.

    TODO (Phase 0.2): Convert to TypedDict for native LangGraph compatibility.
    """

    # Identity
    run_id: UUID = Field(default_factory=uuid4, description="Unique ID for this agent run")
    session_id: str = Field(default="", description="User session identifier")

    # Task / goal
    goal: str = Field(default="", description="High-level task description provided by the user")
    plan: list[str] = Field(default_factory=list, description="Ordered subtask list from Planner")

    # Execution
    current_step: int = Field(default=0, description="Index into plan[]")
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="LangChain-compatible message list (role, content)",
    )

    # Results
    tool_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Accumulated tool execution results",
    )
    final_output: str | None = Field(default=None, description="Final response to the user")

    # Control flow
    is_complete: bool = Field(default=False, description="True when the graph should terminate")
    error: str | None = Field(default=None, description="Last error message if any node failed")

    # TODO (Phase 0.2): memory: MemoryContext
    # TODO (Phase 0.2): cost_tracker: CostTracker
    # TODO (Phase 0.2): tool_call_history: list[ToolCall]
