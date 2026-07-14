"""
AgentRun Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.common import ORMBaseModel
from src.db.models.agent_run import RunStatus


class AgentRunCreate(ORMBaseModel):
    """Payload for initiating a new Agent Run."""
    goal: str = Field(..., description="High-level goal for the agent run", min_length=1)
    plan: dict[str, Any] = Field(default_factory=dict, description="Initial execution plan or configuration")


class AgentRunResponse(ORMBaseModel):
    """Presentation model for an Agent Run."""
    id: uuid.UUID
    goal: str
    plan: dict[str, Any]
    status: RunStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: str | None = None
