"""
ASEP — TaskRepository
=======================
Async repository for the ``Task`` ORM model.

Extends ``BaseRepository`` with domain-specific query methods scoped to the
``tasks`` table.  All methods leverage the indexes and unique constraint
declared on the model, and never call ``session.commit()``,
``session.rollback()``, or ``session.begin()``.

Query hot-paths covered:
    - Run decomposition: ``get_by_run``
    - Unique plan-slot lookup: ``get_by_run_and_position``
    - ExecutionEngine dispatcher: ``get_by_priority``, ``get_next_pending``
    - Dashboard: ``get_by_status``
    - Retry management: ``increment_retry``
    - Lifecycle transitions: ``update_status``
    - Run-level completion checks: ``count_by_run_and_status``
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from src.db.models.task import Task, TaskPriority, TaskStatus
from src.repositories.base import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    BaseRepository,
    _clamp_limit,
)


class TaskRepository(BaseRepository[Task, uuid.UUID]):
    """Async repository for ``Task`` persistence and domain queries.

    Inherits CRUD primitives from ``BaseRepository``.  Adds query methods
    that map directly to the indexes on ``tasks``:

    - ``ix_task_agent_run_id``
    - ``ix_task_agent_run_position``
    - ``ix_task_status``
    - ``ix_task_priority``
    - ``ix_task_status_priority``
    - ``uq_task_agent_run_position`` (unique lookup)

    Attributes:
        _model: Bound to ``Task``.

    Example::

        repo = TaskRepository(session)
        tasks = await repo.get_by_run(run_id)
    """

    _model = Task

    # ------------------------------------------------------------------
    # Lookup by parent run
    # ------------------------------------------------------------------

    async def get_by_run(
        self,
        agent_run_id: uuid.UUID,
        *options: ExecutableOption,
        order_by_position: bool = True,
    ) -> list[Task]:
        """Return all tasks belonging to a given ``AgentRun``.

        Uses ``ix_task_agent_run_id`` (or ``ix_task_agent_run_position``
        when ``order_by_position=True``).

        Args:
            agent_run_id:      UUID of the parent ``AgentRun``.
            *options:          SQLAlchemy loader strategy options.
            order_by_position: If ``True`` (default), order results by
                               ``position ASC``.  Pass ``False`` for
                               insertion-order retrieval.

        Returns:
            A list of ``Task`` instances belonging to the run.
        """
        stmt = select(Task).where(Task.agent_run_id == agent_run_id)
        if order_by_position:
            stmt = stmt.order_by(Task.position.asc())
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Unique plan-slot lookup
    # ------------------------------------------------------------------

    async def get_by_run_and_position(
        self,
        agent_run_id: uuid.UUID,
        position: int,
        *options: ExecutableOption,
    ) -> Task | None:
        """Return the task at a specific position within a run, or ``None``.

        The ``uq_task_agent_run_position`` unique constraint guarantees at
        most one result.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            position:     Zero-based plan position.
            *options:     SQLAlchemy loader strategy options.

        Returns:
            The ``Task`` instance, or ``None`` if the slot is empty.
        """
        stmt = (
            select(Task)
            .where(
                Task.agent_run_id == agent_run_id,
                Task.position == position,
            )
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalar(stmt)
        return result

    # ------------------------------------------------------------------
    # Lookup by status (dashboard)
    # ------------------------------------------------------------------

    async def get_by_status(
        self,
        status: TaskStatus,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
    ) -> list[Task]:
        """Return tasks in a given lifecycle state, newest first.

        Uses ``ix_task_status``.

        Args:
            status:   The ``TaskStatus`` value to filter on.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).
            offset:   Rows to skip.

        Returns:
            A list of ``Task`` instances ordered by ``created_at DESC``.
        """
        stmt = (
            select(Task)
            .where(Task.status == status)
            .order_by(Task.created_at.desc())
            .limit(_clamp_limit(limit))
            .offset(offset)
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Next PENDING task within a run
    # ------------------------------------------------------------------

    async def get_next_pending(
        self,
        agent_run_id: uuid.UUID,
        *options: ExecutableOption,
    ) -> Task | None:
        """Return the lowest-position PENDING task within a run.

        Used by the Supervisor to dispatch the next unit of work.
        Hits ``ix_task_agent_run_position`` to avoid a full-run scan.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            *options:     SQLAlchemy loader strategy options.

        Returns:
            The ``Task`` with the smallest ``position`` that is still
            ``PENDING``, or ``None`` if all tasks have left PENDING.
        """
        stmt = (
            select(Task)
            .where(
                Task.agent_run_id == agent_run_id,
                Task.status == TaskStatus.PENDING,
            )
            .order_by(Task.position.asc())
            .limit(1)
        )
        if options:
            stmt = stmt.options(*options)
        return await self._session.scalar(stmt)

    # ------------------------------------------------------------------
    # ExecutionEngine dispatcher — by priority
    # ------------------------------------------------------------------

    async def get_by_priority(
        self,
        priority: TaskPriority,
        *options: ExecutableOption,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Task]:
        """Return PENDING tasks at a given priority level, oldest first.

        Uses the composite index ``ix_task_status_priority`` so the
        ExecutionEngine can efficiently find the next work item without
        scanning the full ``tasks`` table.

        Args:
            priority: The ``TaskPriority`` value to filter on.
            *options: SQLAlchemy loader strategy options.
            limit:    Maximum rows to return (clamped to ``MAX_LIMIT``).

        Returns:
            A list of PENDING ``Task`` instances at the given priority,
            ordered by ``created_at ASC`` (oldest pending first).
        """
        stmt = (
            select(Task)
            .where(
                Task.status == TaskStatus.PENDING,
                Task.priority == priority,
            )
            .order_by(Task.created_at.asc())
            .limit(_clamp_limit(limit))
        )
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalars(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Retry management
    # ------------------------------------------------------------------

    async def increment_retry(self, task_id: uuid.UUID) -> Task:
        """Atomically increment ``retry_count`` on a task.

        Validates that ``retry_count < max_retries`` before incrementing.
        If the task is already at its retry ceiling, raises ``ValueError``
        so the caller can transition the task to ``FAILED`` permanently.

        Args:
            task_id: UUID of the ``Task`` to retry.

        Returns:
            The updated ``Task`` instance with ``retry_count`` incremented
            by one and ``status`` reset to ``PENDING``.

        Raises:
            NoResultFound: If no ``Task`` with ``task_id`` exists.
            ValueError:    If ``retry_count >= max_retries``.
        """
        task = await self.get_or_raise(task_id)
        if task.retry_count >= task.max_retries:
            raise ValueError(
                f"Task {task_id} has exhausted its retry budget "
                f"({task.retry_count}/{task.max_retries}).  "
                f"Transition the task to FAILED instead."
            )
        return await self.update(
            task,
            retry_count=task.retry_count + 1,
            status=TaskStatus.PENDING,
        )

    # ------------------------------------------------------------------
    # Status transition helper
    # ------------------------------------------------------------------

    async def update_status(
        self,
        task_id: uuid.UUID,
        status: TaskStatus,
        **extra_fields: Any,
    ) -> Task:
        """Transition a ``Task`` to a new lifecycle state.

        Fetches the task by primary key, sets ``status``, and applies any
        additional field updates (e.g. ``started_at``, ``finished_at``,
        ``result``, ``error_message``).  Flushes after mutation.

        Args:
            task_id:       UUID of the target ``Task``.
            status:        New ``TaskStatus`` value.
            **extra_fields: Additional column updates applied atomically
                with the status change.

        Returns:
            The updated ``Task`` instance.

        Raises:
            NoResultFound: If no ``Task`` with ``task_id`` exists.
        """
        task = await self.get_or_raise(task_id)
        return await self.update(task, status=status, **extra_fields)

    # ------------------------------------------------------------------
    # Run-level completion check
    # ------------------------------------------------------------------

    async def count_by_run_and_status(
        self,
        agent_run_id: uuid.UUID,
        status: TaskStatus,
    ) -> int:
        """Count tasks in a given state within a run.

        Useful for the Supervisor to determine whether all tasks have
        completed, or whether any have failed.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            status:       The ``TaskStatus`` value to count.

        Returns:
            int: Number of tasks matching ``(agent_run_id, status)``.
        """
        stmt = (
            select(func.count())
            .select_from(Task)
            .where(
                Task.agent_run_id == agent_run_id,
                Task.status == status,
            )
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)
