"""
ASEP — Vector Collections Manager
"""

import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.vector.embeddings import DEFAULT_VECTOR_SIZE

logger = logging.getLogger(__name__)

# Default sandbox collection name
DEFAULT_COLLECTION = "asep_default"


async def create_collection_if_not_exists(
    client: AsyncQdrantClient,
    collection_name: str = DEFAULT_COLLECTION,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    distance_metric: Distance = Distance.COSINE,
) -> None:
    """Ensure a Qdrant collection exists with the specified parameters."""
    exists = await client.collection_exists(collection_name=collection_name)
    if not exists:
        logger.info(f"Creating Qdrant collection '{collection_name}' (size={vector_size}, distance={distance_metric.name})")
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance_metric)
        )
    else:
        logger.debug(f"Qdrant collection '{collection_name}' already exists.")
