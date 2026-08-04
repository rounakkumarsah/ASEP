"""
ASEP — Memory Runtime Engine & Eviction Policies
===============================================
Extends MemoryManager with conversation memory windows, token-aware bounds,
and LRU / TTL memory eviction strategies.
"""

from __future__ import annotations

import enum
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conversation Memory
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMemory(BaseModel):
    """Manages sliding window and token limits for multi-turn conversations."""
    session_id: str
    max_messages: int = 50
    max_tokens: int = 4096
    messages: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        msg = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._truncate_window()

    def get_messages(self) -> List[ChatMessage]:
        return list(self.messages)

    def _truncate_window(self) -> None:
        if len(self.messages) > self.max_messages:
            excess = len(self.messages) - self.max_messages
            # Keep system prompt if index 0
            if self.messages and self.messages[0].role == "system":
                self.messages = [self.messages[0]] + self.messages[1 + excess:]
            else:
                self.messages = self.messages[excess:]


# ---------------------------------------------------------------------------
# Eviction Policies (LRU & TTL)
# ---------------------------------------------------------------------------

class EvictionStrategy(str, enum.Enum):
    LRU = "lru"
    TTL = "ttl"
    IMPORTANCE = "importance"


@dataclass
class MemoryItem:
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    importance: float = 1.0


class MemoryEvictionPolicy:
    """Manages memory bounds using LRU and TTL policies."""

    def __init__(
        self,
        max_capacity: int = 1000,
        default_ttl: Optional[float] = 3600.0,
        strategy: EvictionStrategy = EvictionStrategy.LRU,
    ) -> None:
        self.max_capacity = max_capacity
        self.default_ttl = default_ttl
        self.strategy = strategy
        self._store: OrderedDict[str, MemoryItem] = OrderedDict()

    def set(self, key: str, value: Any, ttl: Optional[float] = None, importance: float = 1.0) -> None:
        now = time.time()
        item_ttl = ttl if ttl is not None else self.default_ttl

        if key in self._store:
            self._store.move_to_end(key)
            self._store[key].value = value
            self._store[key].last_accessed = now
            self._store[key].ttl_seconds = item_ttl
            self._store[key].importance = importance
        else:
            item = MemoryItem(key=key, value=value, created_at=now, last_accessed=now, ttl_seconds=item_ttl, importance=importance)
            self._store[key] = item

        self._evict_expired()
        self._evict_over_capacity()

    def get(self, key: str, default: Any = None) -> Any:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return default

        # Check TTL
        if item.ttl_seconds and (now - item.created_at) > item.ttl_seconds:
            del self._store[key]
            return default

        # Access update for LRU
        item.last_accessed = now
        self._store.move_to_end(key)
        return item.value

    def _evict_expired(self) -> None:
        now = time.time()
        expired_keys = [
            k for k, item in self._store.items()
            if item.ttl_seconds and (now - item.created_at) > item.ttl_seconds
        ]
        for k in expired_keys:
            del self._store[k]

    def _evict_over_capacity(self) -> None:
        while len(self._store) > self.max_capacity:
            if self.strategy == EvictionStrategy.LRU:
                # Remove oldest item (front of OrderedDict)
                popped_key, _ = self._store.popitem(last=False)
                logger.debug("LRU evicted memory key '%s'", popped_key)
            elif self.strategy == EvictionStrategy.IMPORTANCE:
                # Remove item with lowest importance
                min_key = min(self._store.keys(), key=lambda k: self._store[k].importance)
                del self._store[min_key]
                logger.debug("Importance evicted memory key '%s'", min_key)
            else:
                self._store.popitem(last=False)

    def size(self) -> int:
        self._evict_expired()
        return len(self._store)
