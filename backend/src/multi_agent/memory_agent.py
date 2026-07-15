"""
ASEP — Memory Agent
"""

import asyncio
import logging

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.messaging import MessageBus
from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Wraps the Memory Manager for asynchronous state operations via messaging."""

    def __init__(self, bus: MessageBus, memory: MemoryManager) -> None:
        self.role = AgentRole.MEMORY
        self._bus = bus
        self._memory = memory
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        async for msg in self._bus.subscribe(self.role):
            if msg.message_type == MessageType.REQUEST:
                await self._handle_request(msg)

    async def _handle_request(self, msg: Message) -> None:
        action = msg.payload.get("action")
        logger.debug(f"[{msg.session_id}] MEMORY received request: {action}")
        
        # Example minimal handling for memory requests
        try:
            if action == "save_episodic":
                await self._memory.episodic.save_event(
                    session_id=msg.session_id,
                    event_type=msg.payload.get("event_type", "unknown"),
                    data=msg.payload.get("data", {})
                )
            
            # Send response back to sender
            response = Message(
                session_id=msg.session_id,
                run_id=msg.run_id,
                thread_id=msg.thread_id,
                trace_id=msg.trace_id,
                sender_role=self.role,
                receiver_role=msg.sender_role,
                message_type=MessageType.RESPONSE,
                payload={"status": "success", "action": action}
            )
            await self._bus.publish(response)
            
        except Exception as exc:
            logger.error(f"[{msg.session_id}] MEMORY failed handling request: {exc}")
            response = Message(
                session_id=msg.session_id,
                run_id=msg.run_id,
                thread_id=msg.thread_id,
                trace_id=msg.trace_id,
                sender_role=self.role,
                receiver_role=msg.sender_role,
                message_type=MessageType.RESPONSE,
                payload={"status": "error", "error": str(exc), "action": action}
            )
            await self._bus.publish(response)
