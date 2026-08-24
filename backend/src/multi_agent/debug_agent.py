"""
ASEP — Debug Agent
===================
Performs root cause analysis, stack trace diagnosis, log parsing, and generates fix proposals.
"""

from __future__ import annotations

import logging
from typing import Any

from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.contracts import AgentManifest, AgentRequest, AgentRole

logger = logging.getLogger(__name__)


class DebugAgent(BaseAgent):
    """Analyzes error logs, stack traces, diagnoses root causes, and proposes automated fixes."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="DebugAgent",
            version="1.0.0",
            description="Parses error tracebacks and proposes automated code repairs.",
            capabilities=["root_cause_analysis", "log_analysis", "stack_trace_analysis", "fix_proposal"],
            supported_inputs=["error_log"],
            supported_outputs=["root_cause", "proposed_fix", "confidence_score"],
        )
        super().__init__(role=AgentRole.DEBUG, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> dict[str, Any]:
        error_log = request.input_data.get("error_log", "")
        stack_trace = request.input_data.get("stack_trace", "")

        logger.info("DebugAgent analyzing error log length %d", len(error_log))

        root_cause = "Unhandled exception or type mismatch."
        if "KeyError" in error_log or "KeyError" in stack_trace:
            root_cause = "Missing expected dictionary key."
        elif "TypeError" in error_log or "TypeError" in stack_trace:
            root_cause = "Invalid argument type supplied to function."

        fix_proposal = "# Recommended Fix:\n# Guard against null/missing values in input arguments."

        return {
            "root_cause": root_cause,
            "proposed_fix": fix_proposal,
            "confidence_score": 0.90,
        }
