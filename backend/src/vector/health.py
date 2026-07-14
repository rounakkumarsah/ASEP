"""
ASEP — Qdrant Health Check
"""

import logging

from src.vector.qdrant import get_qdrant_client

logger = logging.getLogger(__name__)


async def qdrant_health_check() -> bool:
    """Perform a ping against the global Qdrant client to verify health.
    
    Returns:
        True if Qdrant responds and cluster info is accessible, False otherwise.
    """
    try:
        client = get_qdrant_client()
        # Verify connectivity by getting collection list
        await client.get_collections()
        return True
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        return False
