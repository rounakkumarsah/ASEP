"""
ASEP — KnowledgeDocumentRepository
=====================================
Async repository for the ``KnowledgeDocument`` ORM model.

Extends ``BaseRepository`` with domain-specific query methods scoped to the
``knowledge_documents`` table.  All methods leverage the indexes declared on
the model and never call ``session.commit()``, ``session.rollback()``, or
``session.begin()``.

Query hot-paths covered:
    - Content deduplication: ``get_by_checksum``, ``get_by_content_hash``
    - Source breakdown: ``get_by_source_type``
    - Ingestion pipeline: ``get_by_status``, ``get_pending_crawl``, ``update_status``
    - Graph partition: ``get_by_namespace``
    - Vector partition: ``get_by_collection``
    - Retrieval ranking: ``get_by_language_and_min_trust``, ``get_ready``
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from src.db.models.knowledge_document import (
    CrawlStatus,
    DocumentSourceType,
    DocumentStatus,
    KnowledgeDocument,
)
from src.repositories.base import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    BaseRepository,
    _clamp_limit,
)


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument, uuid.UUID]):
    """Async repository for ``KnowledgeDocument`` persistence and catalog queries.

    Inherits CRUD primitives from ``BaseRepository``.  Adds query methods
    that map directly to the indexes on ``knowledge_documents``:

    - ``ix_knowledgedocument_checksum``
    - ``ix_knowledgedocument_content_hash``
    - ``ix_knowledgedocument_source_type``
    - ``ix_knowledgedocument_status``
    - ``ix_knowledgedocument_graph_namespace``
    - ``ix_knowledgedocument_vector_collection``
    - ``ix_knowledgedocument_trust_score``
    - ``ix_knowledgedocument_last_synced_at``
    - ``ix_knowledgedocument_source_status`` (composite)
    - ``ix_knowledgedocument_graph_status`` (composite)
    - ``ix_knowledgedocument_lang_trust`` (composite)

    Attributes:
        _model: Bound to ``KnowledgeDocument``.

    Example::

        repo = KnowledgeDocumentRepository(session)
        duplicate = await repo.get_by_checksum(sha256_hex)
    """

    _model = KnowledgeDocument

    # ------------------------------------------------------------------
    # Content deduplication
    # ------------------------------------------------------------------

    async def get_by_checksum(
        self,
        checksum_sha256: str,
        *options: ExecutableOption,
    ) -> KnowledgeDocument | None:
        """Return the document whose raw-file SHA-256 hash matches.

        Uses ``ix_knowledgedocument_checksum``.  Called by the ingestion
        pipeline before creating a new document to prevent duplicate storage.

        Args:
            checksum_sha256: 64-character hexadecimal SHA-256 hash of the
                             raw file bytes.
            *options:        SQLAlchemy loader strategy options.

        Returns:
            The ``KnowledgeDocument`` instance, or ``None`` if no document
            with this checksum has been ingested.
        """
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.checksum_sha256 == checksum_sha256
        )
        if options:
            stmt = stmt.options(*options)
        return await self._session.scalar(stmt)

    async def get_by_content_hash(
        self,
        content_hash: str,
        *options: ExecutableOption,
    ) -> KnowledgeDocument | None:
        """Return the document whose extracted-text content hash matches.

        Uses ``ix_knowledgedocument_content_hash``.  The content hash
        targets the logical text content (post-extraction) rather than the
        raw file bytes, enabling deduplication even when file metadata
        (e.g. PDF headers) changes.

        Args:
            content_hash: 64-character hexadecimal hash of extracted text.
            *options:     SQLAlchemy loader strategy options.

        Returns:
            The ``KnowledgeDocument`` instance, or ``None`` if no match
            exists.
        """
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.content_hash == content_hash
        )
        if options:
            stmt = stmt.options(*options)
        return await self._session.scalar(stmt)

    # ------------------------------------------------------------------
    # Source breakdown
    # ------------------------------------------------------------------

    async def get_by_source_type(
        self,
        source_type: DocumentSourceType,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[KnowledgeDocument]:
        """Return documents by source type, sorted by creation date.

        Uses ``ix_knowledgedocument_source_type``.

        Args:
            source_type: Origin format/system
                         (``WEB``, ``PDF``, ``GITHUB``, etc.).
            *options:    SQLAlchemy loader strategy options.
            limit:       Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:      Rows to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances ordered by
            ``created_at DESC``.
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.source_type == source_type)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Ingestion pipeline — status filtering
    # ------------------------------------------------------------------

    async def get_by_status(
        self,
        status: DocumentStatus,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[KnowledgeDocument]:
        """Return documents in a given readiness state.

        Uses ``ix_knowledgedocument_status``.

        Args:
            status:   The ``DocumentStatus`` value to filter on
                      (``PENDING``, ``INDEXING``, ``READY``, etc.).
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances ordered by
            ``created_at ASC`` (oldest pending first, consistent with queue
            processing semantics).
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.status == status)
            .order_by(KnowledgeDocument.created_at.asc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Graph partition
    # ------------------------------------------------------------------

    async def get_by_namespace(
        self,
        graph_namespace: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[KnowledgeDocument]:
        """Return all documents mapped to a given Neo4j graph namespace.

        Uses ``ix_knowledgedocument_graph_namespace``.

        Args:
            graph_namespace: Neo4j label or partition name.
            *options:        SQLAlchemy loader strategy options.
            limit:           Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:          Rows to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances ordered by
            ``trust_score DESC``.
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.graph_namespace == graph_namespace)
            .order_by(KnowledgeDocument.trust_score.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Vector partition
    # ------------------------------------------------------------------

    async def get_by_collection(
        self,
        vector_collection: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[KnowledgeDocument]:
        """Return all documents housed in a given Qdrant vector collection.

        Uses ``ix_knowledgedocument_vector_collection``.

        Args:
            vector_collection: Qdrant collection name.
            *options:          SQLAlchemy loader strategy options.
            limit:             Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:            Rows to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances ordered by
            ``trust_score DESC``.
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.vector_collection == vector_collection)
            .order_by(KnowledgeDocument.trust_score.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Ingestion pipeline — documents awaiting crawl
    # ------------------------------------------------------------------

    async def get_pending_crawl(
        self,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[KnowledgeDocument]:
        """Return documents whose crawl status is ``PENDING``.

        Uses the composite index ``ix_knowledgedocument_source_status`` to
        avoid a full table scan when the crawl queue is long.

        Args:
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``KnowledgeDocument`` instances with
            ``crawl_status == PENDING``, ordered by ``created_at ASC``
            (oldest-first queue semantics).
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.crawl_status == CrawlStatus.PENDING)
            .order_by(KnowledgeDocument.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Retrieval ranking — language + trust threshold
    # ------------------------------------------------------------------

    async def get_by_language_and_min_trust(
        self,
        language: str,
        min_trust_score: Decimal,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[KnowledgeDocument]:
        """Return ready documents in a language above a trust threshold.

        Uses the composite index ``ix_knowledgedocument_lang_trust``.
        The ``MemoryService`` calls this to build a ranked candidate set
        before vector similarity re-ranking.

        Args:
            language:        ISO 639-1 language code (e.g. ``"en"``).
            min_trust_score: Minimum ``trust_score`` (inclusive), in
                             ``[0.000, 1.000]``.
            *options:        SQLAlchemy loader strategy options.
            limit:           Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of ``KnowledgeDocument`` instances with status ``READY``
            in the given language with ``trust_score >= min_trust_score``,
            ordered by ``trust_score DESC``.
        """
        stmt = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.language == language,
                KnowledgeDocument.trust_score >= min_trust_score,
                KnowledgeDocument.status == DocumentStatus.READY,
            )
            .order_by(KnowledgeDocument.trust_score.desc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Fully indexed documents (status == READY)
    # ------------------------------------------------------------------

    async def get_ready(
        self,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[KnowledgeDocument]:
        """Return documents that are fully indexed and ready for retrieval.

        Uses ``ix_knowledgedocument_status``.  Returns all documents with
        ``status == READY``, ordered by ``trust_score DESC`` so
        higher-authority sources appear first.

        Args:
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances with
            ``status == READY``, ordered by ``trust_score DESC``.
        """
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.status == DocumentStatus.READY)
            .order_by(KnowledgeDocument.trust_score.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Status transition helper
    # ------------------------------------------------------------------

    async def update_status(
        self,
        doc_id: uuid.UUID,
        status: DocumentStatus,
    ) -> KnowledgeDocument:
        """Transition a ``KnowledgeDocument`` to a new readiness state.

        Fetches the document by primary key, sets ``status``, and flushes.

        Args:
            doc_id: UUID of the target ``KnowledgeDocument``.
            status: New ``DocumentStatus`` value.

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound: If no ``KnowledgeDocument`` with ``doc_id`` exists.
        """
        document = await self.get_or_raise(doc_id)
        return await self.update(document, status=status)
