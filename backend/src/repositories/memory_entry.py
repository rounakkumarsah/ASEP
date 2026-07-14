"""
ASEP — MemoryEntryRepository
==============================
Async repository for the ``MemoryEntry`` ORM model.

Extends ``BaseRepository`` with domain-specific query methods scoped to the
``memory_entries`` table.  All methods leverage the indexes declared on the
model and never call ``session.commit()``, ``session.rollback()``, or
``session.begin()``.

Query hot-paths covered:
    - Run memory retrieval: ``get_by_agent_run``
    - Namespace partition scans: ``get_by_namespace``, ``get_by_namespace_and_type``
    - Qdrant reconciliation: ``get_by_embedding_id``
    - Ranked retrieval: ``get_by_importance_range``, ``get_top_by_importance``
    - Usage tracking: ``increment_access_count``
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.repositories.base import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    BaseRepository,
    _clamp_limit,
)


class MemoryEntryRepository(BaseRepository[MemoryEntry, uuid.UUID]):
    """Async repository for ``MemoryEntry`` persistence and domain queries.

    Inherits CRUD primitives from ``BaseRepository``.  Adds query methods
    that map directly to the indexes on ``memory_entries``:

    - ``ix_memory_entry_agent_run_id``
    - ``ix_memory_entry_memory_type``
    - ``ix_memory_entry_namespace``
    - ``ix_memory_entry_embedding_id``
    - ``ix_memory_entry_namespace_type``

    Attributes:
        _model: Bound to ``MemoryEntry``.

    Example::

        repo = MemoryEntryRepository(session)
        top = await repo.get_top_by_importance("project-x", MemoryType.SEMANTIC)
    """

    _model = MemoryEntry

    # ------------------------------------------------------------------
    # Lookup by parent run
    # ------------------------------------------------------------------

    async def get_by_agent_run(
        self,
        agent_run_id: uuid.UUID,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[MemoryEntry]:
        """Return all memory entries associated with a given ``AgentRun``.

        Uses ``ix_memory_entry_agent_run_id``.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            *options:     SQLAlchemy loader strategy options.
            limit:        Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:       Rows to skip.

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``created_at DESC``.
        """
        stmt = (
            select(MemoryEntry)
            .where(MemoryEntry.agent_run_id == agent_run_id)
            .order_by(MemoryEntry.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Namespace partition scans
    # ------------------------------------------------------------------

    async def get_by_namespace(
        self,
        namespace: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[MemoryEntry]:
        """Return all memory entries within a namespace.

        Uses ``ix_memory_entry_namespace``.  All retrieval queries should
        supply a ``namespace`` to prevent cross-project contamination.

        Args:
            namespace: Logical partition identifier (project slug, tenant ID,
                       agent scope).
            *options:  SQLAlchemy loader strategy options.
            limit:     Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:    Rows to skip.

        Returns:
            A list of ``MemoryEntry`` instances in the namespace, ordered
            by ``importance_score DESC``.
        """
        stmt = (
            select(MemoryEntry)
            .where(MemoryEntry.namespace == namespace)
            .order_by(MemoryEntry.importance_score.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_by_namespace_and_type(
        self,
        namespace: str,
        memory_type: MemoryType,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[MemoryEntry]:
        """Return memory entries filtered by namespace and cognitive type.

        Uses the composite index ``ix_memory_entry_namespace_type`` — the
        hot retrieval path for the ``MemoryService``.

        Args:
            namespace:   Logical partition identifier.
            memory_type: Cognitive classification (``EPISODIC``,
                         ``SEMANTIC``, ``PROCEDURAL``, ``WORKING``).
            *options:    SQLAlchemy loader strategy options.
            limit:       Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:      Rows to skip.

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``importance_score DESC``.
        """
        stmt = (
            select(MemoryEntry)
            .where(
                MemoryEntry.namespace == namespace,
                MemoryEntry.memory_type == memory_type,
            )
            .order_by(MemoryEntry.importance_score.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Qdrant reconciliation
    # ------------------------------------------------------------------

    async def get_by_embedding_id(
        self,
        embedding_id: uuid.UUID,
        *options: ExecutableOption,
    ) -> MemoryEntry | None:
        """Return the memory entry that corresponds to a Qdrant point ID.

        Uses ``ix_memory_entry_embedding_id``.  Called by the embedding
        pipeline to reconcile vector-store results back to PostgreSQL rows.

        Args:
            embedding_id: UUID of the Qdrant point.
            *options:     SQLAlchemy loader strategy options.

        Returns:
            The ``MemoryEntry`` instance, or ``None`` if no entry has been
            linked to this embedding ID yet.
        """
        stmt = select(MemoryEntry).where(MemoryEntry.embedding_id == embedding_id)
        if options:
            stmt = stmt.options(*options)
        return await self._session.scalar(stmt)

    # ------------------------------------------------------------------
    # Ranked retrieval — importance range
    # ------------------------------------------------------------------

    async def get_by_importance_range(
        self,
        namespace: str,
        min_score: Decimal,
        max_score: Decimal,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[MemoryEntry]:
        """Return entries within a namespace filtered by importance score.

        Useful for the ``MemoryService`` to exclude low-quality entries
        below a dynamic threshold before embedding-similarity re-ranking.

        Args:
            namespace:  Logical partition identifier.
            min_score:  Minimum ``importance_score`` (inclusive), in
                        ``[0.000, 1.000]``.
            max_score:  Maximum ``importance_score`` (inclusive).
            *options:   SQLAlchemy loader strategy options.
            limit:      Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``importance_score DESC``.
        """
        stmt = (
            select(MemoryEntry)
            .where(
                MemoryEntry.namespace == namespace,
                MemoryEntry.importance_score >= min_score,
                MemoryEntry.importance_score <= max_score,
            )
            .order_by(MemoryEntry.importance_score.desc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Top-N retrieval
    # ------------------------------------------------------------------

    async def get_top_by_importance(
        self,
        namespace: str,
        memory_type: MemoryType,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[MemoryEntry]:
        """Return the top-N entries by ``importance_score`` in a namespace.

        Primary retrieval path for injecting memories into LLM context
        windows.  Uses ``ix_memory_entry_namespace_type``.

        Args:
            namespace:   Logical partition identifier.
            memory_type: Cognitive classification to narrow the result set.
            *options:    SQLAlchemy loader strategy options.
            limit:       Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``importance_score DESC, accessed_at DESC NULLS LAST``.
        """
        stmt = (
            select(MemoryEntry)
            .where(
                MemoryEntry.namespace == namespace,
                MemoryEntry.memory_type == memory_type,
            )
            .order_by(
                MemoryEntry.importance_score.desc(),
                MemoryEntry.accessed_at.desc().nulls_last(),
            )
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    async def increment_access_count(self, entry_id: uuid.UUID) -> MemoryEntry:
        """Increment the access counter and refresh ``accessed_at``.

        Called by the ``MemoryService`` each time a memory entry is
        successfully retrieved and injected into an agent context window.
        The recency timestamp is set to the current UTC time.

        Args:
            entry_id: UUID of the ``MemoryEntry`` to update.

        Returns:
            The updated ``MemoryEntry`` instance.

        Raises:
            NoResultFound: If no ``MemoryEntry`` with ``entry_id`` exists.
        """
        entry = await self.get_or_raise(entry_id)
        return await self.update(
            entry,
            access_count=entry.access_count + 1,
            accessed_at=datetime.now(tz=timezone.utc),
        )
