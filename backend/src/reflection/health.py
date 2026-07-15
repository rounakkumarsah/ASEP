"""
ASEP — Reflection Health Check
"""

import logging

from src.reflection.models import ReflectionReport, ReflectionItem, LessonCategory, RootCauseCategory, FailureAnalysis
from src.reflection.policies import ReflectionPolicy, ReflectionTrigger

logger = logging.getLogger(__name__)


async def reflection_health_check() -> bool:
    """Verifies reflection components instantiate and produce valid typed outputs."""
    try:
        # Verify policy models
        policy = ReflectionPolicy(trigger=ReflectionTrigger.ALWAYS, min_confidence_threshold=0.9)
        assert policy.trigger == ReflectionTrigger.ALWAYS

        # Verify Reflection models
        item = ReflectionItem(
            category=LessonCategory.PLANNING,
            failure_description="Failed to plan properly.",
            root_cause="Bad prompt.",
            evidence="Step 1 failed.",
            recommendation="Do not fail.",
            confidence=0.95,
        )
        assert item.confidence == 0.95

        analysis = FailureAnalysis(
            category=RootCauseCategory.TOOL_FAILURE,
            contributing_factors=["timeout", "network issue"],
        )

        report = ReflectionReport(
            session_id="hc-session",
            run_id="hc-run",
            passed=False,
            failure_analysis=analysis,
            items=[item],
        )
        assert report.passed is False
        assert len(report.items) == 1

        logger.info("Reflection health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Reflection health check failed: {exc}")
        return False
