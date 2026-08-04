"""
ASEP — Coding Agent
====================
Handles code generation, feature implementation, refactoring, and patch generation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.contracts import AgentManifest, AgentRequest, AgentRole

logger = logging.getLogger(__name__)


class CodingAgent(BaseAgent):
    """Generates code, implements features, performs refactoring, and creates patches."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="CodingAgent",
            version="1.0.0",
            description="Generates, refactors, and patches code based on design specs.",
            capabilities=["code_generation", "refactoring", "patching", "implementation"],
            supported_inputs=["specification", "action"],
            supported_outputs=["generated_code", "patch", "status"],
        )
        super().__init__(role=AgentRole.CODING, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        spec = request.input_data.get("specification", "")
        action = request.input_data.get("action", "generate")
        language = request.input_data.get("language", "python")

        logger.info("CodingAgent executing action '%s' for spec: %s", action, spec[:80])

        if action == "refactor":
            result_code = f"# Refactored {language} code for: {spec}\n# Optimized for performance and readability."
        elif action == "patch":
            result_code = f"--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@\n-# Fix applied for: {spec}\n+# Updated logic"
        else:
            result_code = f"# Generated {language} code implementing: {spec}\n\ndef main():\n    pass\n"

        return {
            "generated_code": result_code,
            "patch": f"patch_for_{action}.diff",
            "status": "completed",
            "language": language,
        }
