from __future__ import annotations
from typing import Dict, Any, List
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Planner Agent analyzing complex task requirements and mapping dependency execution nodes."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="PlannerAgent",
            version="1.0.0",
            description="Analyzes complex requests, estimates complexity, and decomposes goals into subtasks.",
            capabilities=["planning", "goal_decomposition", "complexity_estimation"],
            supported_inputs=["request"],
            supported_outputs=["subtasks", "complexity_score", "plan"]
        )
        super().__init__(role=AgentRole.PLANNER, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        goal = request.input_data.get("request", "")
        
        # Deconstruct and analyze requirements
        complexity_score = min(1.0, max(0.1, len(goal.split()) / 50.0))
        
        subtasks = [
            {
                "task_id": "knowledge_retrieval",
                "agent_role": "knowledge",
                "input_data": {"query": goal},
                "dependencies": []
            },
            {
                "task_id": "research_enrichment",
                "agent_role": "research",
                "input_data": {"query": goal},
                "dependencies": []
            },
            {
                "task_id": "agent_execution",
                "agent_role": "executor",
                "input_data": {"prompt": goal},
                "dependencies": ["knowledge_retrieval"]
            },
            {
                "task_id": "agent_evaluation",
                "agent_role": "evaluator",
                "input_data": {},
                "dependencies": ["agent_execution"]
            }
        ]
        
        return {
            "subtasks": subtasks,
            "complexity_score": complexity_score,
            "plan": f"Plan compiled for: {goal}"
        }
