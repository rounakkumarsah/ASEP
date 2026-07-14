"""
ASEP — Redis Health Check
"""

from typing import Annotated

from fastapi import Depends

from src.cache.redis import get_redis_client


async def redis_health_check() -> bool:
    """Perform a ping against the global Redis client to verify health.
    
    Returns:
        True if Redis responds to PING, False otherwise.
    """
    try:
        client = get_redis_client()
        return await client.ping()
    except Exception:
        return False
