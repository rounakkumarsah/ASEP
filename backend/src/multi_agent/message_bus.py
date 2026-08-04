"""
ASEP — Multi-Agent Async Message Bus
====================================
Pub/Sub event bus for inter-agent communication, broadcasting, and task delegation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    sender_role: str
    recipient_role: Optional[str]
    topic: str
    payload: Dict[str, Any]


class AgentMessageBus:
    """Async message bus facilitating agent messaging and broadcasting."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[AgentMessage], Any]]] = {}
        self._history: List[AgentMessage] = []

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], Any]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    async def publish(self, message: AgentMessage) -> None:
        self._history.append(message)
        logger.info(
            "MessageBus published on '%s' from %s to %s",
            message.topic,
            message.sender_role,
            message.recipient_role or "ALL",
        )

        handlers = self._subscribers.get(message.topic, [])
        for handler in handlers:
            try:
                res = handler(message)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.error("Error executing subscriber for topic '%s': %s", message.topic, exc)

    def get_history(self, topic: Optional[str] = None) -> List[AgentMessage]:
        if topic:
            return [m for m in self._history if m.topic == topic]
        return list(self._history)
