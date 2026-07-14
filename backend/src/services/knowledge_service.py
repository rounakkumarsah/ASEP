"""
ASEP — KnowledgeService
=========================
Business logic for the ``KnowledgeDocument`` catalog.

Responsibilities:
    - Validate inputs (document_name, title non-empty; trust_score in
      [0.0, 1.0]; state transitions legal).
    - Convert Python ``float`` trust scores to ``Decimal`` for the ORM.
    - Orchestrate the document ingestion status pipeline:
      ``PENDING → INDEXING → READY`` (or ``→ FAILED``).
    - Expose read queries for the crawl queue, retrieval pipeline, and
      deduplication checks.
    - Commit the transaction explicitly after every mutating operation.
    - Return ORM entities; DTO mapping belongs to the API layer.

Out of scope for Phase 0.6:
    - Crawling / fetching remote documents (Crawl4AI integration).
    - Text chunking and extraction.
    - Embedding generation and Qdrant ingestion.
    - Neo4j graph node creation.

Rules:
    - Never instantiates repositories directly.
    - Never creates or touches ``AsyncSession``.
    - Never calls other services.
    - All database access is via ``AbstractUnitOfWork``.

Document status pipeline::

    PENDING ──mark_indexing──► INDEXING ──mark_ready──► READY ──archive──► ARCHIVED
    PENDING ──mark_indexing──► INDEXING ──mark_failed──► FAILED
    FAILED  ──mark_indexing──► INDEXING  (retry path)
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.db.models.knowledge_document import (
    CrawlStatus,
    DocumentSourceType,
    DocumentStatus,
    KnowledgeDocument,
)
from src.services.exceptions import InvalidStateError
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)

_TRUST_MIN = Decimal("0.000")
_TRUST_MAX = Decimal("1.000")

# Status transitions
_INDEXING_ALLOWED: frozenset[DocumentStatus] = frozenset(
    {DocumentStatus.PENDING, DocumentStatus.FAILED}
)
_READY_ALLOWED: frozenset[DocumentStatus] = frozenset({DocumentStatus.INDEXING})
_FAILED_ALLOWED: frozenset[DocumentStatus] = frozenset({DocumentStatus.INDEXING})
_ARCHIVE_ALLOWED: frozenset[DocumentStatus] = frozenset({DocumentStatus.READY})


class KnowledgeService:
    """Service owning the business logic for the ``KnowledgeDocument`` catalog.

    Each public method opens its own ``async with uow`` block, executes one
    atomic business operation, and commits explicitly.  Read-only methods open
    a UoW block but do not call ``commit()``.

    Args:
        uow_factory: A zero-argument callable returning a fresh
            ``AbstractUnitOfWork``.

    Example::

        service = KnowledgeService(SQLAlchemyUnitOfWork)
        doc = await service.register_document(
            document_name="fastapi_docs_v1",
            title="FastAPI Official Documentation",
            source_type=DocumentSourceType.WEB,
            source_url="https://fastapi.tiangolo.com",
            language="en",
        )
        doc = await service.mark_indexing(doc.id)
        doc = await service.mark_ready(doc.id, chunk_count=412, embedding_count=412)
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
    def _validate_trust(trust_score: float) -> Decimal:
        """Validate and convert a float trust score to ``Decimal``.

        Args:
            trust_score: Float value to validate.  Must be in ``[0.0, 1.0]``.

        Returns:
            ``Decimal`` representation with scale 3.

        Raises:
            ValueError: If ``trust_score`` is outside ``[0.0, 1.0]``.
        """
        decimal_score = Decimal(str(round(trust_score, 3)))
        if not (_TRUST_MIN <= decimal_score <= _TRUST_MAX):
            raise ValueError(
                f"trust_score must be in [0.0, 1.0], got {trust_score}."
            )
        return decimal_score

    def _guard_transition(
        self,
        doc: KnowledgeDocument,
        allowed: frozenset[DocumentStatus],
        transition: str,
    ) -> None:
        """Raise ``InvalidStateError`` if ``doc.status`` is not in ``allowed``.

        Args:
            doc:        The ``KnowledgeDocument`` being transitioned.
            allowed:    Set of statuses from which the transition is legal.
            transition: Human-readable name of the transition.

        Raises:
            InvalidStateError: If ``doc.status not in allowed``.
        """
        if doc.status not in allowed:
            raise InvalidStateError(
                entity_type="KnowledgeDocument",
                entity_id=doc.id,
                current_status=doc.status.value,
                attempted_transition=transition,
            )

    # ------------------------------------------------------------------
    # Register — create catalog entry
    # ------------------------------------------------------------------

    async def register_document(
        self,
        document_name: str,
        title: str,
        source_type: DocumentSourceType,
        *,
        description: str | None = None,
        source_url: str | None = None,
        local_path: str | None = None,
        repository_url: str | None = None,
        repository_branch: str | None = None,
        version: str | None = None,
        checksum_sha256: str | None = None,
        content_hash: str | None = None,
        language: str | None = None,
        encoding: str | None = None,
        trust_score: float = 0.5,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        created_by: str | None = None,
        document_metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Register a new document in the Knowledge Layer catalog.

        Creates the ``KnowledgeDocument`` row with ``status=PENDING``.
        The ingestion pipeline is responsible for transitioning it through
        ``INDEXING → READY``.

        Args:
            document_name:     Technical slug or identifier
                               (e.g. ``"fastapi_docs_v1"``).  Must be
                               non-empty.
            title:             Human-readable display name.  Must be non-empty.
            source_type:       Origin format or system
                               (``WEB``, ``PDF``, ``GITHUB``, etc.).
            description:       Optional abstract or summary.
            source_url:        Original URL if fetched from the web.
            local_path:        Filesystem path if ingested locally.
            repository_url:    Git repository URL if applicable.
            repository_branch: Git branch name if applicable.
            version:           Explicit version string (e.g. ``"v1.0.0"``).
            checksum_sha256:   SHA-256 hash of the raw file (64 hex chars).
            content_hash:      Hash of the extracted text content (64 hex chars).
            language:          ISO 639-1 language code (e.g. ``"en"``).
            encoding:          Character encoding (e.g. ``"utf-8"``).
            trust_score:       Authority weight in ``[0.0, 1.0]``.
                               Defaults to ``0.5``.
            mime_type:         MIME type of the raw document.
            file_size_bytes:   Size of the raw document in bytes.
            created_by:        Opaque creator identifier.
            document_metadata: Arbitrary JSONB context.

        Returns:
            The persisted ``KnowledgeDocument`` instance with
            ``status=PENDING``.

        Raises:
            ValueError: If ``document_name`` or ``title`` is empty, or if
                ``trust_score`` is out of range.
        """
        document_name = document_name.strip()
        if not document_name:
            raise ValueError("KnowledgeDocument.document_name must be non-empty.")
        title = title.strip()
        if not title:
            raise ValueError("KnowledgeDocument.title must be non-empty.")
        trust = self._validate_trust(trust_score)

        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            document_name=document_name,
            title=title,
            source_type=source_type,
            status=DocumentStatus.PENDING,
            description=description,
            source_url=source_url,
            local_path=local_path,
            repository_url=repository_url,
            repository_branch=repository_branch,
            version=version,
            checksum_sha256=checksum_sha256,
            content_hash=content_hash,
            language=language,
            encoding=encoding,
            trust_score=trust,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            created_by=created_by,
            document_metadata=document_metadata,
        )
        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.create(doc)
            await uow.commit()

        logger.info(
            "KnowledgeDocument registered",
            extra={
                "doc_id": str(doc.id),
                "document_name": document_name,
                "source_type": source_type.value,
            },
        )
        return doc

    # ------------------------------------------------------------------
    # Read — single document
    # ------------------------------------------------------------------

    async def get_document(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Return a single ``KnowledgeDocument`` by primary key.

        Args:
            doc_id: UUID of the target ``KnowledgeDocument``.

        Returns:
            The ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound: If no document with ``doc_id`` exists.
        """
        async with self._uow_factory() as uow:
            return await uow.knowledge_documents.get_or_raise(doc_id)

    # ------------------------------------------------------------------
    # Status pipeline transitions
    # ------------------------------------------------------------------

    async def mark_indexing(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Transition a ``PENDING`` or ``FAILED`` document to ``INDEXING``.

        Called by the ingestion pipeline at the start of the
        chunk-embed-graph cycle.

        Args:
            doc_id: UUID of the target ``KnowledgeDocument``.

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound:    If no document with ``doc_id`` exists.
            InvalidStateError: If the document is not in ``PENDING`` or
                ``FAILED`` state.
        """
        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.get_or_raise(doc_id)
            self._guard_transition(doc, _INDEXING_ALLOWED, "mark_indexing")
            doc = await uow.knowledge_documents.update(
                doc, status=DocumentStatus.INDEXING
            )
            await uow.commit()

        logger.info("KnowledgeDocument indexing started", extra={"doc_id": str(doc_id)})
        return doc

    async def mark_ready(
        self,
        doc_id: uuid.UUID,
        *,
        chunk_count: int | None = None,
        embedding_count: int | None = None,
        graph_node_count: int | None = None,
        vector_collection: str | None = None,
        embedding_model: str | None = None,
        embedding_dimension: int | None = None,
        graph_namespace: str | None = None,
        graph_version: str | None = None,
        last_indexed_at: datetime | None = None,
    ) -> KnowledgeDocument:
        """Transition an ``INDEXING`` document to ``READY``.

        Updates optional telemetry fields that describe what was produced
        during the indexing run.

        Args:
            doc_id:             UUID of the target ``KnowledgeDocument``.
            chunk_count:        Number of semantic chunks extracted.
            embedding_count:    Number of embedding vectors generated.
            graph_node_count:   Number of Neo4j nodes/relationships created.
            vector_collection:  Qdrant collection housing the vectors.
            embedding_model:    Model used to generate the embeddings.
            embedding_dimension: Dimensionality of the embedding vectors.
            graph_namespace:    Neo4j label/partition.
            graph_version:      Ontology or pipeline version used.
            last_indexed_at:    Timestamp of successful indexing completion.
                                Defaults to the current UTC time if omitted.

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound:    If no document with ``doc_id`` exists.
            InvalidStateError: If the document is not in ``INDEXING`` state.
        """
        from datetime import timezone as _tz

        updates: dict[str, Any] = {"status": DocumentStatus.READY}
        if chunk_count is not None:
            updates["chunk_count"] = chunk_count
        if embedding_count is not None:
            updates["embedding_count"] = embedding_count
        if graph_node_count is not None:
            updates["graph_node_count"] = graph_node_count
        if vector_collection is not None:
            updates["vector_collection"] = vector_collection
        if embedding_model is not None:
            updates["embedding_model"] = embedding_model
        if embedding_dimension is not None:
            updates["embedding_dimension"] = embedding_dimension
        if graph_namespace is not None:
            updates["graph_namespace"] = graph_namespace
        if graph_version is not None:
            updates["graph_version"] = graph_version
        updates["last_indexed_at"] = last_indexed_at or datetime.now(tz=_tz.utc)

        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.get_or_raise(doc_id)
            self._guard_transition(doc, _READY_ALLOWED, "mark_ready")
            doc = await uow.knowledge_documents.update(doc, **updates)
            await uow.commit()

        logger.info("KnowledgeDocument marked READY", extra={"doc_id": str(doc_id)})
        return doc

    async def mark_failed(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Transition an ``INDEXING`` document to ``FAILED``.

        Called when the ingestion pipeline encounters an unrecoverable error.
        The document can be retried by calling ``mark_indexing()`` again.

        Args:
            doc_id: UUID of the target ``KnowledgeDocument``.

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound:    If no document with ``doc_id`` exists.
            InvalidStateError: If the document is not in ``INDEXING`` state.
        """
        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.get_or_raise(doc_id)
            self._guard_transition(doc, _FAILED_ALLOWED, "mark_failed")
            doc = await uow.knowledge_documents.update(
                doc, status=DocumentStatus.FAILED
            )
            await uow.commit()

        logger.warning("KnowledgeDocument indexing failed", extra={"doc_id": str(doc_id)})
        return doc

    async def archive_document(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Transition a ``READY`` document to ``ARCHIVED``.

        Archived documents are excluded from active retrieval queries but
        remain in the catalog for audit and lineage purposes.

        Args:
            doc_id: UUID of the target ``KnowledgeDocument``.

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound:    If no document with ``doc_id`` exists.
            InvalidStateError: If the document is not in ``READY`` state.
        """
        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.get_or_raise(doc_id)
            self._guard_transition(doc, _ARCHIVE_ALLOWED, "archive")
            doc = await uow.knowledge_documents.update(
                doc, status=DocumentStatus.ARCHIVED
            )
            await uow.commit()

        logger.info("KnowledgeDocument archived", extra={"doc_id": str(doc_id)})
        return doc

    # ------------------------------------------------------------------
    # Crawl status management
    # ------------------------------------------------------------------

    async def update_crawl_status(
        self,
        doc_id: uuid.UUID,
        crawl_status: CrawlStatus,
    ) -> KnowledgeDocument:
        """Update the crawl lifecycle state of a document.

        ``crawl_status`` is independent of ``status``.  It tracks the
        external fetch phase (Crawl4AI / HTTP request) separately from the
        overall document readiness state.

        Args:
            doc_id:       UUID of the target ``KnowledgeDocument``.
            crawl_status: New ``CrawlStatus`` value
                          (``PENDING``, ``CRAWLING``, ``SUCCESS``,
                          ``FAILED``).

        Returns:
            The updated ``KnowledgeDocument`` instance.

        Raises:
            NoResultFound: If no document with ``doc_id`` exists.
        """
        async with self._uow_factory() as uow:
            doc = await uow.knowledge_documents.get_or_raise(doc_id)
            doc = await uow.knowledge_documents.update(
                doc, crawl_status=crawl_status
            )
            await uow.commit()

        logger.info(
            "KnowledgeDocument crawl_status updated",
            extra={"doc_id": str(doc_id), "crawl_status": crawl_status.value},
        )
        return doc

    # ------------------------------------------------------------------
    # Read — deduplication
    # ------------------------------------------------------------------

    async def find_by_checksum(
        self,
        checksum_sha256: str,
    ) -> KnowledgeDocument | None:
        """Return the document whose raw-file SHA-256 hash matches.

        Called before ``register_document`` to prevent duplicate ingestion.

        Args:
            checksum_sha256: 64-character hexadecimal SHA-256 hash of the
                             raw file bytes.

        Returns:
            The ``KnowledgeDocument`` instance, or ``None`` if no match.
        """
        async with self._uow_factory() as uow:
            return await uow.knowledge_documents.get_by_checksum(checksum_sha256)

    # ------------------------------------------------------------------
    # Read — pipeline and retrieval queries
    # ------------------------------------------------------------------

    async def get_ready_documents(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        """Return fully indexed documents available for retrieval.

        Args:
            limit:  Maximum documents to return.
            offset: Documents to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances with ``status=READY``,
            ordered by ``trust_score DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.knowledge_documents.get_ready(
                limit=limit, offset=offset
            )

    async def get_pending_crawl(self, limit: int = 50) -> list[KnowledgeDocument]:
        """Return documents whose crawl status is ``PENDING``.

        Used by the Crawl4AI integration to build the next fetch batch.

        Args:
            limit: Maximum documents to return.

        Returns:
            A list of ``KnowledgeDocument`` instances with
            ``crawl_status=PENDING``, ordered by ``created_at ASC``.
        """
        async with self._uow_factory() as uow:
            return await uow.knowledge_documents.get_pending_crawl(limit=limit)

    async def list_by_source_type(
        self,
        source_type: DocumentSourceType,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        """Return documents filtered by origin format/system.

        Args:
            source_type: Origin format (``WEB``, ``PDF``, ``GITHUB``, etc.).
            limit:       Maximum documents to return.
            offset:      Documents to skip.

        Returns:
            A list of ``KnowledgeDocument`` instances ordered by
            ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.knowledge_documents.get_by_source_type(
                source_type, limit=limit, offset=offset
            )
