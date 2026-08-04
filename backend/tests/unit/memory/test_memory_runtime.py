"""
ASEP — Unit Tests for Memory Runtime
"""

import time
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
