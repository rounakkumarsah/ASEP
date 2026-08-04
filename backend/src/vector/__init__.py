"""
ASEP — Vector Package
=======================
Public re-exports for all vector/Qdrant components.

Usage::

    from src.vector import VectorService, VectorRecord, VectorSearchResult
    from src.vector import get_qdrant_client, QdrantClientDep
    from src.vector import DEFAULT_COLLECTION, create_collection_if_not_exists
"""

from src.vector.collections import (
    DEFAULT_COLLECTION,
    DEFAULT_DISTANCE,
    create_collection_if_not_exists,
    delete_collection,
)
from src.vector.embeddings import DEFAULT_VECTOR_SIZE
from src.vector.health import qdrant_health_check
from src.vector.models import VectorRecord, VectorSearchResult
from src.vector.qdrant import (
    QdrantClientDep,
    close_qdrant,
    get_qdrant_client,
    init_qdrant,
    qdrant_dependency,
)
from src.vector.vector_service import VectorService

__all__ = [
    # Collections
    "DEFAULT_COLLECTION",
    "DEFAULT_DISTANCE",
    "create_collection_if_not_exists",
    "delete_collection",
    # Embeddings
    "DEFAULT_VECTOR_SIZE",
    # Health
    "qdrant_health_check",
    # Models
    "VectorRecord",
    "VectorSearchResult",
    # Client
    "QdrantClientDep",
    "close_qdrant",
    "get_qdrant_client",
    "init_qdrant",
    "qdrant_dependency",
    # Service
    "VectorService",
]
