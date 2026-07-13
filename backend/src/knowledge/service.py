"""
ASEP — Knowledge Module (Placeholder)
========================================
Manages structured knowledge about codebases:
  - Code graph (Neo4j)
  - Document index (Qdrant)
  - Entity extraction and linking

TODO (Phase 0.2):
    - Implement CodeGraphService (parse AST → Neo4j nodes/edges)
    - Implement EmbeddingService (chunk code → Qdrant vectors)
    - Implement EntityLinker (link code entities to knowledge graph)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Placeholder knowledge service.

    TODO (Phase 0.2): implement code graph ingestion pipeline.
    """

    async def ingest_codebase(self, path: str) -> None:
        """Ingest a codebase directory into the knowledge graph."""
        logger.info("KnowledgeService.ingest_codebase (stub)", extra={"path": path})
        # TODO (Phase 0.2): parse AST, extract entities, push to Neo4j + Qdrant

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Semantic search over the knowledge graph."""
        logger.info("KnowledgeService.search (stub)", extra={"query": query})
        # TODO (Phase 0.2): embed query → Qdrant search → Neo4j graph expansion
        return []
