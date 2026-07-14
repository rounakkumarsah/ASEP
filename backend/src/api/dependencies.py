"""
ASEP — API Dependencies
=======================
FastAPI dependency injection providers.

This module is the ONLY place in the API layer that is allowed to
import `SQLAlchemyUnitOfWork`. Routers interact exclusively with the
Service Layer via these dependencies.
"""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends

from src.services.agent_run_service import AgentRunService
from src.services.audit_service import AuditService
from src.services.knowledge_service import KnowledgeService
from src.services.memory_service import MemoryService
from src.services.task_service import TaskService
from src.unit_of_work.base import AbstractUnitOfWork
from src.unit_of_work.sqlalchemy import SQLAlchemyUnitOfWork


def get_uow_factory() -> Callable[[], AbstractUnitOfWork]:
    """
    Dependency provider for the Unit of Work factory.
    This encapsulates the SQLAlchemy implementation, ensuring Services
    remain framework-agnostic.
    """
    return lambda: SQLAlchemyUnitOfWork()


# ---------------------------------------------------------------------------
# Service Dependencies
# ---------------------------------------------------------------------------

def get_agent_run_service(
    uow_factory: Annotated[Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)]
) -> AgentRunService:
    return AgentRunService(uow_factory)


def get_task_service(
    uow_factory: Annotated[Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)]
) -> TaskService:
    return TaskService(uow_factory)


def get_memory_service(
    uow_factory: Annotated[Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)]
) -> MemoryService:
    return MemoryService(uow_factory)


def get_audit_service(
    uow_factory: Annotated[Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)]
) -> AuditService:
    return AuditService(uow_factory)


def get_knowledge_service(
    uow_factory: Annotated[Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)]
) -> KnowledgeService:
    return KnowledgeService(uow_factory)


# ---------------------------------------------------------------------------
# Annotated Aliases for Routers
# ---------------------------------------------------------------------------

AgentRunServiceDep = Annotated[AgentRunService, Depends(get_agent_run_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
