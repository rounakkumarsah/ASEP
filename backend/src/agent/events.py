"""
ASEP — Agent Typed Event System
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentEventType(str, Enum):
    # Session lifecycle
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    SESSION_CANCELLED = "session_cancelled"

    # Context pipeline
    CONTEXT_BUILT = "context_built"

    # Planning phase
    PLAN_CREATED = "plan_created"

    # Execution phase
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"

    # Tool invocations
    TOOL_CALLED = "tool_called"
    TOOL_SUCCEEDED = "tool_succeeded"
    TOOL_FAILED = "tool_failed"

    # Memory
    MEMORY_UPDATED = "memory_updated"


class AgentEvent(BaseModel):
    """Strongly typed event emitted by the Agent throughout session execution."""
    event_type: AgentEventType
    session_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


def make_event(
    event_type: AgentEventType,
    session_id: str,
    **kwargs: Any,
) -> AgentEvent:
    """Construct an AgentEvent concisely from keyword payload args."""
    return AgentEvent(
        event_type=event_type,
        session_id=session_id,
        payload=kwargs,
    )
