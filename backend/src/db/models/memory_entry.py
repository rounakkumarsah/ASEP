"""
ASEP — MemoryEntry ORM Model
==============================
Defines the ``MemoryEntry`` SQLAlchemy 2.0 mapped class, which persists a
single unit of agent memory to PostgreSQL for long-term durability.

Architecture context:
    The ASEP memory system operates across three tiers:

    1. **Working memory** — ephemeral; managed by Redis (not this model).
    2. **Episodic / semantic / procedural memory** — durable; stored here
       in PostgreSQL with a parallel embedding vector in Qdrant.
    3. **Retrieval** — the ``MemoryService`` embeds a query, searches Qdrant
       by ``embedding_id``, then loads the full ``MemoryEntry`` rows from
       PostgreSQL for context injection.

    This model is the PostgreSQL anchor for tier 2.  It carries the raw
    ``content``, its cognitive classification (``memory_type``), retrieval
    metadata (``importance_score``, ``access_count``, ``accessed_at``), and
    a reference to the Qdrant point (``embedding_id``) that holds the
    corresponding vector.

Design notes:
    - Uses SQLAlchemy 2.0 ``Mapped`` / ``mapped_column`` API throughout;
      the legacy ``Column`` API is intentionally absent.
    - ``MemoryType`` is persisted as a native Postgres ``ENUM`` type for
      DB-level constraint enforcement.
    - ``importance_score`` uses ``NUMERIC(4, 3)`` — exact decimal arithmetic
      avoids floating-point drift in ranking calculations.  Constrained to
      ``[0.000, 1.000]`` by a CHECK constraint; defaults to ``0.500``.
    - ``agent_run_id`` is **nullable** (``ON DELETE SET NULL``).  A memory
      entry may exist without a parent run (e.g. bootstrapped domain
      knowledge), and must survive the deletion of its source run.
    - ``embedding_id`` is a bare ``UUID`` column with no FK constraint.
      Qdrant is a separate service; referential integrity between PostgreSQL
      and Qdrant is managed at the application layer, not the DB layer.
    - The JSONB ``metadata`` column is mapped to the Python attribute
      ``entry_metadata`` to avoid shadowing SQLAlchemy's reserved
      ``DeclarativeBase.metadata`` attribute.  It is aliased to the Postgres
      column ``metadata`` via the positional name argument in
      ``mapped_column("metadata", JSONB, ...)``.
    - ``namespace`` partitions memories by project, tenant, or agent scope,
      enabling the ``MemoryService`` to restrict retrieval to a relevant
      subset without full-table scans.
    - ``lazy="selectin"`` is used on the relationship so that
      ``AsyncSession`` callers receive a populated ``agent_run`` attribute
      without triggering a ``MissingGreenlet`` error from implicit lazy-
      loading in async context.
    - All timestamps are timezone-aware (``TIMESTAMPTZ``).  Server-side
      defaults via ``func.now()`` are used — not Python-side
      ``datetime.utcnow()`` (deprecated in Python 3.12).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.models.agent_run import AgentRun, TimestampMixin
from src.db.postgres import Base


# ---------------------------------------------------------------------------
# MemoryType
# ---------------------------------------------------------------------------


class MemoryType(str, enum.Enum):
    """Cognitive classification of a ``MemoryEntry``.

    Inheriting from ``str`` means every member is simultaneously a plain
    Python string and an enum member, which simplifies JSON serialisation
    and direct string comparison without requiring ``.value`` access.

    The taxonomy follows the standard three-tier memory model used in
    cognitive science and adopted by most agent-memory frameworks:

    Attributes:
        EPISODIC: A specific past event associated with a particular run:
            an agent action, a tool call result, an observation, or an
            intermediate artefact.  Episodic memories are the most granular
            and time-bound entries.
        SEMANTIC: General, decontextualised knowledge — code facts, domain
            concepts, API interfaces, entity relationships.  Not tied to a
            single run; shared across all agents in the same namespace.
        PROCEDURAL: A learned skill, workflow, or pattern the agent can
            apply to future tasks.  Analogous to "muscle memory" — the agent
            knows *how* to do something without reasoning from first
            principles each time.
        WORKING: Short-lived scratchpad content produced within the current
            run.  Primarily managed in Redis for speed; persisted here for
            auditability and cross-run introspection.  The ``MemoryService``
            is responsible for TTL-based eviction from Redis.
    """

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


# ---------------------------------------------------------------------------
# MemoryEntry
# ---------------------------------------------------------------------------


class MemoryEntry(TimestampMixin, Base):
    """ORM representation of a single durable agent memory.

    Each row stores one unit of agent knowledge: the raw ``content``, its
    cognitive classification (``memory_type``), a retrieval weight
    (``importance_score``), a reference to the corresponding Qdrant vector
    (``embedding_id``), and usage statistics used by the recency-weighted
    retrieval algorithm.

    Table:
        memory_entries

    Primary key:
        ``id`` — UUID v4, generated application-side so callers can
        construct the identifier before the INSERT is committed.

    Foreign key:
        ``agent_run_id`` → ``agent_runs.id`` (nullable).
        ``ON DELETE SET NULL`` preserves the memory entry when its source
        run is deleted — the entry becomes "unlinked" but remains available
        to future agents.

    Relationship:
        ``agent_run`` — unidirectional many-to-one to ``AgentRun``.  Typed
        ``Mapped[AgentRun | None]`` because ``agent_run_id`` is nullable.
        The reciprocal ``AgentRun.memories`` back-reference will be wired
        in a dedicated ``agent_run.py`` update.

    Attributes:
        id: UUID v4 primary key, generated on the Python side before INSERT.
        agent_run_id: Nullable FK to ``agent_runs.id``.  ``ON DELETE SET NULL``
            ensures the entry survives its parent run's deletion.  ``None``
            for globally scoped memories not associated with any run.
        memory_type: Cognitive classification of this entry.  Stored as a
            native Postgres ``ENUM``.  Defaults to ``MemoryType.EPISODIC``.
        content: Full raw text content of the memory.  Non-nullable; this is
            the primary information payload.
        summary: Optional compressed version of ``content`` suitable for
            injection into an LLM context window without consuming excessive
            tokens.
        importance_score: Retrieval weight ∈ ``[0.000, 1.000]``.  Stored as
            ``NUMERIC(4, 3)`` for exact decimal arithmetic.  Combined with
            recency and embedding similarity at retrieval time.  Defaults to
            ``0.500``.  Constrained by ``ck_memory_entry_importance_score_range``.
        embedding_id: UUID of the corresponding Qdrant point.  Not a FK —
            Qdrant is a separate service; integrity is maintained at the
            application layer.  ``None`` until the embedding pipeline has
            processed this entry.
        embedding_model: Identifier of the model used to produce the
            embedding (e.g. ``"nomic-embed-text"``).  ``None`` until the
            embedding pipeline runs.  Constrained: if ``embedding_model`` is
            set, ``embedding_id`` must also be set
            (``ck_memory_entry_embedding_model_with_id``).
        namespace: Logical partition identifier (project slug, tenant ID,
            agent scope).  Defaults to ``"default"``.  All retrieval
            queries should filter by namespace to avoid cross-contamination.
        source: Optional origin reference — a file path, URL, tool name, or
            human-readable provenance string.
        entry_metadata: Arbitrary JSONB context (chunk indices, page
            numbers, extraction parameters).  Stored in the Postgres column
            ``metadata``; mapped to ``entry_metadata`` in Python to avoid
            shadowing ``DeclarativeBase.metadata``.
        accessed_at: Timezone-aware timestamp updated each time this entry
            is retrieved by the ``MemoryService``.  Used by recency-weighted
            ranking.  ``None`` until the first retrieval.
        access_count: Running count of how many times this entry has been
            retrieved.  Constrained to ``>= 0``; incremented by the
            ``MemoryService`` on each successful retrieval.
        created_at: Inherited from ``TimestampMixin``.  Set once on INSERT.
        updated_at: Inherited from ``TimestampMixin``.  Refreshed on UPDATE.
        agent_run: Nullable many-to-one relationship to the source
            ``AgentRun``.  Loaded via ``selectin`` strategy for
            ``AsyncSession`` compatibility.
    """

    __tablename__ = "memory_entries"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side before INSERT.",
    )

    # ------------------------------------------------------------------
    # Source run reference (nullable)
    # ------------------------------------------------------------------

    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
        doc=(
            "Nullable FK to agent_runs.id.  "
            "ON DELETE SET NULL preserves the memory entry when its source run "
            "is deleted.  None for globally scoped memories not tied to any run."
        ),
    )

    # ------------------------------------------------------------------
    # Cognitive classification
    # ------------------------------------------------------------------

    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(
            MemoryType,
            name="memory_type",          # Postgres ENUM type name
            native_enum=True,            # Use a real Postgres ENUM (not VARCHAR)
            create_constraint=True,      # Emit CREATE TYPE on DDL generation
            validate_strings=True,       # Reject unknown values on load
        ),
        nullable=False,
        default=MemoryType.EPISODIC,
        doc="Cognitive classification of this entry.  Defaults to EPISODIC.",
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc=(
            "Full raw text content of the memory.  "
            "Non-nullable; this is the primary information payload."
        ),
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "Optional compressed version of content suitable for injection "
            "into an LLM context window without consuming excessive tokens."
        ),
    )

    # ------------------------------------------------------------------
    # Retrieval weight
    # ------------------------------------------------------------------

    importance_score: Mapped[Decimal] = mapped_column(
        Numeric(precision=4, scale=3),
        nullable=False,
        # String form avoids floating-point representation drift
        default=Decimal("0.500"),
        doc=(
            "Retrieval weight stored as NUMERIC(4, 3) for exact decimal arithmetic. "
            "Must be in [0.000, 1.000]; constrained by "
            "ck_memory_entry_importance_score_range.  "
            "Defaults to 0.500.  Combined with recency and embedding similarity "
            "at retrieval time."
        ),
    )

    # ------------------------------------------------------------------
    # Embedding reference (Qdrant, no FK)
    # ------------------------------------------------------------------

    embedding_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        doc=(
            "UUID of the corresponding Qdrant point.  "
            "No FK constraint — Qdrant is a separate service; referential "
            "integrity is maintained at the application layer.  "
            "None until the embedding pipeline has processed this entry."
        ),
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc=(
            "Identifier of the model used to produce the embedding "
            "(e.g. 'nomic-embed-text').  "
            "None until the embedding pipeline runs.  "
            "If set, embedding_id must also be set "
            "(ck_memory_entry_embedding_model_with_id)."
        ),
    )

    # ------------------------------------------------------------------
    # Namespace / provenance
    # ------------------------------------------------------------------

    namespace: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="default",
        doc=(
            "Logical partition identifier (project slug, tenant ID, agent scope).  "
            "Defaults to 'default'.  All retrieval queries should filter by "
            "namespace to avoid cross-contamination between projects or tenants."
        ),
    )

    source: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc=(
            "Optional origin reference — a file path, URL, tool name, or "
            "human-readable provenance string."
        ),
    )

    # ------------------------------------------------------------------
    # Agent-supplied context (JSONB)
    # ------------------------------------------------------------------

    entry_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",                      # Postgres column name — avoids Base.metadata clash
        JSONB,
        nullable=True,
        doc=(
            "Arbitrary JSONB context (chunk indices, page numbers, extraction "
            "parameters, source coordinates).  Stored in the Postgres column "
            "'metadata'; mapped to 'entry_metadata' in Python to avoid shadowing "
            "DeclarativeBase.metadata."
        ),
    )

    # ------------------------------------------------------------------
    # Usage statistics (recency-weighted retrieval)
    # ------------------------------------------------------------------

    accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc=(
            "Timezone-aware timestamp updated each time this entry is retrieved "
            "by the MemoryService.  Used by recency-weighted ranking.  "
            "None until the first retrieval."
        ),
    )

    access_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc=(
            "Running count of how many times this entry has been retrieved.  "
            "Constrained to >= 0 by ck_memory_entry_access_count_non_negative.  "
            "Incremented by the MemoryService on each successful retrieval."
        ),
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------

    agent_run: Mapped[AgentRun | None] = relationship(
        "AgentRun",
        foreign_keys=[agent_run_id],
        # selectin is required for AsyncSession: implicit lazy="select" raises
        # MissingGreenlet when the attribute is accessed outside an awaitable
        # context.  Callers can suppress loading with noload() option.
        lazy="selectin",
        doc=(
            "Nullable many-to-one relationship to the source AgentRun.  "
            "None for globally scoped memories not tied to any run.  "
            "Unidirectional — AgentRun.memories back-reference is wired separately."
        ),
    )

    # ------------------------------------------------------------------
    # Check constraints and indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Check constraints -------------------------------------------------

        # importance_score must be a valid probability-like weight
        CheckConstraint(
            "importance_score >= 0.000 AND importance_score <= 1.000",
            name="ck_memory_entry_importance_score_range",
        ),

        # access_count is a running total; must never be negative
        CheckConstraint(
            "access_count >= 0",
            name="ck_memory_entry_access_count_non_negative",
        ),

        # If an embedding model name is stored, its Qdrant point ID must
        # also be present — partial embedding records are disallowed
        CheckConstraint(
            "embedding_model IS NULL OR embedding_id IS NOT NULL",
            name="ck_memory_entry_embedding_model_with_id",
        ),

        # Indexes -----------------------------------------------------------

        # Retrieve all memories for a given run
        Index("ix_memory_entry_agent_run_id", "agent_run_id"),

        # Filter by cognitive category (episodic vs semantic vs procedural)
        Index("ix_memory_entry_memory_type", "memory_type"),

        # Tenant / project partition scans (all queries should be namespaced)
        Index("ix_memory_entry_namespace", "namespace"),

        # Look up by Qdrant point ID (embedding pipeline reconciliation)
        Index("ix_memory_entry_embedding_id", "embedding_id"),

        # Hot retrieval path: all memories of a type within a namespace
        Index("ix_memory_entry_namespace_type", "namespace", "memory_type"),
    )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation.

        Returns:
            str: A string of the form
                ``MemoryEntry(id=..., memory_type=..., namespace=...,
                importance_score=...)``.
        """
        return (
            f"MemoryEntry("
            f"id={self.id!s}, "
            f"memory_type={self.memory_type!r}, "
            f"namespace={self.namespace!r}, "
            f"importance_score={self.importance_score!r}"
            f")"
        )
