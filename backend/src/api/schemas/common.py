"""
ASEP — Common Schemas
=====================
Shared Pydantic models for the API presentation layer.
"""

from __future__ import annotations

from typing import Annotated, Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMBaseModel(BaseModel):
    """Base class for all schema models that wrap ORM objects."""
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standardized error payload."""
    error_code: str
    message: str
    details: dict[str, Any] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated lists."""
    items: list[T]
    total: int
    limit: int
    offset: int


class PaginationParams(BaseModel):
    """Reusable query parameters for pagination."""
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0
