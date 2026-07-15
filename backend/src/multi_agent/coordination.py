"""
ASEP — Coordination Context
"""

from typing import Any

from pydantic import BaseModel, Field

from src.multi_agent.contracts import AgentRole


class CoordinationContext(BaseModel):
    """Shared state representation to ensure synchronized multi-agent operations."""
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str
    goal: str
    active_role: AgentRole = Field(default=AgentRole.SUPERVISOR)
    shared_state: dict[str, Any] = Field(default_factory=dict)
