"""
ASEP — Control Plane Approvals
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field

from src.governance.decision import ApprovalState, DecisionResult
from src.governance.intent import ActionIntent

logger = logging.getLogger(__name__)


class PendingApproval(BaseModel):
    intent: ActionIntent
    state: ApprovalState = ApprovalState.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    expires_at: datetime
    
    # We cannot store an asyncio.Event in Pydantic easily without arbitrary_types_allowed,
    # so we manage the event separately in the Queue


class ApprovalQueue:
    """Stateful manager exposing PENDING governance decisions for human review."""

    def __init__(self, default_timeout_minutes: int = 15) -> None:
        self._pending: dict[str, PendingApproval] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._decisions: dict[str, DecisionResult] = {}
        self.default_timeout_minutes = default_timeout_minutes

    async def enqueue_and_wait(self, intent: ActionIntent) -> DecisionResult:
        """Called by Governance ApprovalManager to wait for human review."""
        intent_id = intent.intent_id
        
        # Register the pending approval
        expires = datetime.now(tz=timezone.utc) + timedelta(minutes=self.default_timeout_minutes)
        self._pending[intent_id] = PendingApproval(intent=intent, expires_at=expires)
        event = asyncio.Event()
        self._events[intent_id] = event

        logger.info(f"[{intent.session_id}] Intent {intent_id} added to ApprovalQueue. Waiting...")
        
        # Wait for admin to resolve or timeout
        try:
            # We don't use asyncio.wait_for directly here to keep it simple,
            # but in a real system we'd handle expiration via a background task.
            # For this phase, we await the event indefinitely (or until timeout if we built a cleaner).
            await event.wait()
            decision = self._decisions.get(intent_id, DecisionResult.DENY)
            return decision
        finally:
            # Cleanup
            self._pending.pop(intent_id, None)
            self._events.pop(intent_id, None)
            self._decisions.pop(intent_id, None)

    def list_pending(self, session_id: str | None = None) -> list[PendingApproval]:
        now = datetime.now(tz=timezone.utc)
        results = []
        for p in self._pending.values():
            if session_id and p.intent.session_id != session_id:
                continue
            if now > p.expires_at:
                p.state = ApprovalState.EXPIRED
            results.append(p)
        return results

    def resolve(self, intent_id: str, decision: DecisionResult) -> bool:
        """Called by Admin (write API) to approve or deny."""
        if intent_id in self._pending and intent_id in self._events:
            self._decisions[intent_id] = decision
            self._pending[intent_id].state = ApprovalState.APPROVED if decision == DecisionResult.ALLOW else ApprovalState.DENIED
            self._events[intent_id].set()
            logger.info(f"Admin resolved intent {intent_id} with {decision.value}")
            return True
        return False
