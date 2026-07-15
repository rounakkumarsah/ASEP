"""
ASEP — Procedural Memory Writer
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.memory.memory_manager import MemoryManager
    from src.reflection.models import ReflectionReport
    from src.reflection.policies import ReflectionPolicy

logger = logging.getLogger(__name__)


class ProceduralMemoryWriter:
    """Writes high-confidence reflection lessons into Procedural Memory.
    
    Never overwrites existing procedures — instead, versions them to maintain an audit trail.
    """

    def __init__(self, memory_manager: "MemoryManager") -> None:
        self._memory = memory_manager

    async def commit_lessons(
        self,
        report: "ReflectionReport",
        policy: "ReflectionPolicy"
    ) -> int:
        """Filter lessons by confidence threshold and write them to procedural memory."""
        if not policy.update_procedural_memory:
            logger.info(f"[{report.session_id}] Procedural memory updates disabled by policy.")
            return 0

        committed = 0
        for item in report.items:
            if item.confidence >= policy.min_confidence_threshold:
                # Format as a strict procedural rule
                name = f"Lesson: {item.category.value.title()} - {item.root_cause[:30]}..."
                description = (
                    f"Context: {item.evidence}\n"
                    f"Failure/Issue: {item.failure_description}\n"
                    f"Rule: {item.recommendation}"
                )
                
                try:
                    # add_procedure generates a new version naturally, preserving history
                    await self._memory.procedural.add_procedure(
                        name=name,
                        description=description,
                        steps=[item.recommendation],
                        metadata={
                            "session_id": report.session_id,
                            "category": item.category.value,
                            "confidence": item.confidence,
                            "auto_generated": True,
                        }
                    )
                    committed += 1
                except Exception as exc:
                    logger.warning(f"[{report.session_id}] Failed to commit lesson to procedural memory: {exc}")

        logger.info(f"[{report.session_id}] Committed {committed} high-confidence lessons to procedural memory.")
        return committed
