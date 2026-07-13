"""
ASEP — Neo4j Connection Manager
==================================
Manages the async Neo4j driver used for the code knowledge graph.

Intended uses:
  - Code graph (file → module → class → function relationships)
  - Dependency graph (package imports, call chains)
  - Agent knowledge graph (entity extraction from codebases)

TODO (Phase 0.2):
    - Implement graph schema constraints / indices on startup
    - Add query helper for common Cypher patterns
    - Add health-check RETURN 1 query
    - Add connection pool monitoring
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends
from neo4j import AsyncDriver, AsyncGraphDatabase

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None


def _get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        logger.info("Neo4j async driver created", extra={"uri": settings.NEO4J_URI})
    return _driver


async def get_neo4j() -> AsyncDriver:
    """
    FastAPI dependency that returns the shared Neo4j async driver.

    Usage:
        @router.get("/graph")
        async def graph_endpoint(driver: Neo4jDriver) -> dict:
            async with driver.session() as session:
                result = await session.run("MATCH (n) RETURN count(n)")
                ...
    """
    return _get_driver()


# Annotated alias
Neo4jDriver = Annotated[AsyncDriver, Depends(get_neo4j)]


async def close_neo4j() -> None:
    """Close the Neo4j driver and all its connections."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")
