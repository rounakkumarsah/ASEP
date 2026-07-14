"""
ASEP — Neo4j Driver Connection Pool
"""

import logging
from typing import AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Neo4j AsyncDriver instance
_neo4j_driver: AsyncDriver | None = None


async def init_neo4j() -> None:
    """Initialise the global Neo4j driver connection pool."""
    global _neo4j_driver
    if _neo4j_driver is None:
        settings = get_settings()
        logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}")
        
        try:
            _neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Verify connectivity
            await _neo4j_driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise


async def close_neo4j() -> None:
    """Close the global Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        logger.info("Closing Neo4j connection pool.")
        await _neo4j_driver.close()
        _neo4j_driver = None


def get_neo4j_driver() -> AsyncDriver:
    """Get the global Neo4j driver instance.
    
    Raises:
        RuntimeError: If Neo4j has not been initialized.
    """
    if _neo4j_driver is None:
        raise RuntimeError("Neo4j driver is not initialized. Call init_neo4j() first.")
    return _neo4j_driver


async def neo4j_driver_dependency() -> AsyncGenerator[AsyncDriver, None]:
    """FastAPI dependency to inject the Neo4j driver."""
    driver = get_neo4j_driver()
    yield driver
