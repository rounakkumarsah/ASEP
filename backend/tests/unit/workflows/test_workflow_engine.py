"""
ASEP — Unit Tests for Workflow Engine
"""

import pytest
from src.workflows.engine import WorkflowEngine
from src.workflows.models import (
    CheckpointPolicy,
    ExecutionState,
    RetryPolicy,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowStep,
)


@pytest.mark.asyncio
async def test_workflow_engine_execute_sequential():
    engine = WorkflowEngine()

    step1 = WorkflowStep(node_id="step-1", target_agent="research", next_node="step-2")
    step2 = WorkflowStep(node_id="step-2", target_agent="executor", next_node=None)

    wf_def = WorkflowDefinition(
        workflow_id="wf-1",
        name="Sequential Test WF",
        description="Test workflow",
        steps=[step1, step2],
        is_enabled=True,
    )
    context = WorkflowContext(workflow_id="wf-1", execution_id="exec-123")

    outputs = await engine.execute(wf_def, context, inputs={})

    assert "step-1" in outputs
    assert "step-2" in outputs
    assert engine.active_executions["exec-123"] == ExecutionState.COMPLETED


@pytest.mark.asyncio
async def test_workflow_engine_conditional_branch():
    engine = WorkflowEngine()

    step1 = WorkflowStep(
        node_id="step-1",
        target_agent="planner",
        conditional_routes={"pass": "step-2", "fail": "step-3"},
        next_node="step-2",
    )
    step2 = WorkflowStep(node_id="step-2", target_agent="executor")
    step3 = WorkflowStep(node_id="step-3", target_agent="governance")

    wf_def = WorkflowDefinition(
        workflow_id="wf-2",
        name="Conditional WF",
        steps=[step1, step2, step3],
        is_enabled=True,
    )
    context = WorkflowContext(workflow_id="wf-2", execution_id="exec-conditional")

    outputs = await engine.execute(wf_def, context, inputs={})
    assert "step-1" in outputs
    assert "step-2" in outputs
    assert "step-3" not in outputs


@pytest.mark.asyncio
async def test_workflow_engine_parallel_execution():
    engine = WorkflowEngine()

    step_parallel = WorkflowStep(
        node_id="fan-out",
        parallel_nodes=["p-1", "p-2"],
        join_node="join-node",
    )
    p1 = WorkflowStep(node_id="p-1", target_agent="agent-1")
    p2 = WorkflowStep(node_id="p-2", target_agent="agent-2")
    join_node = WorkflowStep(node_id="join-node", target_agent="supervisor")

    wf_def = WorkflowDefinition(
        workflow_id="wf-parallel",
        name="Parallel Test WF",
        steps=[step_parallel, p1, p2, join_node],
        is_enabled=True,
    )
    context = WorkflowContext(workflow_id="wf-parallel", execution_id="exec-parallel")

    outputs = await engine.execute(wf_def, context, inputs={})

    assert "p-1" in outputs
    assert "p-2" in outputs
    assert "join-node" in outputs


@pytest.mark.asyncio
async def test_workflow_engine_hitl_approval_pause_and_resume():
    engine = WorkflowEngine()

    hitl_step = WorkflowStep(node_id="terminal-step", target_tool="terminal")
    wf_def = WorkflowDefinition(
        workflow_id="wf-hitl",
        name="HITL Test WF",
        steps=[hitl_step],
        is_enabled=True,
    )
    context = WorkflowContext(workflow_id="wf-hitl", execution_id="exec-hitl")

    # Initial execution pauses at WAITING_HITL
    await engine.execute(wf_def, context, inputs={})
    assert engine.active_executions["exec-hitl"] == ExecutionState.WAITING_HITL

    # Resume workflow
    engine.checkpoints["exec-hitl"].approval_state = "APPROVED"
    engine.resume("exec-hitl")
    assert engine.active_executions["exec-hitl"] == ExecutionState.RUNNING
