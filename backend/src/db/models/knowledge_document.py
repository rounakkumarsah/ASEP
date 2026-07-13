"""
ASEP — KnowledgeDocument ORM Model
==================================
Defines the ``KnowledgeDocument`` SQLAlchemy 2.0 mapped class, which serves
as the canonical catalog for all documentation and reference material ingested
into the platform's Knowledge Layer.

Architecture context:
    This model tracks the lifecycle, origin, and extraction status of content
    but does NOT store the raw text or the embeddings itself.
    - Raw text and semantic chunks are stored in Neo4j.
    - Embedding vectors are stored in Qdrant.
    - The ``KnowledgeSyncService`` coordinates the ingestion pipeline
      (crawl -> chunk -> embed -> graph) and updates this row to reflect
      progress.

Design notes:
    - Uses SQLAlchemy 2.0 ``Mapped`` / ``mapped_column`` API throughout.
    - ``DocumentSourceType``, ``DocumentStatus``, and ``CrawlStatus`` are
      stored as native Postgres ``ENUM`` types for DB-level constraint
      enforcement.
    - No Foreign Keys are declared — this model integrates with external
      data stores (Qdrant, Neo4j, Crawl4AI) or future models without tight
      DB-level coupling.
    - ``trust_score`` uses ``NUMERIC(4, 3)`` to ensure exact decimal
      arithmetic for weighting retrieval confidence.
    - The JSONB ``metadata`` column is mapped to the Python attribute
      ``document_metadata`` to avoid shadowing SQLAlchemy's reserved
      ``DeclarativeBase.metadata`` attribute.
    - All timestamps are timezone-aware (``TIMESTAMPTZ``).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DocumentSourceType(str, enum.Enum):
    """Origin format or system for a ingested document."""

    WEB = "web"
    PDF = "pdf"
    GITHUB = "github"
    LOCAL = "local"
    MARKDOWN = "markdown"
    API = "api"
    VIDEO = "video"
    DOCS = "docs"


class DocumentStatus(str, enum.Enum):
    """Overall readiness state of the document in the Knowledge Layer."""

    PENDING = "pending"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class CrawlStatus(str, enum.Enum):
    """Lifecycle state of the external fetching/crawling phase."""

    PENDING = "pending"
    CRAWLING = "crawling"
    SUCCESS = "success"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# KnowledgeDocument
# ---------------------------------------------------------------------------


class KnowledgeDocument(TimestampMixin, Base):
    """ORM representation of a document in the Knowledge Layer catalog.

    Table:
        knowledge_documents

    Primary key:
        ``id`` — UUID v4.

    Foreign keys:
        None.  References to external graphs or vector stores are opaque
        strings (e.g. ``vector_collection``, ``graph_namespace``).
    """

    __tablename__ = "knowledge_documents"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side before INSERT.",
    )

    document_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Technical slug or identifier (e.g. 'fastapi_docs_v1').",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Human-readable display name.",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional abstract or summary of the document's contents.",
    )

    # ------------------------------------------------------------------
    # Source
    # ------------------------------------------------------------------

    source_type: Mapped[DocumentSourceType] = mapped_column(
        Enum(
            DocumentSourceType,
            name="document_source_type",
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        doc="Origin format or system.",
    )

    source_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True, doc="Original URL if fetched from the web."
    )

    local_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, doc="Path if ingested from local filesystem."
    )

    repository_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True, doc="Git repository URL if applicable."
    )

    repository_branch: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Git branch name if applicable."
    )

    # ------------------------------------------------------------------
    # File details
    # ------------------------------------------------------------------

    file_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, doc="Size of the raw document in bytes."
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(128), nullable=True, doc="MIME type of the raw document."
    )

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    version: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="Explicit version string (e.g. 'v1.0.0')."
    )

    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64), nullable=True, doc="SHA-256 hash of the raw file."
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, doc="Logical hash of the extracted text content."
    )

    language: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="ISO language code (e.g. 'en')."
    )

    encoding: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="Character encoding (e.g. 'utf-8')."
    )

    # ------------------------------------------------------------------
    # Knowledge / Status
    # ------------------------------------------------------------------

    trust_score: Mapped[Decimal] = mapped_column(
        Numeric(precision=4, scale=3),
        nullable=False,
        default=Decimal("0.500"),
        doc=(
            "Confidence or authority weight in [0.000, 1.000].  "
            "Used to rank conflicting answers."
        ),
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=DocumentStatus.PENDING,
        doc="Overall readiness state of the document.",
    )

    crawl_status: Mapped[CrawlStatus | None] = mapped_column(
        Enum(
            CrawlStatus,
            name="document_crawl_status",
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=True,
        doc="Lifecycle state of the external fetching/crawling phase.",
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of semantic chunks extracted.",
    )

    embedding_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of embedding vectors generated.",
    )

    graph_node_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of entities/relationships mapped in Neo4j.",
    )

    # ------------------------------------------------------------------
    # Vector details
    # ------------------------------------------------------------------

    vector_collection: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Qdrant collection name housing the vectors."
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Model used to generate the embeddings."
    )

    embedding_dimension: Mapped[int | None] = mapped_column(
        Integer, nullable=True, doc="Dimensionality of the embedding vectors."
    )

    # ------------------------------------------------------------------
    # Graph details
    # ------------------------------------------------------------------

    graph_namespace: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Neo4j label or partition holding the nodes."
    )

    graph_version: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="Ontology or extraction pipeline version."
    )

    # ------------------------------------------------------------------
    # Search metadata
    # ------------------------------------------------------------------

    tags: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True, doc="JSON array of semantic tags."
    )

    keywords: Mapped[list[str] | None] = mapped_column(
        JSONB, nullable=True, doc="JSON array of extracted keywords."
    )

    document_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        doc="Arbitrary JSONB context. Aliased to avoid DeclarativeBase.metadata.",
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last successful fetch from source."
    )

    last_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last successful vector/graph sync."
    )

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Opaque string identifier (e.g. UUID, 'system') of the creator.",
    )

    updated_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Opaque string identifier of the last actor to mutate the row.",
    )

    # ------------------------------------------------------------------
    # Check constraints and indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Check constraints -------------------------------------------------

        CheckConstraint(
            "trust_score >= 0.000 AND trust_score <= 1.000",
            name="ck_knowledgedocument_trust_score_range",
        ),
        CheckConstraint(
            "chunk_count >= 0",
            name="ck_knowledgedocument_chunk_count_non_negative",
        ),
        CheckConstraint(
            "embedding_count >= 0",
            name="ck_knowledgedocument_embedding_count_non_negative",
        ),
        CheckConstraint(
            "graph_node_count >= 0",
            name="ck_knowledgedocument_graph_node_count_non_negative",
        ),

        # Single-column Indexes ---------------------------------------------

        Index("ix_knowledgedocument_source_type", "source_type"),
        Index("ix_knowledgedocument_status", "status"),
        Index("ix_knowledgedocument_checksum", "checksum_sha256"),
        Index("ix_knowledgedocument_content_hash", "content_hash"),
        Index("ix_knowledgedocument_language", "language"),
        Index("ix_knowledgedocument_graph_namespace", "graph_namespace"),
        Index("ix_knowledgedocument_vector_collection", "vector_collection"),
        Index("ix_knowledgedocument_trust_score", "trust_score"),
        Index("ix_knowledgedocument_last_synced_at", "last_synced_at"),

        # Composite Indexes -------------------------------------------------

        Index("ix_knowledgedocument_source_status", "source_type", "status"),
        Index("ix_knowledgedocument_graph_status", "graph_namespace", "status"),
        Index("ix_knowledgedocument_lang_trust", "language", "trust_score"),
    )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation.

        Returns:
            str: A string of the form
                ``KnowledgeDocument(id=..., document_name=..., status=...)``.
        """
        name_preview = (
            (self.document_name[:40] + "…")
            if len(self.document_name) > 40
            else self.document_name
        )
        return (
            f"KnowledgeDocument("
            f"id={self.id!s}, "
            f"document_name={name_preview!r}, "
            f"source_type={self.source_type!r}, "
            f"status={self.status!r}"
            f")"
        )
