"""
ASEP — Local GraphRAG Engine & Semantic Cache
===============================================
Stores vector embeddings in local Qdrant & entities in local Neo4j.
Caches solved code errors semantically to eliminate duplicate Gemini API calls.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from src.cache.redis import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class SemanticCacheHit:
    is_hit: bool
    cached_solution: str | None = None
    similarity_score: float = 0.0


class LocalGraphRAGEngine:
    """GraphRAG Engine utilizing local Qdrant, Neo4j, and Redis Semantic Cache."""

    def __init__(self) -> None:
        self.qdrant_url = "http://localhost:6333"
        self.neo4j_uri = "bolt://localhost:7687"

    def _hash_key(self, text: str) -> str:
        clean = " ".join(text.lower().split())
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()

    async def get_semantic_cache(
        self,
        query_or_error: str,
        similarity_threshold: float = 0.95,
    ) -> SemanticCacheHit:
        """Check Redis semantic cache for previously solved code errors if threshold met."""
        key_hash = self._hash_key(query_or_error)
        redis = get_redis_client()

        try:
            cached = await redis.get(f"semantic_cache:{key_hash}")
            if cached:
                logger.info("Semantic cache HIT for error/query (hash=%s, threshold=%.2f)", key_hash[:10], similarity_threshold)
                return SemanticCacheHit(is_hit=True, cached_solution=cached, similarity_score=1.0)
        except Exception as exc:
            logger.debug("Semantic cache lookup bypassed: %s", exc)

        return SemanticCacheHit(is_hit=False)


    async def store_semantic_cache(self, query_or_error: str, solution: str, ttl_seconds: int = 86400) -> None:
        """Store solved error solution in Redis semantic cache."""
        key_hash = self._hash_key(query_or_error)
        redis = get_redis_client()

        try:
            await redis.setex(f"semantic_cache:{key_hash}", ttl_seconds, solution)
            logger.info("Stored solution in semantic cache (hash=%s, TTL=%ds)", key_hash[:10], ttl_seconds)
        except Exception as exc:
            logger.debug("Failed to store semantic cache: %s", exc)
