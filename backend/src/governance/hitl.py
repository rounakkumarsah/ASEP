"""
ASEP — Human-in-the-Loop (HITL) Orchestration Engine
"""

from __future__ import annotations

import contextlib
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ApprovalAction(StrEnum):
    APPROVE = "Approve"
    REJECT = "Reject"
    MODIFY = "Modify"
    RETRY = "Retry"
    ESCALATE = "Escalate"
    CANCEL = "Cancel"
    EXPIRE = "Expire"


class ReviewerRole(StrEnum):
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
    requested_permissions: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    justification: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewer: str | None = None
    reviewer_role: ReviewerRole | None = None
    decision: ApprovalAction | None = None
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)
    modified_arguments: dict[str, Any] | None = None
    expired_at: datetime | None = None

    # SLA metric parameters
    created_at: float = Field(default_factory=time.time)
    decided_at: float | None = None
    latency_seconds: float | None = None


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
        logger.info(
            f"[Notification] Dispatching alert to Slack/Email/Dashboard queue for session={session.session_id}"
        )


class HITLEngine:
    """Enterprise Human-in-the-Loop decision and queue registry engine."""

    def __init__(self) -> None:
        self.uow_factory = None
        self.templates: dict[str, ApprovalTemplate] = {
            "critical_shell": ApprovalTemplate(
                template_id="critical_shell",
                name="Critical Shell Command Review",
                description="Manual reviews required for running CLI terminal processes.",
                default_risk_level=RiskLevel.CRITICAL,
                required_reviewer_role=ReviewerRole.SECURITY_REVIEWER,
            )
        }
        self.risk_policies: dict[str, RiskLevel] = {
            "filesystem.delete": RiskLevel.HIGH,
            "filesystem.write": RiskLevel.MEDIUM,
            "git.commit": RiskLevel.MEDIUM,
            "terminal": RiskLevel.CRITICAL,
            "docker": RiskLevel.CRITICAL,
        }

    def evaluate_risk(self, tool_name: str, arguments: dict[str, Any]) -> RiskLevel:
        """Determines the risk classification mapped to tool parameters."""
        action = arguments.get("action", "")
        key = f"{tool_name}.{action}" if action else tool_name

        # Check specific operation policy
        if key in self.risk_policies:
            return self.risk_policies[key]
        if tool_name in self.risk_policies:
            return self.risk_policies[tool_name]

        return RiskLevel.LOW

    async def create_session(
        self,
        request_id: str,
        execution_id: str,
        correlation_id: str,
        requesting_agent: str,
        requesting_tool: str,
        requested_permissions: list[str],
        arguments: dict[str, Any],
        justification: str,
        ttl_seconds: int = 300,
    ) -> ReviewSession:
        """Create and queue a human review session for critical tasks in the database."""
        risk_lvl = self.evaluate_risk(requesting_tool, arguments)
        session_id = f"resume_tok_{uuid.uuid4().hex[:12]}"

        import uuid as pyuuid

        from src.db.models.hitl_session import HITLSession, HITLStatus

        db_session = HITLSession(
            session_id=session_id,
            execution_id=pyuuid.UUID(execution_id),
            correlation_id=correlation_id,
            requesting_agent=requesting_agent,
            requesting_tool=requesting_tool,
            risk_level=risk_lvl.value,
            status=HITLStatus.PENDING,
            arguments_json=arguments,
            justification=justification,
            ttl_seconds=ttl_seconds,
        )

        uow_ctx = self.uow_factory() if self.uow_factory else None
        if uow_ctx is None:
            from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

            uow_ctx = SQLAlchemyUnitOfWork()

        async with uow_ctx as uow:
            await uow.hitl_sessions.create(db_session)
            await uow.commit()

        # Construct ReviewSession domain schema to return
        session = ReviewSession(
            session_id=session_id,
            request_id=request_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
            requesting_agent=requesting_agent,
            requesting_tool=requesting_tool,
            requested_permissions=requested_permissions,
            risk_level=risk_lvl,
            justification=justification,
            modified_arguments=arguments,
            expired_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        session.audit_trail.append(
            {
                "action": "ApprovalRequested",
                "timestamp": time.time(),
                "details": f"Review requested for action '{requesting_tool}' classified as {risk_lvl}.",
            }
        )

        NotificationInterface.notify(session)
        logger.info(f"ApprovalRequested: Created HITL review session {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> ReviewSession | None:
        """Fetch a review session by ID."""
        uow_ctx = self.uow_factory() if self.uow_factory else None
        if uow_ctx is None:
            from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

            uow_ctx = SQLAlchemyUnitOfWork()

        async with uow_ctx as uow:
            db_sess = await uow.hitl_sessions.get(session_id)
            if not db_sess:
                return None
            return self._to_domain(db_sess)

    async def get_all_sessions(self) -> list[ReviewSession]:
        """Fetch all review sessions."""
        uow_ctx = self.uow_factory() if self.uow_factory else None
        if uow_ctx is None:
            from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

            uow_ctx = SQLAlchemyUnitOfWork()

        async with uow_ctx as uow:
            db_sessions = await uow.hitl_sessions.list()
            return [self._to_domain(s) for s in db_sessions]

    def _to_domain(self, db_sess: Any) -> ReviewSession:
        # Parse fields with fallback
        try:
            risk = RiskLevel(db_sess.risk_level)
        except ValueError:
            risk = RiskLevel.LOW

        decision = None
        if db_sess.decision:
            try:
                decision_val = (
                    db_sess.decision.value
                    if hasattr(db_sess.decision, "value")
                    else db_sess.decision
                )
                decision = ApprovalAction(decision_val)
            except ValueError:
                pass

        role = None
        if db_sess.reviewer_role:
            with contextlib.suppress(ValueError):
                role = ReviewerRole(db_sess.reviewer_role)

        created_at_ts = db_sess.created_at.timestamp() if db_sess.created_at else time.time()
        decided_at_ts = db_sess.decided_at.timestamp() if db_sess.decided_at else None

        domain_sess = ReviewSession(
            session_id=db_sess.session_id,
            request_id=db_sess.correlation_id,
            execution_id=str(db_sess.execution_id),
            correlation_id=db_sess.correlation_id,
            requesting_agent=db_sess.requesting_agent,
            requesting_tool=db_sess.requesting_tool,
            requested_permissions=["approve"],
            risk_level=risk,
            justification=db_sess.justification,
            reviewer=db_sess.reviewer,
            reviewer_role=role,
            decision=decision,
            modified_arguments=db_sess.arguments_json,
            expired_at=(
                db_sess.created_at + timedelta(seconds=db_sess.ttl_seconds)
                if db_sess.created_at
                else None
            ),
            created_at=created_at_ts,
            decided_at=decided_at_ts,
            latency_seconds=db_sess.latency_seconds,
            audit_trail=[],
        )

        # Reconstruct audit trail — always include the creation event
        domain_sess.audit_trail.append(
            {
                "action": "ApprovalRequested",
                "timestamp": created_at_ts,
                "details": f"Review requested for action '{db_sess.requesting_tool}' classified as {risk}.",
            }
        )
        # Append the decision event if the session has been resolved
        if db_sess.decision:
            domain_sess.audit_trail.append(
                {
                    "action": f"Approval{domain_sess.decision.value}",
                    "timestamp": decided_at_ts or time.time(),
                    "details": f"Decision submitted by {db_sess.reviewer} ({role.value if role else ''}). Notes: {db_sess.notes or ''}",
                }
            )
        return domain_sess

    async def submit_decision(
        self,
        session_id: str,
        action: ApprovalAction,
        reviewer: str,
        role: ReviewerRole,
        modified_args: dict[str, Any] | None = None,
        notes: str = "",
    ) -> ReviewSession:
        """Resolve a queued review session with approval, rejection, or modifications in database."""
        from src.db.models.hitl_session import HITLAction, HITLStatus

        uow_ctx = self.uow_factory() if self.uow_factory else None
        if uow_ctx is None:
            from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

            uow_ctx = SQLAlchemyUnitOfWork()

        async with uow_ctx as uow:
            db_sess = await uow.hitl_sessions.get(session_id)
            if not db_sess:
                raise KeyError(f"Review session {session_id} not found.")

            if db_sess.decision:
                raise ValueError(f"Review session {session_id} already resolved.")

            now = datetime.now(UTC)
            db_sess.decided_at = now
            db_sess.reviewer = reviewer
            db_sess.reviewer_role = role.value
            db_sess.notes = notes

            # Check expiration
            expire_time = (
                db_sess.created_at + timedelta(seconds=db_sess.ttl_seconds)
                if db_sess.created_at
                else now
            )
            # Ensure compare timezone awareness
            if db_sess.created_at and db_sess.created_at.tzinfo is None:
                expire_time = expire_time.replace(tzinfo=UTC)

            if now > expire_time:
                db_sess.decision = HITLAction.EXPIRE
                db_sess.status = HITLStatus.EXPIRED
            else:
                db_sess.decision = HITLAction(action.value)
                if action == ApprovalAction.APPROVE:
                    db_sess.status = HITLStatus.APPROVED
                elif action == ApprovalAction.REJECT:
                    db_sess.status = HITLStatus.REJECTED
                else:
                    db_sess.status = HITLStatus.APPROVED

            if db_sess.created_at:
                created_tz = db_sess.created_at
                if created_tz.tzinfo is None:
                    created_tz = created_tz.replace(tzinfo=UTC)
                db_sess.latency_seconds = (now - created_tz).total_seconds()

            if modified_args:
                db_sess.arguments_json = modified_args

            await uow.commit()
            return self._to_domain(db_sess)

    async def get_sla_stats(self) -> ApprovalSLA:
        """Recalculates and retrieves average review parameters for active logs."""
        from src.db.models.hitl_session import HITLAction

        uow_ctx = self.uow_factory() if self.uow_factory else None
        if uow_ctx is None:
            from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork

            uow_ctx = SQLAlchemyUnitOfWork()

        async with uow_ctx as uow:
            sessions = await uow.hitl_sessions.list()
            resolved = [s for s in sessions if s.decision is not None]
            if not resolved:
                return ApprovalSLA()

            latencies = [s.latency_seconds for s in resolved if s.latency_seconds is not None]
            avg_time = sum(latencies) / len(latencies) if latencies else 0.0

            timeouts = len([s for s in resolved if s.decision == HITLAction.EXPIRE])
            timeout_rate = timeouts / len(resolved)

            escalated = len([s for s in resolved if s.decision == HITLAction.ESCALATE])
            escalation_rate = escalated / len(resolved)

            return ApprovalSLA(
                approval_latency=avg_time,
                average_review_time=avg_time,
                escalation_rate=escalation_rate,
                timeout_rate=timeout_rate,
            )


_global_hitl_engine: HITLEngine | None = None


def get_hitl_engine() -> HITLEngine:
    global _global_hitl_engine
    if _global_hitl_engine is None:
        _global_hitl_engine = HITLEngine()
    return _global_hitl_engine
