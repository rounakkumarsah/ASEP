"""
ASEP — src/db/models package
=============================
Public re-exports for all SQLAlchemy ORM model classes and their
associated domain types.

Importing from this package guarantees that every model class has been
registered against ``Base.metadata`` before Alembic autogenerate or any
``Base.metadata.create_all`` call runs.

Usage::

    from src.db.models import AgentRun, RunStatus
    from src.db.models import Task, TaskStatus, TaskPriority
    from src.db.models import MemoryEntry, MemoryType
    from src.db.models import AuditLog, ActorType, AuditSeverity, AuditOutcome
    from src.db.models import KnowledgeDocument, DocumentSourceType, DocumentStatus, CrawlStatus
"""

from src.db.models.agent_run import AgentRun, RunStatus, TimestampMixin
from src.db.models.audit_log import ActorType, AuditLog, AuditOutcome, AuditSeverity
from src.db.models.knowledge_document import CrawlStatus, DocumentSourceType, DocumentStatus, KnowledgeDocument
from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.db.models.task import Task, TaskPriority, TaskStatus

__all__: list[str] = [
    # agent_run
    "AgentRun",
    "RunStatus",
    "TimestampMixin",
    # task
    "Task",
    "TaskStatus",
    "TaskPriority",
    # memory_entry
    "MemoryEntry",
    "MemoryType",
    # audit_log
    "AuditLog",
    "ActorType",
    "AuditSeverity",
    "AuditOutcome",
    # knowledge_document
    "KnowledgeDocument",
    "DocumentSourceType",
    "DocumentStatus",
    "CrawlStatus",
]
