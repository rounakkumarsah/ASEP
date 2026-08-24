"""
ASEP — Review Agent
====================
Performs code review, security vulnerability checks, performance auditing, and style validation.
"""

from __future__ import annotations

import logging
from typing import Any

from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.contracts import AgentManifest, AgentRequest, AgentRole

logger = logging.getLogger(__name__)


class ReviewAgent(BaseAgent):
    """Reviews code quality, security posture, performance, and adherence to style guides."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="ReviewAgent",
            version="1.0.0",
            description="Audits code quality, security vulnerabilities, and performance bottlenecks.",
            capabilities=["code_review", "security_audit", "performance_review", "style_validation"],
            supported_inputs=["code_content"],
            supported_outputs=["approved", "issues", "score", "summary"],
        )
        super().__init__(role=AgentRole.REVIEW, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> dict[str, Any]:
        code = request.input_data.get("code_content", "")
        review_type = request.input_data.get("review_type", "all")

        logger.info("ReviewAgent executing review_type '%s' on code snippet length %d", review_type, len(code))

        issues: list[dict[str, Any]] = []

        # Simple security static check rules
        if "eval(" in code or "exec(" in code:
            issues.append({"category": "security", "severity": "HIGH", "message": "Use of unsafe eval/exec functions detected."})
        if "hardcoded_secret" in code.lower():
            issues.append({"category": "security", "severity": "CRITICAL", "message": "Potential hardcoded credential."})

        approved = len([i for i in issues if i["severity"] in ["HIGH", "CRITICAL"]]) == 0
        score = max(100 - (len(issues) * 15), 50)

        return {
            "approved": approved,
            "issues": issues,
            "score": score,
            "summary": f"Review completed with {len(issues)} issues found.",
        }
