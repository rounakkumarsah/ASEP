"""
Memory Router
"""

import uuid
from fastapi import APIRouter, Depends, status

from src.api.dependencies import MemoryServiceDep
from src.api.schemas import (
    MemoryEntryCreate,
    MemoryEntryResponse,
    PaginatedResponse,
    PaginationParams
)
from src.auth.decorators import RequirePermission
from src.auth.permissions import Permission


router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post("/", response_model=MemoryEntryResponse, status_code=status.HTTP_201_CREATED, dependencies=[RequirePermission(Permission.MEMORY_WRITE)])
async def create_memory(
    payload: MemoryEntryCreate,
    service: MemoryServiceDep,
) -> MemoryEntryResponse:
    """Create a new memory entry."""
    return await service.add_memory(
        agent_run_id=payload.agent_run_id,
        key=payload.key,
        value=payload.value,
        category=payload.category,
        task_id=payload.task_id
    )


@router.get("/", response_model=PaginatedResponse[MemoryEntryResponse], dependencies=[RequirePermission(Permission.MEMORY_READ)])
async def list_memory(
    agent_run_id: uuid.UUID,
    service: MemoryServiceDep,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[MemoryEntryResponse]:
    """List memory entries for a specific agent run."""
    # The service returns a list. In a real app we might want a paginated fetch from the DB.
    # For now, we will wrap the result.
    memories = await service.get_run_memory(
        agent_run_id=agent_run_id,
        # Our get_run_memory doesn't currently support limit/offset directly,
        # but we can pass them if we update the service in the future.
    )
    # manual pagination on memory list for now
    start = pagination.offset
    end = start + pagination.limit
    paginated = memories[start:end]
    
    return PaginatedResponse(
        items=paginated,
        total=len(memories),
        limit=pagination.limit,
        offset=pagination.offset
    )
