"""
ASEP — Vector Collections Manager
====================================
Creates and ensures Qdrant collections with the correct schema.

Collection name and vector size are fully configurable via environment
variables (QDRANT_COLLECTION and QDRANT_VECTOR_SIZE in settings).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.http.models import Distance

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — driven by settings so tests and callers can override via env.
# ---------------------------------------------------------------------------

DEFAULT_COLLECTION = "asep_documents"


async def create_collection_if_not_exists(
    client: "AsyncQdrantClient",
    collection_name: str | None = None,
    vector_size: int | None = None,
    distance_metric: "Distance | None" = None,
) -> None:
    """
    Ensure a Qdrant collection exists with the correct schema.

    Parameters default to the values in ``settings`` so callers rarely need
    to pass them explicitly.

    Args:
        client:          Qdrant async client.
        collection_name: Collection to create (default: ``settings.QDRANT_COLLECTION``).
        vector_size:     Embedding dimension (default: ``settings.QDRANT_VECTOR_SIZE``).
        distance_metric: Similarity metric (default: Cosine).
    """
    # Lazy import — qdrant_client is an optional heavy dependency
    from qdrant_client.http.models import Distance, VectorParams  # noqa: PLC0415

    if distance_metric is None:
        distance_metric = Distance.COSINE

    settings = get_settings()
    name = collection_name or settings.QDRANT_COLLECTION
    size = vector_size or settings.QDRANT_VECTOR_SIZE

    exists = await client.collection_exists(collection_name=name)
    if not exists:
        logger.info(
            "Creating Qdrant collection '%s' (size=%d, distance=%s)",
            name,
            size,
            distance_metric.name,
        )
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=size, distance=distance_metric),
        )
        logger.info("Qdrant collection '%s' created successfully.", name)
    else:
        logger.debug("Qdrant collection '%s' already exists — skipping creation.", name)


async def delete_collection(
    client: "AsyncQdrantClient",
    collection_name: str,
) -> bool:
    """
    Delete a Qdrant collection.

    Returns True if the collection was deleted, False if it did not exist.
    """
    exists = await client.collection_exists(collection_name=collection_name)
    if not exists:
        logger.warning("Attempted to delete non-existent collection '%s'.", collection_name)
        return False
    await client.delete_collection(collection_name=collection_name)
    logger.info("Qdrant collection '%s' deleted.", collection_name)
    return True
