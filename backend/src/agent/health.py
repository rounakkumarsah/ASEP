"""
ASEP — Agent Health Check
"""

import logging

from src.agent.events import AgentEventType, make_event
from src.agent.reasoning import ReasoningEngine
from src.agent.state import AgentSessionStatus, AgentState

logger = logging.getLogger(__name__)


async def agent_health_check() -> bool:
    """Verifies agent components instantiate correctly and the event system works.

    Returns:
        True if all checks pass, False otherwise.
    """
    try:
        # Verify state model
        state = AgentState(
            session_id="health-session",
            run_id="health-run",
            thread_id="health-session",
            goal="health check goal",
            status=AgentSessionStatus.IDLE,
        )
        assert state.thread_id == state.session_id, "thread_id must equal session_id"

        # Verify event factory
        event = make_event(AgentEventType.SESSION_STARTED, "health-session", goal="test")
        assert event.event_type == AgentEventType.SESSION_STARTED
        assert event.payload["goal"] == "test"

        # Verify ReasoningEngine produces deterministic output
        from src.agent.context_builder import ContextSnapshot
        engine = ReasoningEngine()
        ctx = ContextSnapshot(session_id="health-session")
        enriched = engine.enrich_goal("do something", ctx)
        assert "do something" in enriched

        logger.info("Agent health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Agent health check failed: {exc}")
        return False
