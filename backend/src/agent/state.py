"""
ASEP — Agent State Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentSessionStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentState(BaseModel):
    """Complete typed snapshot of an agent session's runtime state."""
    session_id: str = Field(description="Unique session identifier")
    run_id: str = Field(description="Correlation ID for the underlying AgentRun DB record")
    thread_id: str = Field(
        description="LangGraph checkpoint thread ID (equals session_id for 1:1 mapping)"
    )
    goal: str = Field(description="The raw user-supplied goal that started this session")
    status: AgentSessionStatus = Field(default=AgentSessionStatus.IDLE)
    plan_task_count: int | None = Field(
        default=None,
        description="Number of tasks in the decomposed plan, set after planning phase"
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for extensibility"
    )
    start_time: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    end_time: datetime | None = Field(default=None)
