"""
ASEP — Working Memory (Redis Backend)
"""

import json
from typing import Any

from src.cache import CacheService


class WorkingMemory:
    """Manages short-term, transient execution states and messages in Redis."""

    def __init__(self, cache_service: CacheService) -> None:
        self.cache = cache_service

    async def set_state(self, session_id: str, key: str, value: Any) -> None:
        """Store transient variable or state for the active run."""
        serialized = json.dumps(value)
        # Namespace keys to prevent collision
        cache_key = f"working_memory:{session_id}:{key}"
        await self.cache.set(cache_key, serialized, ttl_seconds=3600)  # 1 hour default TTL

    async def get_state(self, session_id: str, key: str) -> Any | None:
        """Retrieve a transient state or variable."""
        cache_key = f"working_memory:{session_id}:{key}"
        data = await self.cache.get(cache_key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    async def append_message(self, session_id: str, message: dict[str, Any]) -> None:
        """Append a message string or structured dict to the session history."""
        messages = await self.get_messages(session_id)
        messages.append(message)
        cache_key = f"working_memory:{session_id}:messages"
        await self.cache.set_json(cache_key, {"list": messages}, ttl_seconds=3600)

    async def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve all messages in the active session history."""
        cache_key = f"working_memory:{session_id}:messages"
        data = await self.cache.get_json(cache_key)
        if data and isinstance(data, dict):
            return data.get("list", [])
        return []

    async def clear(self, session_id: str) -> None:
        """Clear all working memory keys associated with the session."""
        cache_key_messages = f"working_memory:{session_id}:messages"
        await self.cache.delete(cache_key_messages)
        
        # Note: In production we could scan and delete wildcard keys under working_memory:{session_id}:*
        # For this phase, standard clearing of messages is sufficient.
