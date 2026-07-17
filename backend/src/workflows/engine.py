"""
ASEP — Workflows Execution Engine
"""

import time
import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.workflows.models import (
    WorkflowDefinition,
    WorkflowContext,
    ExecutionState,
    Checkpoint,
    WorkflowHistory,
    WorkflowEvent,
    WorkflowStep
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """The central orchestration engine running asynchronous agent execution graphs."""

    def __init__(self) -> None:
        self.active_executions: Dict[str, ExecutionState] = {}
        self.checkpoints: Dict[str, Checkpoint] = {}
        self.histories: Dict[str, WorkflowHistory] = {}
        
        # Metrics trackers
        self.active_count = 0
        self.total_completed = 0
        self.total_failed = 0
        self.total_retries = 0

    def get_metrics(self) -> Dict[str, Any]:
        """Observability telemetry snapshot."""
        total = self.total_completed + self.total_failed
        success_rate = (self.total_completed / total) if total > 0 else 1.0
        return {
            "active_workflows": self.active_count,
            "queued_workflows": 0,
            "retry_rate": self.total_retries,
            "failure_rate": self.total_failed,
            "success_rate": success_rate,
            "checkpoint_count": len(self.checkpoints)
        }

    def _emit(self, event: WorkflowEvent, execution_id: str, details: str = "") -> None:
        logger.info(f"[WorkflowTelemetry] Event={event.value} execution_id={execution_id} | {details}")

    async def execute(
        self,
        definition: WorkflowDefinition,
        context: WorkflowContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Launches or resumes execution of a workflow definition."""
        execution_id = context.execution_id
        
        # Check if already completed/cancelled
        if execution_id in self.histories and self.histories[execution_id].end_time is not None:
            return self.checkpoints[execution_id].agent_outputs

        if not definition.is_enabled:
            raise ValueError(f"Workflow {definition.workflow_id} is currently disabled.")

        self.active_executions[execution_id] = ExecutionState.RUNNING
        self.active_count += 1
        
        # Initialize history record
        if execution_id not in self.histories:
            self.histories[execution_id] = WorkflowHistory(
                execution_id=execution_id,
                workflow_id=definition.workflow_id
            )
            self._emit(WorkflowEvent.STARTED, execution_id)
            
        history = self.histories[execution_id]
        history.state_transitions.append({"state": "RUNNING", "time": time.time()})

        # Load or initialize checkpoint
        if execution_id not in self.checkpoints:
            checkpoint = Checkpoint(
                execution_id=execution_id,
                workflow_state=ExecutionState.RUNNING,
                current_node=definition.steps[0].node_id if definition.steps else None,
                pending_nodes=[step.node_id for step in definition.steps]
            )
            self.checkpoints[execution_id] = checkpoint
            self._emit(WorkflowEvent.CHECKPOINT_CREATED, execution_id, f"node={checkpoint.current_node}")
        else:
            checkpoint = self.checkpoints[execution_id]
            checkpoint.workflow_state = ExecutionState.RUNNING
            self._emit(WorkflowEvent.CHECKPOINT_RESTORED, execution_id, f"node={checkpoint.current_node}")

        # Execution loop
        while checkpoint.current_node:
            state = self.active_executions.get(execution_id)
            if state in (ExecutionState.PAUSED, ExecutionState.WAITING_HITL, ExecutionState.CANCELLED):
                break

            current_step = next((s for s in definition.steps if s.node_id == checkpoint.current_node), None)
            if not current_step:
                break

            try:
                # 1. Check if step already completed from previous checkpoint run
                if current_step.node_id in checkpoint.completed_nodes:
                    # Move to next node
                    checkpoint.current_node = self._resolve_next_node(current_step, checkpoint)
                    continue

                # 2. Execute parallel nodes if configured (fan-out / fan-in)
                if current_step.parallel_nodes:
                    self._emit(WorkflowEvent.CHECKPOINT_CREATED, execution_id, f"Fan-out to parallel steps {current_step.parallel_nodes}")
                    parallel_tasks = [
                        self._execute_step_with_retries(step_id, definition, checkpoint, inputs)
                        for step_id in current_step.parallel_nodes
                    ]
                    await asyncio.gather(*parallel_tasks)
                    # Sync join node
                    checkpoint.current_node = current_step.join_node
                    checkpoint.completed_nodes.extend(current_step.parallel_nodes)
                    continue

                # 3. Normal single node step execution with retries
                await self._execute_step_with_retries(current_step.node_id, definition, checkpoint, inputs)
                
                # Check for WAITING_HITL transition during execution (e.g. step simulation triggers approval)
                if self.active_executions.get(execution_id) == ExecutionState.WAITING_HITL:
                    self._emit(WorkflowEvent.PAUSED, execution_id, "Suspended at HITL approval gate.")
                    break

                checkpoint.completed_nodes.append(current_step.node_id)
                if current_step.node_id in checkpoint.pending_nodes:
                    checkpoint.pending_nodes.remove(current_step.node_id)
                
                # Resolve routing logic
                checkpoint.current_node = self._resolve_next_node(current_step, checkpoint)
                
                # Commit checkpoint
                if definition.checkpoint_policy.on_step_complete:
                    self._emit(WorkflowEvent.CHECKPOINT_CREATED, execution_id, f"Committed checkpoint node={checkpoint.current_node}")

            except Exception as e:
                self.total_failed += 1
                checkpoint.workflow_state = ExecutionState.FAILED
                self.active_executions[execution_id] = ExecutionState.FAILED
                history.failures.append({"step": checkpoint.current_node, "error": str(e), "time": time.time()})
                self._emit(WorkflowEvent.FAILED, execution_id, f"Error at step {checkpoint.current_node}: {str(e)}")
                self.active_count -= 1
                raise e

        # Finalize execution state
        final_state = self.active_executions.get(execution_id)
        if final_state == ExecutionState.RUNNING:
            checkpoint.workflow_state = ExecutionState.COMPLETED
            self.active_executions[execution_id] = ExecutionState.COMPLETED
            history.end_time = time.time()
            history.execution_duration = history.end_time - history.start_time
            self.total_completed += 1
            self.active_count -= 1
            self._emit(WorkflowEvent.COMPLETED, execution_id)
            
        return checkpoint.agent_outputs

    def _resolve_next_node(self, step: WorkflowStep, checkpoint: Checkpoint) -> Optional[str]:
        """Resolves switch keys or sequential pointers."""
        if step.conditional_routes:
            # Look up evaluation outcome from agent_outputs
            step_output = checkpoint.agent_outputs.get(step.node_id, {})
            outcome = step_output.get("outcome", "default")
            return step.conditional_routes.get(outcome, step.next_node)
        return step.next_node

    async def _execute_step_with_retries(
        self,
        node_id: str,
        definition: WorkflowDefinition,
        checkpoint: Checkpoint,
        inputs: Dict[str, Any]
    ) -> None:
        """Executes a single step running retries with exponential backoffs."""
        step = next((s for s in definition.steps if s.node_id == node_id), None)
        if not step:
            return

        policy = definition.retry_policy
        attempts = 0
        
        while attempts <= policy.max_retries:
            try:
                # Execution simulation: target routing target agent outputs
                # In real graphs, this maps directly to AgentRuntime invoke/call executions
                logger.info(f"Executing step {node_id} on target={step.target_agent}")
                
                # Check if this simulates high-risk terminal/HITL gate
                if step.target_tool == "terminal" and checkpoint.approval_state is None:
                    # Suspend execution to wait for approval
                    self.active_executions[checkpoint.execution_id] = ExecutionState.WAITING_HITL
                    checkpoint.workflow_state = ExecutionState.WAITING_HITL
                    checkpoint.approval_state = "PENDING"
                    return

                # Record output values
                existing_outcome = checkpoint.agent_outputs.get(node_id, {}).get("outcome")
                checkpoint.agent_outputs[node_id] = {
                    "status": "success",
                    "timestamp": time.time(),
                    "agent": step.target_agent,
                    "outcome": existing_outcome or "success"
                }
                return
            except Exception as e:
                attempts += 1
                self.total_retries += 1
                self._emit(WorkflowEvent.RETRY, checkpoint.execution_id, f"Attempt {attempts} failed: {str(e)}")
                
                # Verify non-retryable conditions
                if attempts > policy.max_retries or any(cond in str(e) for cond in policy.retry_conditions):
                    raise e
                    
                # Backoff delay
                delay = policy.initial_delay * (policy.backoff_factor ** (attempts - 1))
                await asyncio.sleep(delay)

    def pause(self, execution_id: str) -> None:
        """Pause execution progress."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id] = ExecutionState.PAUSED
            self.checkpoints[execution_id].workflow_state = ExecutionState.PAUSED
            self._emit(WorkflowEvent.PAUSED, execution_id)

    def resume(self, execution_id: str) -> None:
        """Resumes a paused execution."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id] = ExecutionState.RUNNING
            self.checkpoints[execution_id].workflow_state = ExecutionState.RUNNING
            self._emit(WorkflowEvent.RESUMED, execution_id)

    def cancel(self, execution_id: str) -> None:
        """Force cancel execution."""
        if execution_id in self.active_executions:
            self.active_executions[execution_id] = ExecutionState.CANCELLED
            self.checkpoints[execution_id].workflow_state = ExecutionState.CANCELLED
            self.histories[execution_id].end_time = time.time()
            self.active_count -= 1
            self._emit(WorkflowEvent.CANCELLED, execution_id)


_global_workflow_engine: Optional[WorkflowEngine] = None

def get_workflow_engine() -> WorkflowEngine:
    global _global_workflow_engine
    if _global_workflow_engine is None:
        _global_workflow_engine = WorkflowEngine()
    return _global_workflow_engine
