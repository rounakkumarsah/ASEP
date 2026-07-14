"""
ASEP — MemoryService
======================
Business logic for ``MemoryEntry`` persistence and retrieval.

Responsibilities:
    - Validate inputs (content non-empty, namespace non-empty,
      importance_score in [0.0, 1.0]).
    - Convert Python ``float`` importance scores to ``Decimal`` before
      passing to the repository (keeps the public API ergonomic).
    - Orchestrate repository operations through the Unit of Work.
    - Commit the transaction explicitly after every mutating operation.
    - Return ORM entities; DTO mapping belongs to the API layer.

Out of scope for Phase 0.6:
    - Qdrant vector embedding and similarity search.
    - Redis short-term memory caching.
    - Memory consolidation (short-term → long-term promotion).
    - TTL-based eviction policies.

Rules:
    - Never instantiates repositories directly.
    - Never creates or touches ``AsyncSession``.
    - Never calls other services.
    - All database access is via ``AbstractUnitOfWork``.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)

_SCORE_MIN = Decimal("0.000")
_SCORE_MAX = Decimal("1.000")


class MemoryService:
    """Service owning business logic for ``MemoryEntry`` management.

    Each public method opens its own ``async with uow`` block, executes one
    atomic business operation, and commits explicitly.  Read-only methods open
    a UoW block but do not call ``commit()``.

    Args:
        uow_factory: A zero-argument callable returning a fresh
            ``AbstractUnitOfWork``.

    Example::

        service = MemoryService(SQLAlchemyUnitOfWork)
        entry = await service.store_memory(
            content="The user prefers concise summaries.",
            namespace="project-x",
            memory_type=MemoryType.SEMANTIC,
            importance_score=0.8,
        )
    """

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        """Initialise with a Unit of Work factory.

        Args:
            uow_factory: Zero-argument callable returning an
                ``AbstractUnitOfWork``.
        """
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_score(score: float, field: str = "importance_score") -> Decimal:
        """Validate and convert a float score to ``Decimal``.

        Args:
            score: Float value to validate.  Must be in ``[0.0, 1.0]``.
            field: Field name used in the error message.

        Returns:
            ``Decimal`` representation with scale 3.

        Raises:
            ValueError: If ``score`` is outside ``[0.0, 1.0]``.
        """
        decimal_score = Decimal(str(round(score, 3)))
        if not (_SCORE_MIN <= decimal_score <= _SCORE_MAX):
            raise ValueError(
                f"{field} must be in [0.0, 1.0], got {score}."
            )
        return decimal_score

    # ------------------------------------------------------------------
    # Create / store
    # ------------------------------------------------------------------

    async def store_memory(
        self,
        content: str,
        namespace: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        agent_run_id: uuid.UUID | None = None,
        importance_score: float = 0.5,
        summary: str | None = None,
        source: str | None = None,
        embedding_id: uuid.UUID | None = None,
        embedding_model: str | None = None,
        entry_metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Create and persist a new ``MemoryEntry``.

        Args:
            content:        Full raw text content of the memory.  Must be
                            non-empty.
            namespace:      Logical partition identifier.  Must be non-empty.
                            All retrieval queries must supply a namespace to
                            prevent cross-project contamination.
            memory_type:    Cognitive classification.  Defaults to ``EPISODIC``.
            agent_run_id:   Optional UUID of the source ``AgentRun``.  Pass
                            ``None`` for globally scoped memories.
            importance_score: Retrieval weight in ``[0.0, 1.0]``.  Defaults
                            to ``0.5``.
            summary:        Optional compressed version of ``content`` for
                            LLM context injection.
            source:         Optional origin reference (file path, URL, tool name).
            embedding_id:   Optional Qdrant point UUID.  Set by the embedding
                            pipeline after vectorisation.
            embedding_model: Model used to produce the embedding.  If set,
                            ``embedding_id`` must also be provided.
            entry_metadata: Arbitrary JSONB context.

        Returns:
            The persisted ``MemoryEntry`` instance.

        Raises:
            ValueError: If ``content`` or ``namespace`` is empty, if
                ``importance_score`` is out of range, or if ``embedding_model``
                is set without ``embedding_id``.
        """
        content = content.strip()
        if not content:
            raise ValueError("MemoryEntry.content must be a non-empty string.")
        namespace = namespace.strip()
        if not namespace:
            raise ValueError("MemoryEntry.namespace must be a non-empty string.")
        score = self._validate_score(importance_score)
        if embedding_model and embedding_id is None:
            raise ValueError(
                "embedding_model may not be set without embedding_id.  "
                "Provide the Qdrant point UUID alongside the model name."
            )

        entry = MemoryEntry(
            id=uuid.uuid4(),
            content=content,
            namespace=namespace,
            memory_type=memory_type,
            agent_run_id=agent_run_id,
            importance_score=score,
            summary=summary,
            source=source,
            embedding_id=embedding_id,
            embedding_model=embedding_model,
            entry_metadata=entry_metadata,
        )
        async with self._uow_factory() as uow:
            entry = await uow.memory_entries.create(entry)
            await uow.commit()

        logger.info(
            "MemoryEntry stored",
            extra={
                "entry_id": str(entry.id),
                "namespace": namespace,
                "memory_type": memory_type.value,
            },
        )
        return entry

    # ------------------------------------------------------------------
    # Read — single entry
    # ------------------------------------------------------------------

    async def get_memory(self, entry_id: uuid.UUID) -> MemoryEntry:
        """Return a single ``MemoryEntry`` by primary key.

        Args:
            entry_id: UUID of the target ``MemoryEntry``.

        Returns:
            The ``MemoryEntry`` instance.

        Raises:
            NoResultFound: If no entry with ``entry_id`` exists.
        """
        async with self._uow_factory() as uow:
            return await uow.memory_entries.get_or_raise(entry_id)

    async def get_by_embedding(
        self,
        embedding_id: uuid.UUID,
    ) -> MemoryEntry | None:
        """Return the entry associated with a Qdrant point ID, or ``None``.

        Used by the embedding pipeline to reconcile Qdrant search results
        with PostgreSQL rows.

        Args:
            embedding_id: UUID of the Qdrant point.

        Returns:
            The ``MemoryEntry`` instance, or ``None`` if not yet linked.
        """
        async with self._uow_factory() as uow:
            return await uow.memory_entries.get_by_embedding_id(embedding_id)

    # ------------------------------------------------------------------
    # Update — access tracking
    # ------------------------------------------------------------------

    async def record_access(self, entry_id: uuid.UUID) -> MemoryEntry:
        """Increment ``access_count`` and refresh ``accessed_at``.

        Called each time a memory entry is injected into an agent context.
        Updates recency state used by the retrieval ranking algorithm.

        Args:
            entry_id: UUID of the target ``MemoryEntry``.

        Returns:
            The updated ``MemoryEntry`` instance.

        Raises:
            NoResultFound: If no entry with ``entry_id`` exists.
        """
        async with self._uow_factory() as uow:
            entry = await uow.memory_entries.increment_access_count(entry_id)
            await uow.commit()

        logger.debug("MemoryEntry access recorded", extra={"entry_id": str(entry_id)})
        return entry

    # ------------------------------------------------------------------
    # Update — importance score
    # ------------------------------------------------------------------

    async def update_importance(
        self,
        entry_id: uuid.UUID,
        importance_score: float,
    ) -> MemoryEntry:
        """Update the importance (retrieval weight) of a memory entry.

        Args:
            entry_id:         UUID of the target ``MemoryEntry``.
            importance_score: New weight in ``[0.0, 1.0]``.

        Returns:
            The updated ``MemoryEntry`` instance.

        Raises:
            ValueError:    If ``importance_score`` is outside ``[0.0, 1.0]``.
            NoResultFound: If no entry with ``entry_id`` exists.
        """
        score = self._validate_score(importance_score)
        async with self._uow_factory() as uow:
            entry = await uow.memory_entries.get_or_raise(entry_id)
            entry = await uow.memory_entries.update(entry, importance_score=score)
            await uow.commit()

        logger.info(
            "MemoryEntry importance updated",
            extra={"entry_id": str(entry_id), "importance_score": str(score)},
        )
        return entry

    # ------------------------------------------------------------------
    # Read — collections
    # ------------------------------------------------------------------

    async def get_top_memories(
        self,
        namespace: str,
        memory_type: MemoryType,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Return the top-N entries ranked by importance score.

        Args:
            namespace:   Logical partition identifier.
            memory_type: Cognitive classification to narrow results.
            limit:       Maximum entries to return.

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``importance_score DESC, accessed_at DESC NULLS LAST``.
        """
        async with self._uow_factory() as uow:
            return await uow.memory_entries.get_top_by_importance(
                namespace, memory_type, limit=limit
            )

    async def get_by_namespace(
        self,
        namespace: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        """Return all entries within a namespace.

        Args:
            namespace: Logical partition identifier.
            limit:     Maximum entries to return.
            offset:    Entries to skip.

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``importance_score DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.memory_entries.get_by_namespace(
                namespace, limit=limit, offset=offset
            )

    async def get_run_memories(
        self,
        agent_run_id: uuid.UUID,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Return all memory entries associated with a run.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            limit:        Maximum entries to return.

        Returns:
            A list of ``MemoryEntry`` instances ordered by
            ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.memory_entries.get_by_agent_run(
                agent_run_id, limit=limit
            )
