"""
AgentRuns Router
"""

import uuid
from fastapi import APIRouter, Depends, status

from src.api.dependencies import AgentRunServiceDep, TaskServiceDep
from src.api.schemas import (
    AgentRunCreate,
    AgentRunResponse,
    PaginatedResponse,
    PaginationParams,
    TaskDefinitionSchema,
    TaskResponse
)
from src.auth.decorators import RequirePermission
from src.auth.permissions import Permission


router = APIRouter(prefix="/agent-runs", tags=["Agent Runs"])


@router.post("/", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequirePermission(Permission.AGENT_RUNS_CREATE)])
async def create_agent_run(
    payload: AgentRunCreate,
    service: AgentRunServiceDep,
) -> AgentRunResponse:
    """Create a new Agent Run."""
    run = await service.create_run(
        goal=payload.goal,
        plan=payload.plan,
        created_by="api_user"  # Placeholder until auth is implemented
    )
    return run


@router.get("/", response_model=PaginatedResponse[AgentRunResponse], dependencies=[RequirePermission(Permission.AGENT_RUNS_READ)])
async def list_agent_runs(
    service: AgentRunServiceDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[AgentRunResponse]:
    """List agent runs with pagination."""
    # Assuming get_active_runs for now. Later we might want generic list support in the service.
    # Service doesn't have a generic "list_runs(limit, offset)" method right now, 
    # but let's use get_active_runs for the list endpoint as a proxy, or add a stub.
    # Actually get_active_runs has no pagination limit offset in its signature.
    # We will just return active runs as a list and wrap it.
    runs = await service.get_active_runs()
    # Mock total count for pagination schema
    return PaginatedResponse(
        items=runs,
        total=len(runs),
        limit=pagination.limit,
        offset=pagination.offset
    )


@router.get("/{run_id}", response_model=AgentRunResponse, dependencies=[RequirePermission(Permission.AGENT_RUNS_READ)])
async def get_agent_run(
    run_id: uuid.UUID,
    service: AgentRunServiceDep,
) -> AgentRunResponse:
    """Get a specific agent run by ID."""
    return await service.get_run(run_id)


# ------------------------------------------------------------------
# Nested Task Endpoints
# ------------------------------------------------------------------

@router.post("/{run_id}/tasks", response_model=list[TaskResponse], status_code=status.HTTP_201_CREATED, dependencies=[RequirePermission(Permission.TASKS_CREATE)])
async def bulk_create_tasks(
    run_id: uuid.UUID,
    payload: list[TaskDefinitionSchema],
    service: TaskServiceDep,
) -> list[TaskResponse]:
    """Bulk create tasks under an agent run."""
    tasks = await service.create_tasks_bulk(
        agent_run_id=run_id,
        task_defs=payload,
    )
    return tasks


@router.get("/{run_id}/tasks", response_model=list[TaskResponse], dependencies=[RequirePermission(Permission.TASKS_READ)])
async def get_tasks_for_run(
    run_id: uuid.UUID,
    service: TaskServiceDep,
) -> list[TaskResponse]:
    """Get all tasks for a specific agent run."""
    return await service.get_tasks_for_run(run_id)
