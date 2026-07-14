"""
Audit Router
"""

from typing import Annotated
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import AuditServiceDep
from src.api.schemas import (
    AuditLogResponse,
    PaginatedResponse,
    PaginationParams
)
from src.auth.decorators import RequirePermission
from src.auth.permissions import Permission
from src.db.models.audit_log import ActorType


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=PaginatedResponse[AuditLogResponse], dependencies=[RequirePermission(Permission.AUDIT_READ)])
async def list_audit_logs(
    service: AuditServiceDep,
    actor_type: ActorType | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[AuditLogResponse]:
    """List audit logs with filtering."""
    if actor_type and actor_id:
        logs = await service.get_actor_history(
            actor_type=actor_type,
            actor_id=actor_id,
            limit=pagination.limit,
            offset=pagination.offset
        )
    elif resource_type:
        logs = await service.get_resource_history(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=pagination.limit,
            offset=pagination.offset
        )
    else:
        # Default empty return or generic query if not implemented in service yet.
        # Audit service currently only exposes actor and resource history, not global history.
        logs = []
        
    return PaginatedResponse(
        items=logs,
        total=len(logs),  # Mock total as count is not implemented for all filters
        limit=pagination.limit,
        offset=pagination.offset
    )


@router.get("/critical", response_model=PaginatedResponse[AuditLogResponse], dependencies=[RequirePermission(Permission.AUDIT_READ)])
async def list_critical_failures(
    service: AuditServiceDep,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(50, ge=1, le=1000),
) -> PaginatedResponse[AuditLogResponse]:
    """List critical severity failures within a timeframe."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)
    logs = await service.get_critical_failures(since=since, limit=limit)
    
    return PaginatedResponse(
        items=logs,
        total=len(logs),
        limit=limit,
        offset=0
    )
