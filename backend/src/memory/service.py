"""
ASEP — Memory Module (Placeholder)
=====================================
Provides agent memory services:
  - Episodic memory   : past agent actions and observations
  - Semantic memory   : knowledge about the codebase / domain
  - Procedural memory : learned skills and workflows

Storage backends:
  - Short-term : Redis (fast, ephemeral)
  - Long-term  : Qdrant (vector similarity search) + PostgreSQL (structured)

TODO (Phase 0.2):
    - Implement MemoryStore with read/write/search operations
    - Add memory consolidation (short → long term)
    - Add forgetting / TTL policies
    - Add memory retrieval ranking (recency × relevance)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Placeholder memory service.

    TODO (Phase 0.2): implement using Qdrant + Redis + PostgreSQL.
    """

    async def store(self, key: str, value: str, namespace: str = "default") -> None:
        """Persist a memory entry."""
        logger.info("MemoryService.store (stub)", extra={"key": key, "namespace": namespace})
        # TODO (Phase 0.2): embed value and upsert into Qdrant

    async def retrieve(self, query: str, namespace: str = "default", top_k: int = 5) -> list[str]:
        """Retrieve semantically similar memory entries."""
        logger.info("MemoryService.retrieve (stub)", extra={"query": query, "namespace": namespace})
        # TODO (Phase 0.2): embed query, search Qdrant, return top_k results
        return []
