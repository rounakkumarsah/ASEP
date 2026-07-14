"""
ASEP — Typed Graph Service Abstraction
"""

import logging
from typing import Any, Mapping

from neo4j import AsyncDriver

from src.config.settings import get_settings
from src.graph.models import GraphResult

logger = logging.getLogger(__name__)


class GraphService:
    """Provides a typed abstraction over Neo4j session and query execution."""

    def __init__(self, driver: AsyncDriver) -> None:
        """Initialise with an async Neo4j driver."""
        self._driver = driver
        self._database = get_settings().NEO4J_DATABASE

    async def execute_read(self, query: str, parameters: dict[str, Any] | None = None) -> GraphResult:
        """Execute a read-only Cypher query with automatic transaction retries."""
        parameters = parameters or {}
        
        async def _work(tx: Any) -> GraphResult:
            result = await tx.run(query, parameters)
            records = await result.data()
            summary = await result.consume()
            return GraphResult(
                records=records,
                summary=summary.__dict__ if summary else {}
            )
            
        async with self._driver.session(database=self._database) as session:
            try:
                return await session.execute_read(_work)
            except Exception as e:
                logger.error(f"Error executing read query: {e}", exc_info=True)
                raise

    async def execute_write(self, query: str, parameters: dict[str, Any] | None = None) -> GraphResult:
        """Execute a write Cypher query with automatic transaction retries."""
        parameters = parameters or {}
        
        async def _work(tx: Any) -> GraphResult:
            result = await tx.run(query, parameters)
            records = await result.data()
            summary = await result.consume()
            return GraphResult(
                records=records,
                summary=summary.__dict__ if summary else {}
            )
            
        async with self._driver.session(database=self._database) as session:
            try:
                return await session.execute_write(_work)
            except Exception as e:
                logger.error(f"Error executing write query: {e}", exc_info=True)
                raise
