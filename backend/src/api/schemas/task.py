"""
Task Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.common import ORMBaseModel
from src.db.models.task import TaskPriority, TaskStatus


class TaskDefinitionSchema(ORMBaseModel):
    """Schema for bulk task creation payload. Maps to TaskDefinition."""
    position: int = Field(..., ge=0, description="Execution order position")
    title: str = Field(..., min_length=1, description="Short title")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Priority weight")
    description: str | None = Field(default=None, description="Instruction prompt")
    task_metadata: dict[str, Any] | None = None
    tool_name: str | None = None


class TaskResponse(ORMBaseModel):
    """Presentation model for a Task."""
    id: uuid.UUID
    agent_run_id: uuid.UUID
    position: int
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    task_metadata: dict[str, Any] | None = None
    tool_name: str | None = None
    result: str | None = None
    error_message: str | None = None
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
