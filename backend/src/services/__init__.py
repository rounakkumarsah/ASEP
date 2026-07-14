"""
ASEP — Service Layer
======================
Public surface of the Phase 0.6 Service Layer.

All five domain services and the ``InvalidStateError`` exception are
re-exported here for a flat, clean import surface::

    from src.services import AgentRunService, TaskService
    from src.services import MemoryService, AuditService, KnowledgeService
    from src.services import InvalidStateError, TaskDefinition

Architecture notes:
    - Services communicate only through ``AbstractUnitOfWork``.
    - Services never call other services.
    - Services return ORM entities only (no DTOs).
    - DTO mapping belongs to the future API Layer.
    - Business validation belongs exclusively in Services.
"""

from src.services.agent_run_service import AgentRunService
from src.services.audit_service import AuditService
from src.services.exceptions import InvalidStateError
from src.services.knowledge_service import KnowledgeService
from src.services.memory_service import MemoryService
from src.services.task_service import TaskDefinition, TaskService

__all__ = [
    # Exception
    "InvalidStateError",
    # Input carriers
    "TaskDefinition",
    # Domain services
    "AgentRunService",
    "TaskService",
    "MemoryService",
    "AuditService",
    "KnowledgeService",
]
