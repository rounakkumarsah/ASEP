"""
Memory Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from src.api.schemas.common import ORMBaseModel
from src.db.models.memory_entry import MemoryType


class MemoryEntryCreate(ORMBaseModel):
    """Payload for creating a new memory entry."""
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., min_length=1, description="Raw text of the memory")
    importance_score: float = Field(..., ge=0.0, le=1.0, description="Float score 0.0-1.0")
    embedding_id: uuid.UUID | None = None
    embedding_model: str | None = None
    context_data: dict[str, Any] | None = None


class MemoryEntryResponse(ORMBaseModel):
    """Presentation model for a Memory Entry."""
    id: uuid.UUID
    agent_run_id: uuid.UUID | None
    memory_type: MemoryType
    content: str
    importance_score: Decimal
    embedding_id: uuid.UUID | None
    embedding_model: str | None
    context_data: dict[str, Any] | None
    access_count: int
    last_accessed_at: datetime | None
    created_at: datetime
    updated_at: datetime
