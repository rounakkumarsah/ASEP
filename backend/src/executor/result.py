"""
ASEP — Executor Typed Result Models
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class TaskResult(BaseModel):
    """Records the outcome of a single SubTask execution."""
    task_id: str = Field(description="ID of the executed subtask")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    output: dict[str, Any] = Field(default_factory=dict, description="Structured output from the handler")
    error: str | None = Field(default=None, description="Error message on failure")
    attempts: int = Field(default=0, description="Total execution attempts made")
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)

    @property
    def duration_seconds(self) -> float | None:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ExecutionReport(BaseModel):
    """Aggregated summary of a full plan execution."""
    run_id: str
    overall_status: TaskStatus
    results: dict[str, TaskResult] = Field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    total_tasks: int = 0
    succeeded: int = 0
    failed: int = 0
    cancelled: int = 0

    @property
    def duration_seconds(self) -> float | None:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ProgressEvent(BaseModel):
    """A typed progress event yielded by the Executor during streaming."""
    event_type: str = Field(description="One of: task_started, task_succeeded, task_failed, task_cancelled, plan_completed")
    task_id: str | None = None
    status: TaskStatus | None = None
    detail: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
