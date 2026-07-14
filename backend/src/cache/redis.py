"""
ASEP — Redis Client & Connection Pool
"""

import asyncio
import logging
from typing import AsyncGenerator

from redis.asyncio import Redis, from_url

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Redis instance
_redis_client: Redis | None = None


async def init_redis() -> None:
    """Initialise the global Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        
        # 'decode_responses=True' parses strings directly instead of returning bytes.
        # This is generally more convenient for standard caching.
        _redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise


async def close_redis() -> None:
    """Close the global Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        logger.info("Closing Redis connection pool.")
        await _redis_client.close()
        _redis_client = None


def get_redis_client() -> Redis:
    """Get the global Redis client instance.
    
    Raises:
        RuntimeError: If Redis has not been initialized.
    """
    if _redis_client is None:
        raise RuntimeError("Redis client is not initialized. Call init_redis() first.")
    return _redis_client


async def redis_dependency() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency to inject the Redis client."""
    client = get_redis_client()
    yield client
