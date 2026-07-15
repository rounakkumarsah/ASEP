"""
ASEP — Governance Health Check
"""

import logging
from src.governance.decision import DecisionResult
from src.governance.intent import ActionIntent
from src.governance.runtime_authorization import RuntimeAuthorizer

logger = logging.getLogger(__name__)


async def governance_health_check() -> bool:
    """Verifies that intents are evaluated correctly by guardrails and policies."""
    try:
        authorizer = RuntimeAuthorizer()
        
        # Test Guardrail Denial (System Prompt modification)
        blocked_intent = ActionIntent(
            session_id="hc", run_id="hc", thread_id="hc", trace_id="hc",
            actor_role="executor", action_type="write", target="system_prompt.txt",
            justification="test"
        )
        decision1 = await authorizer.authorize(blocked_intent)
        assert decision1.result == DecisionResult.DENY
        assert "SystemPromptGuardrail" in decision1.reason

        # Test Policy Approval (Terminal execution)
        approval_intent = ActionIntent(
            session_id="hc", run_id="hc", thread_id="hc", trace_id="hc",
            actor_role="executor", action_type="execute_terminal", target="ls",
            justification="test"
        )
        decision2 = await authorizer.authorize(approval_intent)
        # Assuming the Mock human approved it, it should be ALLOW
        assert decision2.result == DecisionResult.ALLOW
        
        logger.info("Governance health check passed")
        return True

    except Exception as exc:
        logger.warning(f"Governance health check failed: {exc}")
        return False
