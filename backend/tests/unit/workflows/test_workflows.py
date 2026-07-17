from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.workflows.models import (
    WorkflowDefinition,
    WorkflowStep,
    RetryPolicy,
    WorkflowContext,
    ExecutionState
)
from src.workflows.registry import get_workflow_registry
from src.workflows.engine import get_workflow_engine


@pytest.mark.asyncio
async def test_workflow_registry_and_execution_lifecycle():
    registry = get_workflow_registry()
    engine = get_workflow_engine()
    
    # 1. Build and register simple workflow definition
    step1 = WorkflowStep(
        node_id="step-1",
        description="First execution step",
        target_agent="planner",
        next_node="step-2"
    )
    step2 = WorkflowStep(
        node_id="step-2",
        description="Second execution step",
        target_agent="researcher"
    )
    
    wf = WorkflowDefinition(
        workflow_id="simple-seq",
        description="Simple sequential workflow",
        steps=[step1, step2],
        retry_policy=RetryPolicy(max_retries=1)
    )
    registry.register_workflow(wf)
    
    assert registry.lookup("simple-seq") == wf
    
    # 2. Execute workflow
    context = WorkflowContext(
        workflow_id="simple-seq",
        execution_id="exec-simple-1",
        correlation_id="corr-simple-1",
        session_id="session-simple-1"
    )
    
    outputs = await engine.execute(wf, context, {})
    assert outputs["step-1"]["status"] == "success"
    assert outputs["step-2"]["status"] == "success"
    
    checkpoint = engine.checkpoints["exec-simple-1"]
    assert checkpoint.workflow_state == ExecutionState.COMPLETED
    assert checkpoint.completed_nodes == ["step-1", "step-2"]


@pytest.mark.asyncio
async def test_conditional_routing_workflow():
    registry = get_workflow_registry()
    engine = get_workflow_engine()
    
    # Define steps with conditional routing
    step_decide = WorkflowStep(
        node_id="decide-step",
        description="Decide routing path",
        target_agent="planner",
        conditional_routes={
            "path_a": "step-a",
            "path_b": "step-b"
        }
    )
    step_a = WorkflowStep(node_id="step-a", description="Path A step", target_agent="researcher")
    step_b = WorkflowStep(node_id="step-b", description="Path B step", target_agent="researcher")
    
    wf = WorkflowDefinition(
        workflow_id="conditional-wf",
        description="Conditional workflow paths",
        steps=[step_decide, step_a, step_b]
    )
    registry.register_workflow(wf)
    
    context = WorkflowContext(
        workflow_id="conditional-wf",
        execution_id="exec-cond-1",
        correlation_id="corr-cond-1",
        session_id="session-cond-1"
    )
    
    # We will simulate a conditional choice outcome using pre-seeded outputs
    # For decide-step, we specify outcome="path_b"
    checkpoint = engine.checkpoints.get("exec-cond-1")
    if not checkpoint:
        from src.workflows.models import Checkpoint
        checkpoint = Checkpoint(
            execution_id="exec-cond-1",
            workflow_state=ExecutionState.RUNNING,
            current_node="decide-step",
            pending_nodes=["decide-step", "step-a", "step-b"],
            agent_outputs={"decide-step": {"outcome": "path_b"}}
        )
        engine.checkpoints["exec-cond-1"] = checkpoint
        
    outputs = await engine.execute(wf, context, {})
    # Should follow path_b and complete decide-step and step-b, skipping step-a
    assert checkpoint.completed_nodes == ["decide-step", "step-b"]
    assert "step-a" not in checkpoint.completed_nodes


@pytest.mark.asyncio
async def test_hitl_checkpoint_resume_flow():
    registry = get_workflow_registry()
    engine = get_workflow_engine()
    
    # Step 1 is normal. Step 2 requires terminal execution which triggers WAITING_HITL checkpoint pause.
    step1 = WorkflowStep(
        node_id="step-normal",
        description="Normal step",
        target_agent="planner",
        next_node="step-critical"
    )
    step_critical = WorkflowStep(
        node_id="step-critical",
        description="Destructive action step",
        target_agent="executor",
        target_tool="terminal" # tool execution triggers HITL queue suspension
    )
    
    wf = WorkflowDefinition(
        workflow_id="hitl-wf",
        description="HITL triggered workflow pause",
        steps=[step1, step_critical]
    )
    registry.register_workflow(wf)
    
    context = WorkflowContext(
        workflow_id="hitl-wf",
        execution_id="exec-hitl-1",
        correlation_id="corr-hitl-1",
        session_id="session-hitl-1"
    )
    
    # Execute workflow. It should stop at step-critical.
    await engine.execute(wf, context, {})
    
    checkpoint = engine.checkpoints["exec-hitl-1"]
    assert checkpoint.workflow_state == ExecutionState.WAITING_HITL
    assert checkpoint.completed_nodes == ["step-normal"]
    assert checkpoint.approval_state == "PENDING"
    
    # Approve session override
    checkpoint.approval_state = "APPROVED"
    engine.resume("exec-hitl-1")
    
    # Execute again. It should resume from latest checkpoint and complete the step.
    outputs = await engine.execute(wf, context, {})
    assert checkpoint.workflow_state == ExecutionState.COMPLETED
    assert "step-critical" in checkpoint.completed_nodes


def test_workflow_api_endpoints():
    app = create_app()
    client = TestClient(app)
    
    # Verify GET /api/v1/workflows
    resp = client.get("/api/v1/workflows")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    
    # Verify GET /api/v1/workflows/history
    resp_hist = client.get("/api/v1/workflows/history")
    assert resp_hist.status_code == 200
    assert isinstance(resp_hist.json(), list)
