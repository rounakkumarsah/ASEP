"""
ASEP — Executor Agent
"""

import asyncio
import logging

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext
from src.multi_agent.handoff import HandoffManager
from src.multi_agent.messaging import MessageBus
from src.executor.executor import Executor
from src.planner.plan import DecomposedPlan

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """Wraps the Phase 1.6 Executor Engine into a messaging-driven autonomous agent."""

    def __init__(self, bus: MessageBus, executor: Executor) -> None:
        self.role = AgentRole.EXECUTOR
        self._bus = bus
        self._executor = executor
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        async for msg in self._bus.subscribe(self.role):
            if msg.message_type == MessageType.HANDOFF:
                await self._handle_handoff(msg)

    async def _handle_handoff(self, msg: Message) -> None:
        plan_data = msg.payload.get("plan")
        if not plan_data:
            logger.error(f"[{msg.session_id}] EXECUTOR received handoff without a plan.")
            return

        plan = DecomposedPlan.model_validate(plan_data)
        logger.info(f"[{msg.session_id}] EXECUTOR started execution.")
        
        ctx = CoordinationContext(
            session_id=msg.session_id,
            run_id=msg.run_id,
            thread_id=msg.thread_id,
            trace_id=msg.trace_id,
            goal=msg.payload.get("goal", "")
        )

        try:
            # Delegate to existing engine
            result = await self._executor.execute(plan)
            
            # Note: Executor doesn't need to handoff directly to EVALUATOR/REFLECTOR.
            # It hands off to SUPERVISOR, who decides the next routing step based on policies.
            handoff_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.SUPERVISOR,
                payload={"execution_result": result.model_dump(mode="json"), "status": "completed"}
            )
            await self._bus.publish(handoff_msg)
            
        except Exception as exc:
            logger.error(f"[{msg.session_id}] EXECUTOR failed: {exc}")
            # Handoff back to SUPERVISOR on error
            error_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.SUPERVISOR,
                payload={"error": str(exc), "status": "failed"}
            )
            await self._bus.publish(error_msg)
