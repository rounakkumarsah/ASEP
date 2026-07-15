"""
ASEP — Supervisor Agent
"""

import asyncio
import logging
import uuid
from typing import AsyncGenerator

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext
from src.multi_agent.handoff import HandoffManager
from src.multi_agent.messaging import MessageBus
from src.multi_agent.registry import AgentRegistry
from src.multi_agent.router import MessageRouter

logger = logging.getLogger(__name__)


class Supervisor:
    """Master orchestrator for the Multi-Agent Platform."""

    def __init__(self, bus: MessageBus, registry: AgentRegistry) -> None:
        self.role = AgentRole.SUPERVISOR
        self._bus = bus
        self._registry = registry
        self._task: asyncio.Task | None = None
        # Track ongoing sessions by session_id
        self._sessions: dict[str, asyncio.Queue] = {}

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Listen for messages returning to the supervisor."""
        async for msg in self._bus.subscribe(self.role):
            if msg.message_type == MessageType.HANDOFF:
                await self._handle_handoff(msg)

    async def _handle_handoff(self, msg: Message) -> None:
        """Process handoffs and route them to the next agent in the pipeline."""
        if msg.payload.get("status") == "failed":
            logger.error(f"[{msg.session_id}] Pipeline failed at {msg.sender_role.value}: {msg.payload.get('error')}")
            await self._complete_session(msg.session_id, {"status": "failed", "error": msg.payload.get("error")})
            return

        next_role = MessageRouter.get_next_role(msg.sender_role)
        
        if next_role and self._registry.get(next_role):
            logger.info(f"[{msg.session_id}] SUPERVISOR routing {msg.sender_role.value} -> {next_role.value}")
            ctx = CoordinationContext(
                session_id=msg.session_id,
                run_id=msg.run_id,
                thread_id=msg.thread_id,
                trace_id=msg.trace_id,
                goal=msg.payload.get("goal", "")
            )
            handoff = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=next_role,
                payload=msg.payload  # Forward state down the pipeline
            )
            await self._bus.publish(handoff)
        else:
            logger.info(f"[{msg.session_id}] SUPERVISOR pipeline complete.")
            await self._complete_session(msg.session_id, msg.payload)

    async def _complete_session(self, session_id: str, final_payload: dict) -> None:
        """Signal the yielding generator that the session is done."""
        if session_id in self._sessions:
            await self._sessions[session_id].put(final_payload)

    async def run_session(self, goal: str) -> AsyncGenerator[dict, None]:
        """Start a new multi-agent session and yield progress/final results."""
        session_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        
        ctx = CoordinationContext(
            session_id=session_id,
            run_id=run_id,
            thread_id=session_id,
            trace_id=str(uuid.uuid4()),
            goal=goal
        )

        logger.info(f"[{session_id}] SUPERVISOR starting new session.")
        
        # Create completion queue
        self._sessions[session_id] = asyncio.Queue()

        # Route to PLANNER
        handoff = HandoffManager.create_handoff(
            context=ctx,
            from_role=self.role,
            to_role=AgentRole.PLANNER,
            payload={"goal": goal}
        )
        await self._bus.publish(handoff)

        # Wait for the pipeline to finish
        final_result = await self._sessions[session_id].get()
        
        # Cleanup
        del self._sessions[session_id]
        
        yield final_result
