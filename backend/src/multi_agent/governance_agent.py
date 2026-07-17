from __future__ import annotations
from typing import Dict, Any
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent

class GovernanceAgent(BaseAgent):
    """Governance Agent ensuring compliance policy execution, routing approvals, and scoring risk coefficients."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="GovernanceAgent",
            version="1.0.0",
            description="Performs policy validation, approval gating, and risk scoring.",
            capabilities=["policy_validation", "approval_routing", "risk_scoring"],
            supported_inputs=["candidate_result"],
            supported_outputs=["approved", "risk_score", "policy_notes"]
        )
        super().__init__(role=AgentRole.GOVERNANCE, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        tool_name = request.input_data.get("tool_name")
        if tool_name:
            from src.tools import get_tool_registry, verify_tool_permissions
            registry = get_tool_registry()
            tool = registry.lookup(tool_name)
            if tool:
                granted_permissions = request.input_data.get("granted_permissions", [])
                authorized, reason = verify_tool_permissions(tool.required_permissions, granted_permissions)
                if not authorized:
                    return {
                        "approved": False,
                        "risk_score": 1.0,
                        "policy_notes": f"Governance Gate: Permission Denied for tool '{tool_name}': {reason}"
                    }

        result = request.input_data.get("candidate_result", "")
        
        # Simple policy compliance check
        approved = True
        risk_score = 0.1
        
        # Flag higher risk if prompt includes restricted terminology
        restricted = ["hack", "bypass", "exploit", "rootkit"]
        for word in restricted:
            if word in result.lower():
                approved = False
                risk_score = 0.95
                break

        return {
            "approved": approved,
            "risk_score": risk_score,
            "policy_notes": "All checks validated against standard platform rules." if approved else "Restricted keyword matched."
        }
