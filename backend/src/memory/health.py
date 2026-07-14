"""
ASEP — Memory Systems Health Check
"""

import logging

from src.cache.health import redis_health_check
from src.db.postgres import check_db_health
from src.graph.health import neo4j_health_check
from src.vector.health import qdrant_health_check

logger = logging.getLogger(__name__)


async def memory_health_check() -> bool:
    """Verifies that all memory storage backends are operational.
    
    Checks:
        - Redis (Working Memory backend)
        - PostgreSQL (Episodic & Procedural Memory backend)
        - Qdrant (Semantic Vector storage)
        - Neo4j (Semantic Graph storage)
        
    Returns:
        True if all subsystems respond successfully, False otherwise.
    """
    try:
        redis_ok = await redis_health_check()
        db_healthy, _, _ = await check_db_health()
        qdrant_ok = await qdrant_health_check()
        neo4j_ok = await neo4j_health_check()
        
        all_ok = redis_ok and db_healthy and qdrant_ok and neo4j_ok
        if not all_ok:
            logger.warning(
                f"Memory sub-system health degraded: "
                f"Redis={redis_ok}, DB={db_healthy}, Qdrant={qdrant_ok}, Neo4j={neo4j_ok}"
            )
        return all_ok
    except Exception as e:
        logger.error(f"Memory systems health check encountered an error: {e}", exc_info=True)
        return False
