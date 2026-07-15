"""
ASEP — Governance Audit Trail
"""

import json
import logging
import os
from pathlib import Path

from src.governance.decision import GovernanceDecision
from src.governance.intent import ActionIntent

logger = logging.getLogger(__name__)


class AuditTrail:
    """Immutable record keeping for all governance evaluations."""

    def __init__(self, log_dir: str = "logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.log_dir / "audit.log"

    def record(self, intent: ActionIntent, decision: GovernanceDecision) -> None:
        """Log the intent and decision to local JSON Lines file."""
        record = {
            "intent": intent.model_dump(mode="json"),
            "decision": decision.model_dump(mode="json")
        }
        try:
            with open(self.audit_file, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            logger.error(f"Failed to write audit log: {exc}")
