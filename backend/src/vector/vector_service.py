"""
ASEP — Typed Vector Service Abstraction
=========================================
Provides a clean, typed API over the Qdrant async client for all
document ingestion and semantic search operations.

All public methods include:
  - Structured logging (no credentials exposed)
  - Retry logic via tenacity
  - Specific exception propagation

Public API
----------
  create_collection()  — ensure a collection exists
  delete_collection()  — remove a collection
  upsert_documents()   — batch upsert VectorRecord objects
  search()             — semantic similarity search
  delete_points()      — remove points by ID
  health_check()       — liveness probe
"""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import get_settings
from src.vector.models import VectorRecord, VectorSearchResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry policy — shared across all network-bound operations
# ---------------------------------------------------------------------------

_RETRY_POLICY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


class VectorService:
    """
    Typed abstraction over Qdrant client operations.

    Inject via FastAPI dependency or instantiate directly in services:

        service = VectorService(client=get_qdrant_client())
    """

    def __init__(self, client: AsyncQdrantClient) -> None:
        """Initialise with a shared Qdrant async client."""
        self._client = client

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def create_collection(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """
        Create a Qdrant collection if it does not already exist.

        Args:
            collection_name: Target collection (default: ``settings.QDRANT_COLLECTION``).
            vector_size:     Embedding dimension (default: ``settings.QDRANT_VECTOR_SIZE``).
            distance:        Distance metric (default: Cosine).

        Returns:
            True if created, False if already existed.
        """
        settings = get_settings()
        name = collection_name or settings.QDRANT_COLLECTION
        size = vector_size or settings.QDRANT_VECTOR_SIZE

        exists = await self._client.collection_exists(collection_name=name)
        if exists:
            logger.debug("Collection '%s' already exists — skipping creation.", name)
            return False

        logger.info(
            "Creating collection '%s' (size=%d, distance=%s)",
            name,
            size,
            distance.name,
        )
        await self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=size, distance=distance),
        )
        logger.info("Collection '%s' created successfully.", name)
        return True

    @retry(**_RETRY_POLICY)
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a Qdrant collection.

        Returns:
            True if deleted, False if it did not exist.
        """
        exists = await self._client.collection_exists(collection_name=collection_name)
        if not exists:
            logger.warning("Cannot delete non-existent collection '%s'.", collection_name)
            return False
        await self._client.delete_collection(collection_name=collection_name)
        logger.info("Collection '%s' deleted.", collection_name)
        return True

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def upsert_documents(
        self,
        collection_name: str,
        records: list[VectorRecord],
    ) -> bool:
        """
        Batch upsert vector records into a collection.

        This is the primary ingestion method used by the document
        ingestion pipeline:

            Upload PDF → Chunk → Embed → upsert_documents()

        Args:
            collection_name: Target collection.
            records:         List of ``VectorRecord`` objects to store.

        Returns:
            True if the operation completed successfully.
        """
        if not records:
            logger.debug("upsert_documents called with empty record list — no-op.")
            return True

        points = [
            PointStruct(id=r.id, vector=r.vector, payload=r.payload)
            for r in records
        ]

        logger.info(
            "Upserting %d vectors into collection '%s'.",
            len(points),
            collection_name,
        )
        result = await self._client.upsert(
            collection_name=collection_name,
            points=points,
        )
        success = result.status.name == "COMPLETED"
        if success:
            logger.info(
                "Upserted %d vectors into '%s' successfully.",
                len(points),
                collection_name,
            )
        else:
            logger.warning(
                "Upsert to '%s' completed with status: %s",
                collection_name,
                result.status.name,
            )
        return success

    # Alias used by older code paths
    async def upsert(self, collection_name: str, record: VectorRecord) -> bool:
        """Upsert a single vector record. Delegates to upsert_documents()."""
        return await self.upsert_documents(collection_name, [record])

    async def batch_upsert(self, collection_name: str, records: list[VectorRecord]) -> bool:
        """Alias for upsert_documents() for backward compatibility."""
        return await self.upsert_documents(collection_name, records)

    # ------------------------------------------------------------------
    # Semantic search (query pipeline)
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        payload_filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
    ) -> list[VectorSearchResult]:
        """
        Semantic similarity search.

        Used in the RAG query pipeline:

            Question → Embed → search() → Top-K → LLM → Answer

        Args:
            collection_name:  Target collection.
            query_vector:     Embedding of the user query.
            limit:            Maximum results to return.
            payload_filters:  Exact-match payload filters (AND-combined).
            score_threshold:  Minimum similarity score (0.0–1.0).

        Returns:
            List of ``VectorSearchResult`` ordered by descending score.
        """
        query_filter: Filter | None = None
        if payload_filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in payload_filters.items()
            ]
            query_filter = Filter(must=conditions)

        logger.debug(
            "Searching '%s' (limit=%d, filters=%s, threshold=%s)",
            collection_name,
            limit,
            payload_filters,
            score_threshold,
        )

        results_response = await self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        results = results_response.points

        logger.debug("Search returned %d results from '%s'.", len(results), collection_name)
        return [
            VectorSearchResult(
                id=str(hit.id),
                score=hit.score,
                payload=hit.payload or {},
                version=hit.version or 0,
            )
            for hit in results
        ]

    # ------------------------------------------------------------------
    # Point deletion
    # ------------------------------------------------------------------

    @retry(**_RETRY_POLICY)
    async def delete_points(self, collection_name: str, point_ids: list[str]) -> bool:
        """
        Delete vector points by ID.

        Args:
            collection_name: Target collection.
            point_ids:       List of point IDs to remove.

        Returns:
            True if the operation completed successfully.
        """
        if not point_ids:
            logger.debug("delete_points called with empty ID list — no-op.")
            return True

        logger.info(
            "Deleting %d points from collection '%s'.",
            len(point_ids),
            collection_name,
        )
        result = await self._client.delete(
            collection_name=collection_name,
            points_selector=point_ids,
        )
        success = result.status.name == "COMPLETED"
        if success:
            logger.info("Deleted %d points from '%s'.", len(point_ids), collection_name)
        return success

    # Alias for backward compatibility
    async def delete(self, collection_name: str, point_ids: list[str]) -> bool:
        """Alias for delete_points()."""
        return await self.delete_points(collection_name, point_ids)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Liveness probe — returns True if Qdrant responds to a collections list.

        Used by the startup sequence and the observability health endpoint.
        Does NOT retry — a single failure is sufficient to mark unhealthy.
        """
        try:
            await self._client.get_collections()
            logger.debug("Qdrant health check passed.")
            return True
        except Exception as exc:
            logger.warning("Qdrant health check failed: %s", str(exc))
            return False
