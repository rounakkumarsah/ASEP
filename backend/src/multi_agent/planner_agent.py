"""
ASEP — Planner Agent
"""

import asyncio
import logging

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext
from src.multi_agent.handoff import HandoffManager
from src.multi_agent.messaging import MessageBus
from src.planner.planner import Planner

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Wraps the Phase 1.5 Planner Engine into a messaging-driven autonomous agent."""

    def __init__(self, bus: MessageBus, planner: Planner) -> None:
        self.role = AgentRole.PLANNER
        self._bus = bus
        self._planner = planner
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        async for msg in self._bus.subscribe(self.role):
            if msg.message_type == MessageType.HANDOFF:
                await self._handle_handoff(msg)

    async def _handle_handoff(self, msg: Message) -> None:
        goal = msg.payload.get("goal")
        if not goal:
            logger.error(f"[{msg.session_id}] PLANNER received handoff without a goal.")
            return

        logger.info(f"[{msg.session_id}] PLANNER started planning for goal: {goal}")
        
        try:
            # Delegate to existing engine
            plan = await self._planner.plan(goal)
            
            # Context for handoff
            ctx = CoordinationContext(
                session_id=msg.session_id,
                run_id=msg.run_id,
                thread_id=msg.thread_id,
                trace_id=msg.trace_id,
                goal=goal
            )
            
            # Handoff to EXECUTOR
            handoff_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.EXECUTOR,
                payload={"plan": plan.model_dump(mode="json")}
            )
            await self._bus.publish(handoff_msg)
            
        except Exception as exc:
            logger.error(f"[{msg.session_id}] PLANNER failed: {exc}")
            # Handoff back to SUPERVISOR on error
            ctx = CoordinationContext(
                session_id=msg.session_id,
                run_id=msg.run_id,
                thread_id=msg.thread_id,
                trace_id=msg.trace_id,
                goal=goal
            )
            error_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.SUPERVISOR,
                payload={"error": str(exc), "status": "failed"}
            )
            await self._bus.publish(error_msg)
