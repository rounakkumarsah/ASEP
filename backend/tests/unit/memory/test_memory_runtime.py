"""
ASEP — Unit Tests for Memory Runtime
"""

import time
from datetime import UTC

import pytest

from src.memory.runtime import ConversationMemory, EvictionStrategy, MemoryEvictionPolicy


def test_conversation_memory():
    conv = ConversationMemory(session_id="s1", max_messages=3)
    conv.add_message("system", "System prompt")
    conv.add_message("user", "Hello 1")
    conv.add_message("assistant", "Hi 1")
    conv.add_message("user", "Hello 2")

    messages = conv.get_messages()
    assert len(messages) == 3
    assert messages[0].role == "system"
    assert messages[-1].content == "Hello 2"


def test_memory_eviction_lru():
    policy = MemoryEvictionPolicy(max_capacity=2, strategy=EvictionStrategy.LRU)
    policy.set("k1", "v1")
    policy.set("k2", "v2")

    # Access k1 to make k2 least recently used
    assert policy.get("k1") == "v1"

    # Add k3, should evict k2
    policy.set("k3", "v3")

    assert policy.get("k1") == "v1"
    assert policy.get("k2") is None
    assert policy.get("k3") == "v3"


def test_memory_eviction_ttl():
    policy = MemoryEvictionPolicy(max_capacity=10, default_ttl=0.05)
    policy.set("k1", "v1")

    assert policy.get("k1") == "v1"
    time.sleep(0.06)
    assert policy.get("k1") is None


@pytest.mark.asyncio
async def test_memory_retrieval_scoring():
    from unittest.mock import AsyncMock, MagicMock

    from src.memory.retrieval import MemoryRetrieval

    # Mock memory dependencies
    working = MagicMock()
    working.get_messages = AsyncMock(return_value=[{"role": "user", "content": "hello"}])

    # Mock episodic entries
    from datetime import datetime
    from decimal import Decimal
    episode_entry = MagicMock()
    episode_entry.id = "e-123"
    episode_entry.content = "Connection Refused database error trace"
    episode_entry.importance_score = Decimal("0.80")
    episode_entry.created_at = datetime.now(UTC)

    episodic = MagicMock()
    episodic.get_episodes = AsyncMock(return_value=[episode_entry])

    # Mock semantic facts query
    semantic = MagicMock()
    semantic.query_facts = AsyncMock(return_value=[
        {"id": "s-456", "score": 0.85, "text": "database connectivity guidelines", "payload": {"importance": 0.90}}
    ])

    procedural = MagicMock()

    retrieval = MemoryRetrieval(working, episodic, semantic, procedural)
    res = await retrieval.retrieve_context("database error", "session-1", limit=5)

    assert "working" in res
    assert "episodic" in res
    assert "semantic" in res
    assert "ranked_fusion" in res

    # Check that scored matches are sorted descending by score
    scores = [m["score"] for m in res["ranked_fusion"]]
    assert scores == sorted(scores, reverse=True)

