"""
ASEP — Top-Level Reflection Orchestrator
"""

import logging
from typing import TYPE_CHECKING

from src.evaluation.metrics import SessionMetrics
from src.evaluation.scoring import AllScores
from src.evaluation.trajectory import Trajectory
from src.reflection.generator import ReflectionGenerator
from src.reflection.memory_writer import ProceduralMemoryWriter
from src.reflection.models import ReflectionReport
from src.reflection.policies import ReflectionPolicy, ReflectionTrigger

if TYPE_CHECKING:
    from src.memory.memory_manager import MemoryManager
    from src.planner.provider import LLMProvider

logger = logging.getLogger(__name__)


class Reflector:
    """Orchestrates post-session reflection, lesson extraction, and memory updates."""

    def __init__(
        self,
        llm_provider: "LLMProvider",
        memory_manager: "MemoryManager",
    ) -> None:
        self._generator = ReflectionGenerator(llm_provider)
        self._memory_writer = ProceduralMemoryWriter(memory_manager)

    def _should_run(self, policy: ReflectionPolicy, passed: bool) -> bool:
        if policy.trigger == ReflectionTrigger.ALWAYS:
            return True
        if policy.trigger == ReflectionTrigger.NEVER:
            return False
        if policy.trigger == ReflectionTrigger.ON_SUCCESS and passed:
            return True
        if policy.trigger == ReflectionTrigger.ON_FAILURE and not passed:
            return True
        return False

    async def reflect(
        self,
        session_id: str,
        run_id: str,
        trajectory: Trajectory,
        metrics: SessionMetrics,
        scores: AllScores,
        policy: ReflectionPolicy | None = None,
    ) -> ReflectionReport | None:
        """Run the full reflection pipeline for a completed session."""
        policy = policy or ReflectionPolicy()
        passed = scores.passed

        if not self._should_run(policy, passed):
            logger.info(f"[{session_id}] Reflection skipped per policy (trigger={policy.trigger.value}, passed={passed})")
            return None

        logger.info(f"[{session_id}] Starting reflection (passed={passed})")

        # 1. Generate Reflection Report
        report = await self._generator.generate_reflection(
            session_id=session_id,
            run_id=run_id,
            passed=passed,
            trajectory=trajectory,
            metrics=metrics,
            scores=scores,
        )

        # 2. Update Procedural Memory
        await self._memory_writer.commit_lessons(report, policy)

        return report
