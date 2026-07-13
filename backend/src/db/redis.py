"""
ASEP — Redis Connection Manager
==================================
Manages an async Redis connection pool used for:
  - Short-lived caching (LLM response cache, tool result cache)
  - Rate limiting counters
  - Pub/Sub for agent event streaming
  - Ephemeral agent state (locks, cursors)

TODO (Phase 0.2):
    - Add cluster mode support
    - Add Lua script registry
    - Add health-check ping method
    - Add key-namespace prefixing per domain
"""

from __future__ import annotations

import logging
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton
_redis_client: aioredis.Redis | None = None


def _get_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client created", extra={"url": settings.REDIS_URL})
    return _redis_client


async def get_redis() -> aioredis.Redis:
    """
    FastAPI dependency that returns the shared Redis client.

    Usage:
        @router.get("/cache")
        async def cached_endpoint(redis: RedisClient) -> dict:
            value = await redis.get("my-key")
            ...
    """
    return _get_client()


# Annotated alias for clean FastAPI signatures
RedisClient = Annotated[aioredis.Redis, Depends(get_redis)]


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis client closed")
