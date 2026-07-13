"""
ASEP — Qdrant Connection Manager
===================================
Manages the Qdrant async client used for all vector operations:
  - Code embedding search (semantic code retrieval)
  - Memory embedding store (agent episodic memory)
  - Document embedding search (RAG pipeline)

TODO (Phase 0.2):
    - Define collection schemas and create on startup
    - Add collection health check
    - Add embedding dimension configuration
    - Add payload index definitions per collection
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None


def _get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        kwargs: dict = {
            "host": settings.QDRANT_HOST,
            "port": settings.QDRANT_PORT,
        }
        if settings.QDRANT_API_KEY:
            kwargs["api_key"] = settings.QDRANT_API_KEY
        _client = AsyncQdrantClient(**kwargs)
        logger.info(
            "Qdrant async client created",
            extra={"host": settings.QDRANT_HOST, "port": settings.QDRANT_PORT},
        )
    return _client


async def get_qdrant() -> AsyncQdrantClient:
    """
    FastAPI dependency that returns the shared Qdrant async client.

    Usage:
        @router.post("/embed")
        async def embed(qdrant: QdrantClient) -> dict:
            collections = await qdrant.get_collections()
            ...
    """
    return _get_client()


# Annotated alias
QdrantClientDep = Annotated[AsyncQdrantClient, Depends(get_qdrant)]


async def close_qdrant() -> None:
    """Close the Qdrant client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Qdrant client closed")
