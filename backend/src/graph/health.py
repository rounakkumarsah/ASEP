"""
ASEP — Neo4j Health Check
"""

import logging

from src.graph.neo4j import get_neo4j_driver
from src.graph.queries import PING_QUERY
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


async def neo4j_health_check() -> bool:
    """Perform a ping against the global Neo4j driver to verify health.
    
    Returns:
        True if Neo4j responds and the database is accessible, False otherwise.
    """
    try:
        driver = get_neo4j_driver()
        settings = get_settings()
        
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run(PING_QUERY)
            records = await result.data()
            return len(records) > 0 and records[0].get("ping") == 1
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")
        return False
