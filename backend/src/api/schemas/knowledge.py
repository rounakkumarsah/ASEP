"""
Knowledge Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from src.api.schemas.common import ORMBaseModel
from src.db.models.knowledge_document import CrawlStatus, DocumentSourceType, DocumentStatus


class KnowledgeDocumentRegister(ORMBaseModel):
    """Payload for registering a new knowledge document."""
    document_name: str = Field(..., min_length=1, description="Technical slug or identifier")
    title: str = Field(..., min_length=1, description="Human-readable title")
    source_type: DocumentSourceType = Field(..., description="Origin format or system")
    description: str | None = None
    source_url: str | None = None
    local_path: str | None = None
    repository_url: str | None = None
    repository_branch: str | None = None
    version: str | None = None
    language: str | None = None
    encoding: str | None = None
    trust_score: float = Field(0.5, ge=0.0, le=1.0, description="Float score 0.0-1.0")
    mime_type: str | None = None


class KnowledgeDocumentResponse(ORMBaseModel):
    """Presentation model for a Knowledge Document."""
    id: uuid.UUID
    document_name: str
    title: str
    source_type: DocumentSourceType
    status: DocumentStatus
    crawl_status: CrawlStatus
    description: str | None
    source_url: str | None
    local_path: str | None
    repository_url: str | None
    repository_branch: str | None
    version: str | None
    checksum_sha256: str | None
    content_hash: str | None
    language: str | None
    encoding: str | None
    trust_score: Decimal
    mime_type: str | None
    file_size_bytes: int | None
    chunk_count: int | None
    embedding_count: int | None
    graph_node_count: int | None
    vector_collection: str | None
    embedding_model: str | None
    embedding_dimension: int | None
    graph_namespace: str | None
    graph_version: str | None
    document_metadata: dict[str, Any] | None
    created_by: str | None
    last_indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime
