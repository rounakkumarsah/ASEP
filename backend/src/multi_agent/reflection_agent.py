"""
ASEP — Reflection Agent
"""

import asyncio
import logging

from src.multi_agent.contracts import AgentRole, Message, MessageType
from src.multi_agent.coordination import CoordinationContext
from src.multi_agent.handoff import HandoffManager
from src.multi_agent.messaging import MessageBus
from src.reflection.reflector import Reflector
from src.evaluation.evaluator import EvaluationResult

logger = logging.getLogger(__name__)


class ReflectionAgent:
    """Wraps the Phase 2.0 Reflector Engine into a messaging-driven autonomous agent."""

    def __init__(self, bus: MessageBus, reflector: Reflector) -> None:
        self.role = AgentRole.REFLECTOR
        self._bus = bus
        self._reflector = reflector
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        async for msg in self._bus.subscribe(self.role):
            if msg.message_type == MessageType.HANDOFF:
                await self._handle_handoff(msg)

    async def _handle_handoff(self, msg: Message) -> None:
        logger.info(f"[{msg.session_id}] REFLECTOR starting reflection.")
        ctx = CoordinationContext(
            session_id=msg.session_id,
            run_id=msg.run_id,
            thread_id=msg.thread_id,
            trace_id=msg.trace_id,
            goal=msg.payload.get("goal", "")
        )

        try:
            eval_data = msg.payload.get("evaluation_result")
            if not eval_data:
                raise ValueError("No evaluation_result provided for reflection.")

            result = EvaluationResult.model_validate(eval_data)
            
            report = await self._reflector.reflect(
                session_id=msg.session_id,
                run_id=msg.run_id,
                trajectory=result.trajectory,
                metrics=result.metrics,
                scores=result.scores,
                policy=msg.payload.get("policy") # Can be passed in payload
            )
            
            payload = {"status": "completed"}
            if report:
                payload["reflection_report"] = report.model_dump(mode="json")

            handoff_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.SUPERVISOR,
                payload=payload
            )
            await self._bus.publish(handoff_msg)
            
        except Exception as exc:
            logger.error(f"[{msg.session_id}] REFLECTOR failed: {exc}")
            error_msg = HandoffManager.create_handoff(
                context=ctx,
                from_role=self.role,
                to_role=AgentRole.SUPERVISOR,
                payload={"error": str(exc), "status": "failed"}
            )
            await self._bus.publish(error_msg)
