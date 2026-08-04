"""
ASEP — Human-in-the-Loop (HITL) Engine
=======================================
Provides human approval gates, manual review queues, interrupt/resume capability, and audit history.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTERRUPTED = "interrupted"


@dataclass
class HumanApprovalGate:
    gate_id: str
    execution_id: str
    action_type: str
    payload: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_notes: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class HITLEngine:
    """Manages Human-in-the-Loop gates, interrupts, manual reviews, and audit trails."""

    def __init__(self) -> None:
        self._gates: Dict[str, HumanApprovalGate] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def create_gate(
        self,
        gate_id: str,
        execution_id: str,
        action_type: str,
        payload: Dict[str, Any],
    ) -> HumanApprovalGate:
        gate = HumanApprovalGate(
            gate_id=gate_id,
            execution_id=execution_id,
            action_type=action_type,
            payload=payload,
        )
        self._gates[gate_id] = gate
        self._record_audit(execution_id, f"Gate '{gate_id}' created for action '{action_type}'")
        return gate

    def submit_review(
        self,
        gate_id: str,
        approved: bool,
        reviewer_notes: Optional[str] = None,
    ) -> HumanApprovalGate:
        gate = self._gates.get(gate_id)
        if not gate:
            raise KeyError(f"Approval gate '{gate_id}' not found.")

        gate.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        gate.reviewer_notes = reviewer_notes
        gate.updated_at = time.time()

        action = "Approved" if approved else "Rejected"
        self._record_audit(gate.execution_id, f"Gate '{gate_id}' {action}. Notes: {reviewer_notes}")
        return gate

    def interrupt_execution(self, execution_id: str, reason: str) -> None:
        self._record_audit(execution_id, f"Execution INTERRUPTED. Reason: {reason}")

    def resume_execution(self, execution_id: str) -> None:
        self._record_audit(execution_id, "Execution RESUMED by operator.")

    def _record_audit(self, execution_id: str, message: str) -> None:
        entry = {
            "timestamp": time.time(),
            "execution_id": execution_id,
            "message": message,
        }
        self._audit_log.append(entry)
        logger.info("HITL Audit Entry: [%s] %s", execution_id, message)

    def get_audit_trail(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if execution_id:
            return [e for e in self._audit_log if e["execution_id"] == execution_id]
        return list(self._audit_log)
