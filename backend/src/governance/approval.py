"""
ASEP — Human Approval Management
"""

import asyncio
import logging

from src.governance.intent import ActionIntent
from src.governance.decision import ApprovalState, DecisionResult

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Manages asynchronous human-in-the-loop approval gates."""

    async def request_approval(self, intent: ActionIntent) -> DecisionResult:
        """
        Suspending execution pending human review.
        For Phase 2.2, we simulate an asynchronous approval flow.
        """
        logger.info(f"[{intent.session_id}] Approval requested for {intent.action_type} on {intent.target}")
        
        # Simulate an asynchronous delay for human review
        await asyncio.sleep(0.1)
        
        # Simulated approval logic
        # In a real system, this would wait on a Redis pub/sub channel or database flag updated by a UI
        if "destructive" in intent.justification.lower():
            logger.info(f"[{intent.session_id}] Human DENIED destructive action.")
            return DecisionResult.DENY
            
        logger.info(f"[{intent.session_id}] Human APPROVED action.")
        return DecisionResult.ALLOW
