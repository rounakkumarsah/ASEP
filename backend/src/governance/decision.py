"""
ASEP — Governance Decisions
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DecisionResult(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    SANDBOX_ONLY = "SANDBOX_ONLY"
    READ_ONLY = "READ_ONLY"

class ApprovalState(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"

class GovernanceDecision(BaseModel):
    """The outcome of a governance evaluation."""
    intent_id: str
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str

    result: DecisionResult
    reason: str = Field(default="")
    policy_id: str = Field(default="default")

    # State tracking if approval is requested
    approval_state: ApprovalState | None = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
