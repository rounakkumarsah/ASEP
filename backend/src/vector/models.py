"""
ASEP — Vector Models
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    """Represents a single vector point to be stored."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the vector")
    vector: list[float] = Field(description="The embedding vector")
    payload: dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the vector")


class VectorSearchResult(BaseModel):
    """Represents a matched vector from a search."""
    id: str | int = Field(description="The ID of the matched point")
    score: float = Field(description="The similarity score")
    payload: dict[str, Any] = Field(default_factory=dict, description="The payload metadata of the matched point")
    version: int = Field(description="The version of the point")
