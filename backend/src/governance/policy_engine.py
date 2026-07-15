"""
ASEP — Dynamic Policy Engine
"""

from src.governance.intent import ActionIntent
from src.governance.decision import DecisionResult


class PolicyEvaluator:
    """Evaluates an intent against dynamic, context-aware policies."""
    
    def evaluate(self, intent: ActionIntent) -> DecisionResult:
        """
        Evaluate RBAC and context.
        Returns ALLOW, DENY, REQUIRE_APPROVAL, SANDBOX_ONLY, or READ_ONLY.
        """
        # Hardcoded example policy rules for Phase 2.2
        if intent.actor_role == "supervisor":
            return DecisionResult.ALLOW
            
        if intent.action_type == "execute_terminal":
            return DecisionResult.REQUIRE_APPROVAL
            
        if intent.action_type == "deploy":
            return DecisionResult.REQUIRE_APPROVAL
            
        # Default behavior for non-sensitive actions
        return DecisionResult.ALLOW
