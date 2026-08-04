"""
ASEP — src/db/models package
=============================
Public re-exports for all SQLAlchemy ORM model classes and their
associated domain types.

Importing from this package guarantees that every model class has been
registered against ``Base.metadata`` before Alembic autogenerate or any
``Base.metadata.create_all`` call runs.

Import ORDER matters for FK resolution:
  1. Organization (no FK deps within models)
  2. User (FK → organizations)
  3. Project (FK → organizations)
  4. Subscription (FK → organizations)
  5. ApiKey (FK → projects, users)
  6. Payment (FK → users)
  7. All agent/task/memory models
"""

# ── Multi-tenancy (import first — other models depend on these) ────────────
from src.db.models.organization import Organization
from src.db.models.user import User
from src.db.models.project import Project
from src.db.models.subscription import Subscription
from src.db.models.api_key import ApiKey

# ── Agent runtime ──────────────────────────────────────────────────────────
from src.db.models.agent_run import AgentRun, RunStatus, TimestampMixin
from src.db.models.audit_log import ActorType, AuditLog, AuditOutcome, AuditSeverity
from src.db.models.knowledge_document import CrawlStatus, DocumentSourceType, DocumentStatus, KnowledgeDocument
from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.db.models.payment import Payment
from src.db.models.task import Task, TaskPriority, TaskStatus

__all__: list[str] = [
    # multi-tenancy
    "Organization",
    "Project",
    "Subscription",
    "ApiKey",
    # user
    "User",
    # payment
    "Payment",
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
