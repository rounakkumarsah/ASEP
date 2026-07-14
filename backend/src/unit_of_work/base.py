"""
ASEP — AbstractUnitOfWork
==========================
Abstract base class defining the Unit of Work protocol for ASEP.

The Unit of Work (UoW) pattern coordinates a set of repositories that share
a single database transaction.  It owns the transaction boundary exclusively:

- ``commit()``   — flushes all pending changes and ends the transaction
                   successfully.
- ``rollback()`` — discards all pending changes and ends the transaction
                   without persisting anything.

Repositories **must never** call ``commit()``, ``rollback()``, ``flush()``,
``execute()``, or ``close()`` directly.  They only call ``session.add()``,
``session.get()``, ``session.scalars()``, and ``session.flush()`` to stage
and preview changes within the open transaction.

Usage pattern::

    async with SQLAlchemyUnitOfWork() as uow:
        run = AgentRun(goal="Write a report")
        await uow.agent_runs.create(run)
        await uow.commit()

    # Outside the block the session is always closed.

Design notes:
    - ``__aexit__`` rolls back automatically on any unhandled exception
      and never auto-commits on clean exit.  The caller must call
      ``await uow.commit()`` explicitly.
    - This ensures read-only UoW usages (no commit) are valid and that
      transaction intent is always visible in business-logic code.
    - All five domain repositories are exposed as typed attributes so
      callers get IDE autocompletion and type-checker coverage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.repositories.agent_run import AgentRunRepository
    from src.repositories.audit_log import AuditLogRepository
    from src.repositories.knowledge_document import KnowledgeDocumentRepository
    from src.repositories.memory_entry import MemoryEntryRepository
    from src.repositories.task import TaskRepository


class AbstractUnitOfWork(ABC):
    """Abstract Unit of Work defining the transaction-coordination protocol.

    Concrete implementations must:

    1. Open a database session in ``__aenter__``.
    2. Instantiate all five domain repositories, injecting the shared session.
    3. Implement ``commit()`` and ``rollback()`` to drive the session's
       transaction lifecycle.
    4. Close the session unconditionally in ``__aexit__``.

    The five repository attributes below are declared as abstract to force
    subclasses to populate them before returning ``self`` from ``__aenter__``.

    Attributes:
        agent_runs:          Repository for ``AgentRun`` entities.
        tasks:               Repository for ``Task`` entities.
        memory_entries:      Repository for ``MemoryEntry`` entities.
        audit_logs:          Repository for ``AuditLog`` entities (read + append).
        knowledge_documents: Repository for ``KnowledgeDocument`` entities.

    Example::

        class MyUoW(AbstractUnitOfWork):
            async def __aenter__(self): ...
            async def __aexit__(self, *args): ...
            async def commit(self): ...
            async def rollback(self): ...
    """

    # ------------------------------------------------------------------
    # Repository declarations — populated by concrete __aenter__
    # ------------------------------------------------------------------

    agent_runs: AgentRunRepository
    tasks: TaskRepository
    memory_entries: MemoryEntryRepository
    audit_logs: AuditLogRepository
    knowledge_documents: KnowledgeDocumentRepository

    # ------------------------------------------------------------------
    # Async context manager protocol
    # ------------------------------------------------------------------

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Open the database session and initialise all repositories.

        Returns:
            AbstractUnitOfWork: ``self``, so callers can use ``async with
                UoW() as uow:``.
        """

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the session, rolling back first if an exception occurred.

        Contract:
            - If ``exc_type`` is not ``None``: call ``rollback()`` before
              closing.
            - Never auto-commit on clean exit.
            - Always close the session, even if rollback raises.

        Args:
            exc_type: Exception class, or ``None`` on clean exit.
            exc_val:  Exception instance, or ``None`` on clean exit.
            exc_tb:   Traceback, or ``None`` on clean exit.
        """

    # ------------------------------------------------------------------
    # Transaction control — UoW exclusively owns these
    # ------------------------------------------------------------------

    @abstractmethod
    async def commit(self) -> None:
        """Flush all pending changes and commit the current transaction.

        After a successful commit, all flushed changes are permanently
        persisted.  The session remains open for further use within the
        same ``async with`` block (though this is uncommon).

        Raises:
            sqlalchemy.exc.SQLAlchemyError: On any DB-level commit failure.
        """

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all pending changes and roll back the current transaction.

        After rollback, the session is reset to a clean state.  Instances
        that were added or modified since the last flush are expired.

        Raises:
            sqlalchemy.exc.SQLAlchemyError: On any DB-level rollback failure.
        """
