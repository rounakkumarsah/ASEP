from __future__ import annotations
import asyncio
import logging
from typing import Dict, Any, List, Set
from src.multi_agent.contracts import AgentRequest, AgentResponse, AgentState, AgentRole
from src.multi_agent.registry import AgentRegistry, get_agent_registry

logger = logging.getLogger(__name__)

class ExecutionTask:
    def __init__(
        self,
        task_id: str,
        agent_role: AgentRole,
        input_data: Dict[str, Any],
        dependencies: Set[str] | None = None,
        timeout_seconds: float = 30.0
    ) -> None:
        self.task_id = task_id
        self.agent_role = agent_role
        self.input_data = input_data
        self.dependencies = dependencies or set()
        self.timeout_seconds = timeout_seconds
        self.response: AgentResponse | None = None

class ExecutionEngine:
    """Enterprise-grade framework-agnostic DAG concurrency execution engine supporting task dependencies."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or get_agent_registry()

    async def execute_dag(
        self,
        execution_id: str,
        correlation_id: str,
        tasks: List[ExecutionTask]
    ) -> Dict[str, AgentResponse]:
        """Resolves task dependency trees, scheduling parallel execution nodes concurrently."""
        completed_tasks: Dict[str, AgentResponse] = {}
        task_map = {t.task_id: t for t in tasks}
        
        # Track pending task mappings
        pending_ids = set(task_map.keys())
        
        while pending_ids:
            # Find tasks with all dependencies satisfied
            runnable_tasks = []
            for tid in pending_ids:
                task = task_map[tid]
                if all(dep in completed_tasks and completed_tasks[dep].status == AgentState.COMPLETED for dep in task.dependencies):
                    runnable_tasks.append(task)
            
            if not runnable_tasks:
                # Dependency cycle or unresolved failure
                remaining_unresolved = list(pending_ids)
                logger.error(f"Execution deadlock detected. Unresolved tasks: {remaining_unresolved}")
                for tid in remaining_unresolved:
                    task = task_map[tid]
                    task.response = AgentResponse(
                        execution_id=execution_id,
                        correlation_id=correlation_id,
                        status=AgentState.FAILED,
                        error_message="Dependency requirements unsatisfied."
                    )
                    completed_tasks[tid] = task.response
                break

            # Execute all runnable tasks concurrently
            async def run_single_task(t: ExecutionTask):
                agent = self.registry.lookup(t.agent_role)
                if not agent:
                    t.response = AgentResponse(
                        execution_id=execution_id,
                        correlation_id=correlation_id,
                        status=AgentState.FAILED,
                        error_message=f"Agent {t.agent_role.value} not found in registry."
                    )
                    return t.response
                
                # Consolidate parent output payloads into input context
                merged_inputs = dict(t.input_data)
                for dep in t.dependencies:
                    dep_response = completed_tasks[dep]
                    merged_inputs[f"parent_{dep}"] = dep_response.output_data

                req = AgentRequest(
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                    input_data=merged_inputs,
                    timeout_seconds=t.timeout_seconds
                )
                
                t.response = await agent.execute(req)
                return t.response

            results = await asyncio.gather(*(run_single_task(t) for t in runnable_tasks))
            
            for t, res in zip(runnable_tasks, results):
                completed_tasks[t.task_id] = res
                pending_ids.remove(t.task_id)
                
        return completed_tasks
