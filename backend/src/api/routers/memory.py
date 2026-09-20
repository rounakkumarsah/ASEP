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
    PaginationParams,
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
    return await service.store_memory(
        content=payload.content,
        namespace="default",
        memory_type=payload.memory_type,
        importance_score=payload.importance_score,
        embedding_id=payload.embedding_id,
        embedding_model=payload.embedding_model,
        entry_metadata=payload.context_data,
    )


@router.get("/", response_model=PaginatedResponse[MemoryEntryResponse], dependencies=[RequirePermission(Permission.MEMORY_READ)])
async def list_memory(
    service: MemoryServiceDep,
    agent_run_id: uuid.UUID | None = None,
    type: str | None = None,
    query: str | None = None,
    namespace: str = "default",
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[MemoryEntryResponse]:
    """List memory entries."""
    from src.db.models.memory_entry import MemoryType

    if agent_run_id:
        memories = await service.get_run_memories(
            agent_run_id=agent_run_id,
            limit=pagination.limit,
        )
    elif type:
        try:
            mem_type = MemoryType(type)
            memories = await service.get_top_memories(
                namespace=namespace,
                memory_type=mem_type,
                limit=pagination.limit,
            )
        except ValueError:
            memories = []
    else:
        memories = await service.get_by_namespace(
            namespace=namespace,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    if query:
        memories = [m for m in memories if query.lower() in m.content.lower()]

    return PaginatedResponse(
        items=memories,
        total=len(memories),
        limit=pagination.limit,
        offset=pagination.offset
    )
