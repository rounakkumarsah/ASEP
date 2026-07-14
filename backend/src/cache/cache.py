"""
ASEP — Cache Abstraction
"""

import json
from typing import Any

from redis.asyncio import Redis


class CacheService:
    """Generic abstraction for key-value caching."""

    def __init__(self, redis: Redis) -> None:
        """Initialise with a Redis client instance."""
        self._redis = redis

    async def get(self, key: str) -> str | None:
        """Get a string value by key."""
        return await self._redis.get(key)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Get and deserialize a JSON value by key."""
        data = await self.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> bool:
        """Set a string value with an optional TTL.
        
        Args:
            key: The cache key.
            value: The string value.
            ttl_seconds: Optional expiration in seconds.
            
        Returns:
            True if successful.
        """
        result = await self._redis.set(key, value, ex=ttl_seconds)
        return bool(result)

    async def set_json(
        self, key: str, value: dict[str, Any], ttl_seconds: int | None = None
    ) -> bool:
        """Serialize and set a JSON value with an optional TTL."""
        data = json.dumps(value)
        return await self.set(key, data, ttl_seconds)

    async def delete(self, key: str) -> bool:
        """Delete a key from the cache.
        
        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        deleted = await self._redis.delete(key)
        return bool(deleted)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        exists = await self._redis.exists(key)
        return bool(exists)
