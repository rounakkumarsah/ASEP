"""
ASEP — Runtime Authorization
"""

import logging

from src.governance.approval import ApprovalManager
from src.governance.audit import AuditTrail
from src.governance.decision import ApprovalState, DecisionResult, GovernanceDecision
from src.governance.guardrails import Guardrail, SystemPromptGuardrail, WorkspaceGuardrail
from src.governance.intent import ActionIntent
from src.governance.policy_engine import PolicyEvaluator

logger = logging.getLogger(__name__)


class RuntimeAuthorizer:
    """Orchestrates the governance evaluation flow."""

    def __init__(self) -> None:
        self.guardrails: list[Guardrail] = [SystemPromptGuardrail(), WorkspaceGuardrail()]
        self.policy_evaluator = PolicyEvaluator()
        self.approval_manager = ApprovalManager()
        self.audit_trail = AuditTrail()

    async def authorize(self, intent: ActionIntent) -> GovernanceDecision:
        """
        Evaluate intent through Guardrails -> Policy -> Approval -> Final Decision.
        """
        logger.debug(f"[{intent.session_id}] Evaluating intent {intent.intent_id} for {intent.action_type}")
        
        decision = GovernanceDecision(
            intent_id=intent.intent_id,
            session_id=intent.session_id,
            run_id=intent.run_id,
            thread_id=intent.thread_id,
            trace_id=intent.trace_id,
            result=DecisionResult.ALLOW
        )

        # 1. Static Guardrails
        for guardrail in self.guardrails:
            guard_result = guardrail.evaluate(intent)
            if guard_result == DecisionResult.DENY:
                decision.result = DecisionResult.DENY
                decision.reason = f"Blocked by {guardrail.__class__.__name__}"
                self.audit_trail.record(intent, decision)
                return decision

        # 2. Dynamic Policy Engine
        policy_result = self.policy_evaluator.evaluate(intent)
        decision.result = policy_result

        # 3. Human Approval Gates
        if decision.result == DecisionResult.REQUIRE_APPROVAL:
            decision.approval_state = ApprovalState.PENDING
            approval_result = await self.approval_manager.request_approval(intent)
            decision.result = approval_result
            decision.approval_state = ApprovalState.APPROVED if approval_result == DecisionResult.ALLOW else ApprovalState.DENIED

        # Record Audit Trail
        self.audit_trail.record(intent, decision)
        return decision
