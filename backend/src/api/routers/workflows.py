"""
ASEP — API Router for Autonomous Workflows
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.workflows.registry import get_workflow_registry
from src.workflows.engine import get_workflow_engine
from src.workflows.models import (
    WorkflowDefinition,
    WorkflowContext,
    WorkflowHistory,
    Checkpoint
)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class WorkflowStartRequest(BaseModel):
    workflow_id: str
    execution_id: str
    correlation_id: str
    session_id: str
    inputs: Dict[str, Any]


class WorkflowActionRequest(BaseModel):
    execution_id: str


@router.get("", response_model=List[WorkflowDefinition])
async def list_workflows() -> List[WorkflowDefinition]:
    """Retrieve all registered workflows."""
    registry = get_workflow_registry()
    return registry.discover_workflows()


@router.get("/history", response_model=List[WorkflowHistory])
async def get_history() -> List[WorkflowHistory]:
    """Retrieve history of all workflow executions."""
    engine = get_workflow_engine()
    return list(engine.histories.values())


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str) -> WorkflowDefinition:
    """Retrieve a specific workflow definition."""
    registry = get_workflow_registry()
    wf = registry.lookup(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return wf


@router.post("/start")
async def start_workflow(req: WorkflowStartRequest) -> Dict[str, Any]:
    """Execute a workflow execution instance."""
    registry = get_workflow_registry()
    engine = get_workflow_engine()
    
    definition = registry.lookup(req.workflow_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow not found.")
        
    context = WorkflowContext(
        workflow_id=req.workflow_id,
        execution_id=req.execution_id,
        correlation_id=req.correlation_id,
        session_id=req.session_id
    )
    
    try:
        outputs = await engine.execute(definition, context, req.inputs)
        return {
            "status": "success",
            "execution_id": req.execution_id,
            "outputs": outputs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_workflow(req: WorkflowActionRequest) -> Dict[str, Any]:
    """Pause an active workflow execution."""
    engine = get_workflow_engine()
    engine.pause(req.execution_id)
    return {"status": "paused", "execution_id": req.execution_id}


@router.post("/resume")
async def resume_workflow(req: WorkflowActionRequest) -> Dict[str, Any]:
    """Resume a paused workflow execution."""
    engine = get_workflow_engine()
    engine.resume(req.execution_id)
    return {"status": "resumed", "execution_id": req.execution_id}


@router.post("/cancel")
async def cancel_workflow(req: WorkflowActionRequest) -> Dict[str, Any]:
    """Cancel an active workflow execution."""
    engine = get_workflow_engine()
    engine.cancel(req.execution_id)
    return {"status": "cancelled", "execution_id": req.execution_id}
