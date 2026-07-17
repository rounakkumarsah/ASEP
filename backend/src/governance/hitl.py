"""
ASEP — Human-in-the-Loop (HITL) Orchestration Engine
"""

import os
import uuid
import time
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ApprovalAction(str, Enum):
    APPROVE = "Approve"
    REJECT = "Reject"
    MODIFY = "Modify"
    RETRY = "Retry"
    ESCALATE = "Escalate"
    CANCEL = "Cancel"
    EXPIRE = "Expire"


class ReviewerRole(str, Enum):
    OPERATOR = "Operator"
    TEAM_LEAD = "Team Lead"
    ADMINISTRATOR = "Administrator"
    SECURITY_REVIEWER = "Security Reviewer"
    COMPLIANCE_REVIEWER = "Compliance Reviewer"


class ApprovalTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    default_risk_level: RiskLevel
    required_reviewer_role: ReviewerRole


class ReviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"resume_tok_{uuid.uuid4().hex[:12]}")
    request_id: str
    execution_id: str
    correlation_id: str
    requesting_agent: str
    requesting_tool: str
    requested_permissions: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    justification: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewer: Optional[str] = None
    reviewer_role: Optional[ReviewerRole] = None
    decision: Optional[ApprovalAction] = None
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    modified_arguments: Optional[Dict[str, Any]] = None
    expired_at: Optional[datetime] = None
    
    # SLA metric parameters
    created_at: float = Field(default_factory=time.time)
    decided_at: Optional[float] = None
    latency_seconds: Optional[float] = None


class ApprovalSLA(BaseModel):
    approval_latency: float = 0.0
    average_review_time: float = 0.0
    escalation_rate: float = 0.0
    timeout_rate: float = 0.0


# Notification Interface Scaffolds
class NotificationInterface:
    """Interface routes to dashboard triggers and outbound channels."""

    @staticmethod
    def notify(session: ReviewSession) -> None:
        logger.info(f"[Notification] Dispatching alert to Slack/Email/Dashboard queue for session={session.session_id}")


class HITLEngine:
    """Enterprise Human-in-the-Loop decision and queue registry engine."""

    def __init__(self) -> None:
        self.queue: Dict[str, ReviewSession] = {}
        self.sla_stats = ApprovalSLA()
        self.templates: Dict[str, ApprovalTemplate] = {
            "critical_shell": ApprovalTemplate(
                template_id="critical_shell",
                name="Critical Shell Command Review",
                description="Manual reviews required for running CLI terminal processes.",
                default_risk_level=RiskLevel.CRITICAL,
                required_reviewer_role=ReviewerRole.SECURITY_REVIEWER
            )
        }
        self.risk_policies: Dict[str, RiskLevel] = {
            "filesystem.delete": RiskLevel.HIGH,
            "filesystem.write": RiskLevel.MEDIUM,
            "git.commit": RiskLevel.MEDIUM,
            "terminal": RiskLevel.CRITICAL,
            "docker": RiskLevel.CRITICAL
        }

    def evaluate_risk(self, tool_name: str, arguments: Dict[str, Any]) -> RiskLevel:
        """Determines the risk classification mapped to tool parameters."""
        action = arguments.get("action", "")
        key = f"{tool_name}.{action}" if action else tool_name
        
        # Check specific operation policy
        if key in self.risk_policies:
            return self.risk_policies[key]
        if tool_name in self.risk_policies:
            return self.risk_policies[tool_name]
            
        return RiskLevel.LOW

    def create_session(
        self,
        request_id: str,
        execution_id: str,
        correlation_id: str,
        requesting_agent: str,
        requesting_tool: str,
        requested_permissions: List[str],
        arguments: Dict[str, Any],
        justification: str,
        ttl_seconds: int = 300
    ) -> ReviewSession:
        """Create and queue a human review session for critical tasks."""
        risk_lvl = self.evaluate_risk(requesting_tool, arguments)
        
        session = ReviewSession(
            request_id=request_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
            requesting_agent=requesting_agent,
            requesting_tool=requesting_tool,
            requested_permissions=requested_permissions,
            risk_level=risk_lvl,
            justification=justification,
            modified_arguments=arguments,
            expired_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        )
        
        session.audit_trail.append({
            "action": "ApprovalRequested",
            "timestamp": time.time(),
            "details": f"Review requested for action '{requesting_tool}' classified as {risk_lvl}."
        })
        
        self.queue[session.session_id] = session
        NotificationInterface.notify(session)
        logger.info(f"ApprovalRequested: Created HITL review session {session.session_id}")
        return session

    def submit_decision(
        self,
        session_id: str,
        action: ApprovalAction,
        reviewer: str,
        role: ReviewerRole,
        modified_args: Optional[Dict[str, Any]] = None,
        notes: str = ""
    ) -> ReviewSession:
        """Resolve a queued review session with approval, rejection, or modifications."""
        session = self.queue.get(session_id)
        if not session:
            raise KeyError(f"Review session {session_id} not found.")
            
        if session.decision:
            raise ValueError(f"Review session {session_id} already resolved.")

        # Check Expiration before processing
        if session.expired_at and datetime.now(timezone.utc) > session.expired_at:
            session.decision = ApprovalAction.EXPIRE
            session.audit_trail.append({
                "action": "ApprovalExpired",
                "timestamp": time.time(),
                "details": "Session expired before human decision."
            })
            self._recalculate_sla()
            logger.warning(f"ApprovalExpired: Session {session_id} expired.")
            return session

        session.decision = action
        session.reviewer = reviewer
        session.reviewer_role = role
        session.decided_at = time.time()
        session.latency_seconds = session.decided_at - session.created_at
        
        if modified_args:
            session.modified_arguments = modified_args
            
        session.audit_trail.append({
            "action": f"Approval{action.value}",
            "timestamp": time.time(),
            "details": f"Decision submitted by {reviewer} ({role.value}). Notes: {notes}"
        })
        
        self._recalculate_sla()
        logger.info(f"Approval{action.value}: Resolved session {session_id} successfully.")
        return session

    def _recalculate_sla(self) -> None:
        """Recalculates average review parameters for active logs."""
        resolved = [s for s in self.queue.values() if s.decision is not None]
        if not resolved:
            return
            
        latencies = [s.latency_seconds for s in resolved if s.latency_seconds is not None]
        self.sla_stats.average_review_time = sum(latencies) / len(latencies) if latencies else 0.0
        self.sla_stats.approval_latency = self.sla_stats.average_review_time
        
        timeouts = len([s for s in resolved if s.decision == ApprovalAction.EXPIRE])
        self.sla_stats.timeout_rate = timeouts / len(resolved)
        
        escalated = len([s for s in resolved if s.decision == ApprovalAction.ESCALATE])
        self.sla_stats.escalation_rate = escalated / len(resolved)


_global_hitl_engine: Optional[HITLEngine] = None

def get_hitl_engine() -> HITLEngine:
    global _global_hitl_engine
    if _global_hitl_engine is None:
        _global_hitl_engine = HITLEngine()
    return _global_hitl_engine
