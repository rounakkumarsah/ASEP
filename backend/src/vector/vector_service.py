"""
ASEP — Typed Vector Service Abstraction
"""

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
)

from src.vector.collections import DEFAULT_COLLECTION
from src.vector.models import VectorRecord, VectorSearchResult

logger = logging.getLogger(__name__)


class VectorService:
    """Provides a typed abstraction over Qdrant client operations."""

    def __init__(self, client: AsyncQdrantClient) -> None:
        """Initialise with an async Qdrant client."""
        self._client = client

    async def upsert(self, collection_name: str, record: VectorRecord) -> bool:
        """Upsert a single vector record."""
        return await self.batch_upsert(collection_name, [record])

    async def batch_upsert(self, collection_name: str, records: list[VectorRecord]) -> bool:
        """Batch upsert multiple vector records."""
        if not records:
            return True
            
        points = [
            PointStruct(
                id=record.id,
                vector=record.vector,
                payload=record.payload
            )
            for record in records
        ]
        
        try:
            update_result = await self._client.upsert(
                collection_name=collection_name,
                points=points
            )
            return update_result.status.name == "COMPLETED"
        except Exception as e:
            logger.error(f"Error during batch upsert to '{collection_name}': {e}", exc_info=True)
            raise

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        payload_filters: dict[str, Any] | None = None
    ) -> list[VectorSearchResult]:
        """Search for similar vectors, optionally filtering by exact payload matches."""
        query_filter = None
        
        if payload_filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in payload_filters.items()
            ]
            query_filter = Filter(must=conditions)

        try:
            results = await self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            
            return [
                VectorSearchResult(
                    id=hit.id,
                    score=hit.score,
                    payload=hit.payload or {},
                    version=hit.version
                )
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Error searching '{collection_name}': {e}", exc_info=True)
            raise

    async def delete(self, collection_name: str, point_ids: list[str]) -> bool:
        """Delete vectors by ID."""
        if not point_ids:
            return True
            
        try:
            update_result = await self._client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
            return update_result.status.name == "COMPLETED"
        except Exception as e:
            logger.error(f"Error deleting points from '{collection_name}': {e}", exc_info=True)
            raise
