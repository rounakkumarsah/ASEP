"""
Tasks Router
"""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.api.dependencies import TaskServiceDep
from src.api.schemas import TaskResponse
from src.auth.decorators import RequirePermission
from src.auth.permissions import Permission


router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    task_metadata: dict[str, Any] | None = None
    tool_name: str | None = None


@router.get("/{task_id}", response_model=TaskResponse, dependencies=[RequirePermission(Permission.TASKS_READ)])
async def get_task(
    task_id: uuid.UUID,
    service: TaskServiceDep,
) -> TaskResponse:
    """Get a specific task by ID."""
    return await service.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse, dependencies=[RequirePermission(Permission.TASKS_UPDATE)])
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    service: TaskServiceDep,
) -> TaskResponse:
    """Update a task's mutable fields."""
    return await service.update_task(
        task_id,
        title=payload.title,
        description=payload.description,
        task_metadata=payload.task_metadata,
        tool_name=payload.tool_name
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[RequirePermission(Permission.TASKS_DELETE)])
async def delete_task(
    task_id: uuid.UUID,
    service: TaskServiceDep,
) -> None:
    """Delete a task."""
    await service.delete_task(task_id)


# ------------------------------------------------------------------
# State Transitions
# ------------------------------------------------------------------

@router.post("/{task_id}/start", response_model=TaskResponse, dependencies=[RequirePermission(Permission.TASKS_EXECUTE)])
async def start_task(
    task_id: uuid.UUID,
    service: TaskServiceDep,
) -> TaskResponse:
    """Mark a task as RUNNING."""
    return await service.start_task(task_id)


@router.post("/{task_id}/retry", response_model=TaskResponse, dependencies=[RequirePermission(Permission.TASKS_EXECUTE)])
async def retry_task(
    task_id: uuid.UUID,
    service: TaskServiceDep,
) -> TaskResponse:
    """Retry a FAILED task."""
    return await service.retry_task(task_id)


@router.post("/{task_id}/cancel", response_model=TaskResponse, dependencies=[RequirePermission(Permission.TASKS_EXECUTE)])
async def cancel_task(
    task_id: uuid.UUID,
    service: TaskServiceDep,
) -> TaskResponse:
    """Cancel a task."""
    return await service.cancel_task(task_id)
