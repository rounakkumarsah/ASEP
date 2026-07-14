"""
ASEP — Vector Package
"""

from src.vector.collections import DEFAULT_COLLECTION, create_collection_if_not_exists
from src.vector.embeddings import DEFAULT_VECTOR_SIZE
from src.vector.health import qdrant_health_check
from src.vector.models import VectorRecord, VectorSearchResult
from src.vector.qdrant import (
    close_qdrant,
    get_qdrant_client,
    init_qdrant,
    qdrant_dependency,
)
from src.vector.vector_service import VectorService

__all__ = [
    "DEFAULT_COLLECTION",
    "create_collection_if_not_exists",
    "DEFAULT_VECTOR_SIZE",
    "qdrant_health_check",
    "VectorRecord",
    "VectorSearchResult",
    "close_qdrant",
    "get_qdrant_client",
    "init_qdrant",
    "qdrant_dependency",
    "VectorService",
]
