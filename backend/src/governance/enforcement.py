"""
ASEP — Governance Enforcement
"""

import logging
from typing import Any, Callable

from src.governance.decision import DecisionResult
from src.governance.intent import ActionIntent
from src.governance.runtime_authorization import RuntimeAuthorizer

logger = logging.getLogger(__name__)


class AuthorizationError(Exception):
    """Raised when governance denies an action."""
    pass


class Enforcer:
    """Blocks execution if the intent is not authorized."""

    def __init__(self, authorizer: RuntimeAuthorizer) -> None:
        self.authorizer = authorizer

    async def enforce(self, intent: ActionIntent, action: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Evaluate intent and execute action if ALLOWED, else raise AuthorizationError."""
        decision = await self.authorizer.authorize(intent)
        
        if decision.result in (DecisionResult.ALLOW, DecisionResult.READ_ONLY, DecisionResult.SANDBOX_ONLY):
            # In a fuller implementation, READ_ONLY / SANDBOX_ONLY might wrap the action in specific contexts
            return await action(*args, **kwargs)
        else:
            logger.warning(f"[{intent.session_id}] Action {intent.action_type} DENIED: {decision.reason}")
            raise AuthorizationError(f"Action denied by governance: {decision.reason}")
