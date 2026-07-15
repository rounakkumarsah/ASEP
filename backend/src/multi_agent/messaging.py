"""
ASEP — Messaging Bus
"""

import asyncio
import logging
from typing import AsyncGenerator

from src.multi_agent.contracts import AgentRole, Message

logger = logging.getLogger(__name__)


class MessageBus:
    """In-memory async event bus for inter-agent messaging."""

    def __init__(self) -> None:
        # One queue per role for targeted messaging
        self._queues: dict[AgentRole, asyncio.Queue[Message]] = {
            role: asyncio.Queue() for role in AgentRole
        }
        # A global queue for broadcast EVENT messages
        self._event_queue: asyncio.Queue[Message] = asyncio.Queue()

    async def publish(self, message: Message) -> None:
        """Publish a message to its intended recipient or broadcast if it is an EVENT."""
        logger.debug(f"[{message.session_id}] Bus publishing {message.message_type.value} from {message.sender_role.value} to {message.receiver_role.value}")
        
        if message.message_type == "event":
            await self._event_queue.put(message)
        else:
            queue = self._queues.get(message.receiver_role)
            if queue:
                await queue.put(message)
            else:
                logger.warning(f"No queue found for role: {message.receiver_role}")

    async def subscribe(self, role: AgentRole) -> AsyncGenerator[Message, None]:
        """Yield messages intended for the specified role."""
        queue = self._queues[role]
        while True:
            try:
                msg = await queue.get()
                yield msg
                queue.task_done()
            except asyncio.CancelledError:
                logger.debug(f"Subscription cancelled for role: {role.value}")
                break

    async def subscribe_events(self) -> AsyncGenerator[Message, None]:
        """Yield global events for monitoring (e.g. by the Supervisor)."""
        while True:
            try:
                msg = await self._event_queue.get()
                yield msg
                self._event_queue.task_done()
            except asyncio.CancelledError:
                break
