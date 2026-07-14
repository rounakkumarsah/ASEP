"""
ASEP — SQLAlchemyUnitOfWork
=============================
Concrete SQLAlchemy 2.0 async implementation of ``AbstractUnitOfWork``.

This class is the production Unit of Work.  It opens a single
``AsyncSession`` per ``async with`` block, instantiates all five domain
repositories against that session, and manages the transaction lifecycle
exclusively.

Session lifecycle::

    __aenter__:
        session_factory()       → new AsyncSession (begins implicit transaction)
        <instantiate repos>     → all repos share the same session
        return self

    commit():
        session.commit()        → flush + commit; transaction ends successfully

    rollback():
        session.rollback()      → discard changes; transaction ends without save

    __aexit__(exc_type, ...):
        if exc_type:
            rollback()          → discard on any unhandled exception
        session.close()         → return connection to pool (always)

Design notes:
    - ``expire_on_commit=False`` on the session factory means ORM instances
      remain accessible after ``commit()`` without a reload round-trip.
      This is the correct setting for async usage where lazy-loading is
      unavailable.
    - The ``AsyncSession`` is strictly private (``_session``).  Callers
      interact with the database exclusively through the five repository
      attributes.
    - ``execute()``, ``flush()``, and ``close()`` are NOT exposed on this
      class.  They belong to the repository and session layers respectively.
    - The default ``session_factory`` is the application singleton from
      ``src.db.postgres``.  Tests override this by passing a custom factory
      (e.g. backed by an in-memory SQLite engine or a mock).
"""

from __future__ import annotations

import logging
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.postgres import _get_session_factory
from src.repositories.agent_run import AgentRunRepository
from src.repositories.audit_log import AuditLogRepository
from src.repositories.knowledge_document import KnowledgeDocumentRepository
from src.repositories.memory_entry import MemoryEntryRepository
from src.repositories.task import TaskRepository
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """Production Unit of Work backed by a SQLAlchemy ``AsyncSession``.

    One ``SQLAlchemyUnitOfWork`` instance represents exactly one database
    transaction.  All five repositories share the same session so their
    operations are atomically committed or rolled back together.

    Attributes:
        agent_runs:          ``AgentRunRepository`` bound to the active session.
        tasks:               ``TaskRepository`` bound to the active session.
        memory_entries:      ``MemoryEntryRepository`` bound to the active session.
        audit_logs:          ``AuditLogRepository`` bound to the active session.
        knowledge_documents: ``KnowledgeDocumentRepository`` bound to the active
                             session.

    Args:
        session_factory: An ``async_sessionmaker[AsyncSession]`` used to open
            the session in ``__aenter__``.  Defaults to the application's
            global session factory from ``src.db.postgres``.  Pass a custom
            factory in tests to inject a test-scoped session.

    Example::

        # Happy path — business logic commits explicitly
        async with SQLAlchemyUnitOfWork() as uow:
            run = AgentRun(goal="Summarise the Q4 report")
            await uow.agent_runs.create(run)
            await uow.commit()

        # Failure path — exception triggers automatic rollback
        async with SQLAlchemyUnitOfWork() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            await uow.agent_runs.update_status(run.id, RunStatus.RUNNING)
            raise RuntimeError("something went wrong")
            # rollback() is called automatically; session is closed

        # Read-only path — no commit needed
        async with SQLAlchemyUnitOfWork() as uow:
            runs = await uow.agent_runs.get_pending_oldest_first(limit=10)
        # session is closed; no commit was called (no writes occurred)
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        """Initialise with an optional custom session factory.

        Args:
            session_factory: ``async_sessionmaker[AsyncSession]``.  If
                ``None``, the application's global factory from
                ``src.db.postgres._get_session_factory()`` is used.
        """
        self._session_factory: async_sessionmaker[AsyncSession] = (
            session_factory if session_factory is not None else _get_session_factory()
        )
        # Session and repositories are None until __aenter__ is called.
        self._session: AsyncSession | None = None

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        """Open a new ``AsyncSession`` and bind all repositories to it.

        Returns:
            SQLAlchemyUnitOfWork: ``self``, allowing ``async with UoW() as uow:``.
        """
        self._session = self._session_factory()
        self.agent_runs = AgentRunRepository(self._session)
        self.tasks = TaskRepository(self._session)
        self.memory_entries = MemoryEntryRepository(self._session)
        self.audit_logs = AuditLogRepository(self._session)
        self.knowledge_documents = KnowledgeDocumentRepository(self._session)
        logger.debug("SQLAlchemyUnitOfWork session opened")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Roll back on exception, then always close the session.

        Contract:
            - If an unhandled exception propagated out of the ``async with``
              block, ``rollback()`` is called before closing.
            - The session is **always** closed, even if ``rollback()`` raises.
            - Clean exits are **never** auto-committed.  Callers must call
              ``await uow.commit()`` explicitly.

        Args:
            exc_type: Exception class, or ``None`` on clean exit.
            exc_val:  Exception instance, or ``None`` on clean exit.
            exc_tb:   Traceback, or ``None`` on clean exit.
        """
        if self._session is None:
            # __aenter__ was never called; nothing to close.
            return

        try:
            if exc_type is not None:
                logger.debug(
                    "SQLAlchemyUnitOfWork rolling back due to exception",
                    extra={"exc_type": exc_type.__name__},
                )
                await self.rollback()
        finally:
            await self._session.close()
            self._session = None
            logger.debug("SQLAlchemyUnitOfWork session closed")

    # ------------------------------------------------------------------
    # Transaction control
    # ------------------------------------------------------------------

    async def commit(self) -> None:
        """Flush all pending changes and commit the current transaction.

        Calling ``commit()`` ends the current transaction and makes all
        flushed changes durable.  The ``AsyncSession`` remains open after
        commit so the UoW can be reused within the same ``async with`` block
        if required (though this pattern is uncommon).

        Args:
            None

        Raises:
            RuntimeError: If called outside an active ``async with`` block
                (i.e. ``_session`` is ``None``).
            sqlalchemy.exc.SQLAlchemyError: On any DB-level commit failure.
                The caller should allow the exception to propagate so that
                ``__aexit__`` can roll back and close the session.
        """
        if self._session is None:
            raise RuntimeError(
                "SQLAlchemyUnitOfWork.commit() called outside an active "
                "'async with' block.  Use 'async with SQLAlchemyUnitOfWork() as uow:' "
                "before calling commit()."
            )
        await self._session.commit()
        logger.debug("SQLAlchemyUnitOfWork committed")

    async def rollback(self) -> None:
        """Discard all pending changes and roll back the current transaction.

        After rollback the session is reset to a clean state.  ORM instances
        that were staged since the last flush are expired if
        ``expire_on_commit`` is ``True`` (it is ``False`` here to support
        async usage without lazy-load errors).

        Args:
            None

        Raises:
            RuntimeError: If called outside an active ``async with`` block.
            sqlalchemy.exc.SQLAlchemyError: On any DB-level rollback failure.
        """
        if self._session is None:
            raise RuntimeError(
                "SQLAlchemyUnitOfWork.rollback() called outside an active "
                "'async with' block.  Use 'async with SQLAlchemyUnitOfWork() as uow:' "
                "before calling rollback()."
            )
        await self._session.rollback()
        logger.debug("SQLAlchemyUnitOfWork rolled back")
