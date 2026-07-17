from __future__ import annotations
from typing import Dict, Any
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent

class ReflectionAgent(BaseAgent):
    """Reflection Agent critiquing generated agent actions and suggesting iterative improvements."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="ReflectionAgent",
            version="1.0.0",
            description="Reviews generated results and suggests re-execution or refinements.",
            capabilities=["critique_output", "suggest_refinements"],
            supported_inputs=["candidate_output"],
            supported_outputs=["needs_revision", "suggestions"]
        )
        super().__init__(role=AgentRole.REFLECTOR, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        output = request.input_data.get("candidate_output", "")
        
        # Simple critique: if result is empty or too short, request refinement
        needs_revision = len(output.split()) < 3
        suggestions = []
        if needs_revision:
            suggestions.append("Result is too brief. Provide more background details.")
            
        return {
            "needs_revision": needs_revision,
            "suggestions": suggestions
        }
