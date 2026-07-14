"""
ASEP — AgentRunRepository
===========================
Async repository for the ``AgentRun`` ORM model.

Extends ``BaseRepository`` with domain-specific query methods scoped to the
``agent_runs`` table.  All methods leverage the indexes declared on the model
and never call ``session.commit()``, ``session.rollback()``, or
``session.begin()``.

Query hot-paths covered:
    - Queue poller: ``get_pending_oldest_first``
    - Supervisor heartbeat: ``get_running``
    - Dashboard listing: ``get_by_status``, ``list_recent``
    - Caller-session lookup: ``get_by_session_id``
    - Lifecycle transitions: ``update_status``
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from src.db.models.agent_run import AgentRun, RunStatus
from src.repositories.base import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    BaseRepository,
    _clamp_limit,
)


class AgentRunRepository(BaseRepository[AgentRun, uuid.UUID]):
    """Async repository for ``AgentRun`` persistence and domain queries.

    Inherits CRUD primitives from ``BaseRepository``.  Adds query methods
    that map directly to the indexes on ``agent_runs``:

    - ``ix_agent_run_session_id``
    - ``ix_agent_run_status``
    - ``ix_agent_run_created_at``
    - ``ix_agent_run_status_created_at``

    Attributes:
        _model: Bound to ``AgentRun``.

    Example::

        repo = AgentRunRepository(session)
        pending = await repo.get_pending_oldest_first(limit=10)
    """

    _model = AgentRun

    # ------------------------------------------------------------------
    # Lookup by session
    # ------------------------------------------------------------------

    async def get_by_session_id(
        self,
        session_id: str,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AgentRun]:
        """Return all runs associated with a caller session, newest first.

        Uses ``ix_agent_run_session_id``.

        Args:
            session_id: Opaque caller-session identifier.
            *options:   SQLAlchemy loader strategy options.
            limit:      Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:     Rows to skip.

        Returns:
            A list of ``AgentRun`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AgentRun)
            .where(AgentRun.session_id == session_id)
            .order_by(AgentRun.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Lookup by status
    # ------------------------------------------------------------------

    async def get_by_status(
        self,
        status: RunStatus,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AgentRun]:
        """Return all runs in a given lifecycle state, newest first.

        Uses ``ix_agent_run_status``.

        Args:
            status:   The ``RunStatus`` value to filter on.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``AgentRun`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AgentRun)
            .where(AgentRun.status == status)
            .order_by(AgentRun.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Queue poller — PENDING, oldest first
    # ------------------------------------------------------------------

    async def get_pending_oldest_first(
        self,
        limit: int = DEFAULT_LIMIT,
        *options: ExecutableOption,
    ) -> list[AgentRun]:
        """Return up to ``limit`` PENDING runs ordered oldest-first.

        This is the primary queue-poller query.  It hits the composite index
        ``ix_agent_run_status_created_at`` and avoids a full table scan.

        Args:
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            *options: SQLAlchemy loader strategy options.

        Returns:
            A list of ``AgentRun`` instances with status ``PENDING``,
            ordered by ``created_at ASC`` (oldest first).
        """
        stmt = (
            select(AgentRun)
            .where(AgentRun.status == RunStatus.PENDING)
            .order_by(AgentRun.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Supervisor heartbeat — RUNNING
    # ------------------------------------------------------------------

    async def get_running(
        self,
        *options: ExecutableOption,
    ) -> list[AgentRun]:
        """Return all runs currently in ``RUNNING`` state.

        Used by the Supervisor heartbeat to detect stalled runs.

        Args:
            *options: SQLAlchemy loader strategy options.

        Returns:
            A list of ``AgentRun`` instances with status ``RUNNING``,
            ordered by ``started_at ASC`` (longest-running first).
        """
        stmt = (
            select(AgentRun)
            .where(AgentRun.status == RunStatus.RUNNING)
            .order_by(AgentRun.started_at.asc())
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Status transition helper
    # ------------------------------------------------------------------

    async def update_status(
        self,
        run_id: uuid.UUID,
        status: RunStatus,
        **extra_fields: Any,
    ) -> AgentRun:
        """Transition an ``AgentRun`` to a new lifecycle state.

        Fetches the run by primary key, sets ``status``, and applies any
        additional field updates (e.g. ``started_at``, ``finished_at``,
        ``error_message``, ``final_output``).  Flushes after mutation.

        Args:
            run_id:        UUID of the target ``AgentRun``.
            status:        New ``RunStatus`` value.
            **extra_fields: Additional column updates applied atomically
                with the status change.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            NoResultFound: If no ``AgentRun`` with ``run_id`` exists.
        """
        run = await self.get_or_raise(run_id)
        return await self.update(run, status=status, **extra_fields)

    # ------------------------------------------------------------------
    # Recent listing (dashboard / pagination)
    # ------------------------------------------------------------------

    async def list_recent(
        self,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[AgentRun]:
        """Return the most recently created runs, newest first.

        Uses ``ix_agent_run_created_at`` for efficient time-ordered scans.

        Args:
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip (cursor-based pagination).

        Returns:
            A list of ``AgentRun`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(AgentRun)
            .order_by(AgentRun.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())
