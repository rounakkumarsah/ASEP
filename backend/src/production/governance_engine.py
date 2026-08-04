"""
ASEP — Enterprise Governance & Audit Engine
============================================
Tracks permission audits, policy violations, prompt versions, and model version histories.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyViolation:
    violation_id: str
    execution_id: str
    policy_name: str
    severity: str
    details: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PromptVersion:
    prompt_id: str
    version: str
    content: str
    author: str
    timestamp: float = field(default_factory=time.time)


class GovernanceEngine:
    """Manages compliance policies, audit logging, and versioning history."""

    def __init__(self) -> None:
        self._violations: List[PolicyViolation] = []
        self._prompt_history: Dict[str, List[PromptVersion]] = {}
        self._model_history: Dict[str, str] = {"default": "gemini-2.5-flash"}

    def record_violation(
        self,
        violation_id: str,
        execution_id: str,
        policy_name: str,
        severity: str,
        details: str,
    ) -> PolicyViolation:
        v = PolicyViolation(
            violation_id=violation_id,
            execution_id=execution_id,
            policy_name=policy_name,
            severity=severity,
            details=details,
        )
        self._violations.append(v)
        logger.warning(
            "Policy Violation Recorded [%s]: %s (severity=%s)",
            execution_id,
            policy_name,
            severity,
        )
        return v

    def register_prompt_version(
        self, prompt_id: str, version: str, content: str, author: str
    ) -> PromptVersion:
        pv = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            content=content,
            author=author,
        )
        self._prompt_history.setdefault(prompt_id, []).append(pv)
        logger.info("Prompt version registered: %s v%s", prompt_id, version)
        return pv

    def get_prompt_history(self, prompt_id: str) -> List[PromptVersion]:
        return self._prompt_history.get(prompt_id, [])

    def get_violations(self, execution_id: Optional[str] = None) -> List[PolicyViolation]:
        if execution_id:
            return [v for v in self._violations if v.execution_id == execution_id]
        return list(self._violations)
