from __future__ import annotations
import uuid
import time
from typing import Dict, Any, List
from src.multi_agent.contracts import (
    AgentRole,
    AgentManifest,
    AgentRequest,
    AgentResponse,
    AgentState,
    AgentEventName
)
from src.multi_agent.base_agent import BaseAgent
from src.multi_agent.registry import AgentRegistry, get_agent_registry
from src.multi_agent.engine import ExecutionEngine, ExecutionTask

class SupervisorAgent(BaseAgent):
    """Supervisor Agent serving as the single entrypoint coordinating planning, execution, evaluations, and compliance."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        manifest = AgentManifest(
            name="SupervisorAgent",
            version="1.0.0",
            description="Coordinates multi-agent planning, execution, and verification pipelines.",
            capabilities=["orchestration", "workflow_coordination"],
            supported_inputs=["request"],
            supported_outputs=["final_result", "status", "execution_steps"]
        )
        super().__init__(role=AgentRole.SUPERVISOR, manifest=manifest)
        self.registry = registry or get_agent_registry()
        self.engine = ExecutionEngine(self.registry)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        execution_id = request.execution_id
        correlation_id = request.correlation_id
        goal = request.input_data.get("request", "")
        
        self._emit_event(
            execution_id=execution_id,
            correlation_id=correlation_id,
            event_name=AgentEventName.SUPERVISOR_STARTED,
            message=f"Supervisor started workflow session for: {goal}"
        )
        
        # Step 1: Call Planner Agent to get decomposed tasks
        planner = self.registry.lookup(AgentRole.PLANNER)
        if not planner:
            raise ValueError("Planner agent not registered.")
            
        planner_req = AgentRequest(
            execution_id=execution_id,
            correlation_id=correlation_id,
            input_data={"request": goal}
        )
        planner_resp = await planner.execute(planner_req)
        if planner_resp.status != AgentState.COMPLETED:
            raise ValueError(f"Planning failed: {planner_resp.error_message}")
            
        subtasks_data = planner_resp.output_data.get("subtasks", [])
        
        # Step 2: Build execution engine tasks
        execution_tasks = []
        for st in subtasks_data:
            execution_tasks.append(
                ExecutionTask(
                    task_id=st["task_id"],
                    agent_role=AgentRole(st["agent_role"]),
                    input_data=st["input_data"],
                    dependencies=set(st["dependencies"])
                )
            )
            
        # Step 3: Run execution graph
        step_results = await self.engine.execute_dag(
            execution_id=execution_id,
            correlation_id=correlation_id,
            tasks=execution_tasks
        )
        
        # Consolidate candidate execution output
        candidate_result = ""
        exec_step = step_results.get("agent_execution")
        if exec_step and exec_step.status == AgentState.COMPLETED:
            candidate_result = exec_step.output_data.get("result", "")
            
        # Step 4: Run Governance compliance validation before finalizing
        gov = self.registry.lookup(AgentRole.GOVERNANCE)
        approved = True
        risk_score = 0.0
        policy_notes = "No governance agent registered."
        
        if gov:
            gov_req = AgentRequest(
                execution_id=execution_id,
                correlation_id=correlation_id,
                input_data={"candidate_result": candidate_result}
            )
            gov_resp = await gov.execute(gov_req)
            if gov_resp.status == AgentState.COMPLETED:
                approved = gov_resp.output_data.get("approved", True)
                risk_score = gov_resp.output_data.get("risk_score", 0.0)
                policy_notes = gov_resp.output_data.get("policy_notes", "")

        self._emit_event(
            execution_id=execution_id,
            correlation_id=correlation_id,
            event_name=AgentEventName.SUPERVISOR_COMPLETED,
            message="Supervisor completed workflow session."
        )

        return {
            "final_result": candidate_result if approved else "Execution rejected by Governance compliance rules.",
            "status": "completed" if approved else "rejected",
            "risk_score": risk_score,
            "policy_notes": policy_notes,
            "execution_steps": {tid: res.status.value for tid, res in step_results.items()}
        }
