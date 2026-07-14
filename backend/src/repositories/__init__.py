"""
ASEP — Repository Layer
========================
Public surface of the Phase 0.4 Repository Layer.

All five domain repositories and the generic base class are re-exported
here for a clean, flat import surface::

    from src.repositories import AgentRunRepository, TaskRepository

Design context:
    - Repositories are persistence-only: CRUD + domain-specific queries.
    - No service logic, no Unit of Work, no transaction management.
    - Transaction boundaries are owned by the caller (future UoW layer).
    - Repositories never call ``session.commit()``, ``session.rollback()``,
      or ``session.begin()``.
    - ``AsyncSession`` is injected via each repository's constructor.
"""

from src.repositories.agent_run import AgentRunRepository
from src.repositories.audit_log import AuditLogRepository
from src.repositories.base import BaseRepository, DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from src.repositories.knowledge_document import KnowledgeDocumentRepository
from src.repositories.memory_entry import MemoryEntryRepository
from src.repositories.task import TaskRepository

__all__ = [
    # Base
    "BaseRepository",
    "DEFAULT_LIMIT",
    "DEFAULT_OFFSET",
    "MAX_LIMIT",
    # Domain repositories
    "AgentRunRepository",
    "TaskRepository",
    "MemoryEntryRepository",
    "AuditLogRepository",
    "KnowledgeDocumentRepository",
]
