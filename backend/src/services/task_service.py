"""
ASEP — TaskService
====================
Business logic for ``Task`` lifecycle management within an ``AgentRun``.

Responsibilities:
    - Validate inputs (title non-empty, position >= 0, no duplicate positions
      in bulk creation).
    - Enforce legal state transitions via ``InvalidStateError``.
    - Orchestrate repository operations through the Unit of Work.
    - Commit the transaction explicitly after every mutating operation.
    - Return ORM entities to the caller; DTO mapping belongs to the API layer.

Rules:
    - Never instantiates repositories directly.
    - Never creates or touches ``AsyncSession``.
    - Never calls other services.
    - All database access is via ``AbstractUnitOfWork``.

State machine::

    PENDING ──start──► RUNNING ──complete──► COMPLETED
       │                  │
       ├──skip────────────┤──fail──────────► FAILED
       │                  │
       └──cancel──────────┘──cancel────────► CANCELLED
    FAILED ──retry──────────────────────────► PENDING
"""

from __future__ import annotations

import dataclasses
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from src.db.models.task import Task, TaskPriority, TaskStatus
from src.services.exceptions import InvalidStateError
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)

# States from which each transition is permitted
_START_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.PENDING})
_COMPLETE_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.RUNNING})
_FAIL_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.RUNNING})
_SKIP_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.PENDING})
_CANCEL_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.PENDING, TaskStatus.RUNNING})
_RETRY_ALLOWED: frozenset[TaskStatus] = frozenset({TaskStatus.FAILED})


# ---------------------------------------------------------------------------
# TaskDefinition — input structure for bulk creation
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Immutable descriptor for a single task in a bulk-creation call.

    Used exclusively by ``TaskService.create_tasks_bulk``.  Not an ORM
    entity; not a DTO.  It is a validated input carrier internal to the
    service layer.

    Attributes:
        position:      Zero-based plan position.  Must be >= 0 and unique
                       within the batch.
        title:         Human-readable task description.  Must be non-empty.
        priority:      Dispatch priority.  Defaults to ``TaskPriority.NORMAL``.
        description:   Optional extended task description.
        tool_name:     Optional tool or agent name responsible for this task.
        task_metadata: Optional JSONB context for the executing agent.
    """

    position: int
    title: str
    priority: TaskPriority = TaskPriority.NORMAL
    description: str | None = None
    tool_name: str | None = None
    task_metadata: dict[str, Any] | None = None


class TaskService:
    """Service owning the business logic for ``Task`` lifecycle management.

    Each public method opens its own ``async with uow`` block, executes one
    atomic business operation, and commits explicitly.  Read-only methods open
    a UoW block but do not call ``commit()``.

    Args:
        uow_factory: A zero-argument callable returning a fresh
            ``AbstractUnitOfWork``.

    Example::

        service = TaskService(SQLAlchemyUnitOfWork)
        task = await service.create_task(
            agent_run_id=run.id,
            position=0,
            title="Fetch the Q4 data",
        )
        task = await service.start_task(task.id)
    """

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        """Initialise with a Unit of Work factory.

        Args:
            uow_factory: Zero-argument callable returning an
                ``AbstractUnitOfWork``.
        """
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _guard_transition(
        self,
        task: Task,
        allowed: frozenset[TaskStatus],
        transition: str,
    ) -> None:
        """Raise ``InvalidStateError`` if ``task.status`` is not in ``allowed``.

        Args:
            task:       The ``Task`` instance being transitioned.
            allowed:    Set of statuses from which the transition is legal.
            transition: Human-readable name of the transition.

        Raises:
            InvalidStateError: If ``task.status not in allowed``.
        """
        if task.status not in allowed:
            raise InvalidStateError(
                entity_type="Task",
                entity_id=task.id,
                current_status=task.status.value,
                attempted_transition=transition,
            )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_task(
        self,
        agent_run_id: uuid.UUID,
        position: int,
        title: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        description: str | None = None,
        tool_name: str | None = None,
        task_metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a single ``Task`` in ``PENDING`` state.

        Args:
            agent_run_id:  UUID of the parent ``AgentRun``.
            position:      Zero-based plan position.  Must be >= 0.
            title:         Human-readable task description.  Must be non-empty.
            priority:      Dispatch priority (default ``NORMAL``).
            description:   Optional extended description.
            tool_name:     Optional tool or agent name.
            task_metadata: Optional JSONB context for the executing agent.

        Returns:
            The persisted ``Task`` instance.

        Raises:
            ValueError: If ``title`` is empty or ``position`` is negative.
        """
        title = title.strip()
        if not title:
            raise ValueError("Task.title must be a non-empty string.")
        if position < 0:
            raise ValueError(f"Task.position must be >= 0, got {position}.")

        task = Task(
            id=uuid.uuid4(),
            agent_run_id=agent_run_id,
            position=position,
            title=title,
            status=TaskStatus.PENDING,
            priority=priority,
            description=description,
            tool_name=tool_name,
            task_metadata=task_metadata,
        )
        async with self._uow_factory() as uow:
            task = await uow.tasks.create(task)
            await uow.commit()

        logger.info(
            "Task created",
            extra={
                "task_id": str(task.id),
                "run_id": str(agent_run_id),
                "position": position,
            },
        )
        return task

    async def create_tasks_bulk(
        self,
        agent_run_id: uuid.UUID,
        task_defs: list[TaskDefinition],
    ) -> list[Task]:
        """Create multiple tasks for a run in a single atomic transaction.

        All validation runs **before** any database operation (fail-fast):
        - Each ``TaskDefinition.title`` must be non-empty.
        - Each ``TaskDefinition.position`` must be >= 0.
        - No two definitions may share the same ``position``.

        All tasks are inserted within a single ``async with uow`` block so
        they are committed atomically.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            task_defs:    List of ``TaskDefinition`` descriptors.  Must be
                          non-empty.

        Returns:
            A list of persisted ``Task`` instances in the same order as
            ``task_defs``.

        Raises:
            ValueError: If ``task_defs`` is empty, any title is blank, any
                position is negative, or any two positions are duplicated.
        """
        if not task_defs:
            raise ValueError("task_defs must be a non-empty list.")

        # --- Fail-fast validation BEFORE any DB operation ---
        seen_positions: set[int] = set()
        for idx, td in enumerate(task_defs):
            title = td.title.strip()
            if not title:
                raise ValueError(
                    f"task_defs[{idx}].title must be a non-empty string."
                )
            if td.position < 0:
                raise ValueError(
                    f"task_defs[{idx}].position must be >= 0, got {td.position}."
                )
            if td.position in seen_positions:
                raise ValueError(
                    f"task_defs contains duplicate position {td.position} "
                    f"at index {idx}."
                )
            seen_positions.add(td.position)

        tasks: list[Task] = []
        async with self._uow_factory() as uow:
            for td in task_defs:
                task = Task(
                    id=uuid.uuid4(),
                    agent_run_id=agent_run_id,
                    position=td.position,
                    title=td.title.strip(),
                    status=TaskStatus.PENDING,
                    priority=td.priority,
                    description=td.description,
                    tool_name=td.tool_name,
                    task_metadata=td.task_metadata,
                )
                task = await uow.tasks.create(task)
                tasks.append(task)
            await uow.commit()

        logger.info(
            "Tasks bulk-created",
            extra={"run_id": str(agent_run_id), "count": len(tasks)},
        )
        return tasks

    # ------------------------------------------------------------------
    # State transitions — mutating
    # ------------------------------------------------------------------

    async def start_task(self, task_id: uuid.UUID) -> Task:
        """Transition a ``PENDING`` task to ``RUNNING``.

        Sets ``started_at`` to the current UTC time.

        Args:
            task_id: UUID of the target ``Task``.

        Returns:
            The updated ``Task`` instance.

        Raises:
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``PENDING`` state.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _START_ALLOWED, "start")
            task = await uow.tasks.update(
                task,
                status=TaskStatus.RUNNING,
                started_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.info("Task started", extra={"task_id": str(task_id)})
        return task

    async def complete_task(
        self,
        task_id: uuid.UUID,
        result: str | None = None,
    ) -> Task:
        """Transition a ``RUNNING`` task to ``COMPLETED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            task_id: UUID of the target ``Task``.
            result:  Optional result payload / summary.

        Returns:
            The updated ``Task`` instance.

        Raises:
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``RUNNING`` state.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _COMPLETE_ALLOWED, "complete")
            task = await uow.tasks.update(
                task,
                status=TaskStatus.COMPLETED,
                finished_at=datetime.now(tz=timezone.utc),
                result=result,
            )
            await uow.commit()

        logger.info("Task completed", extra={"task_id": str(task_id)})
        return task

    async def fail_task(
        self,
        task_id: uuid.UUID,
        error_message: str,
    ) -> Task:
        """Transition a ``RUNNING`` task to ``FAILED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            task_id:       UUID of the target ``Task``.
            error_message: Human-readable description of the failure.
                           Must be non-empty.

        Returns:
            The updated ``Task`` instance.

        Raises:
            ValueError:       If ``error_message`` is empty.
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``RUNNING`` state.
        """
        error_message = error_message.strip()
        if not error_message:
            raise ValueError("error_message must be a non-empty string.")

        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _FAIL_ALLOWED, "fail")
            task = await uow.tasks.update(
                task,
                status=TaskStatus.FAILED,
                finished_at=datetime.now(tz=timezone.utc),
                error_message=error_message,
            )
            await uow.commit()

        logger.warning("Task failed", extra={"task_id": str(task_id)})
        return task

    async def skip_task(self, task_id: uuid.UUID) -> Task:
        """Transition a ``PENDING`` task to ``SKIPPED``.

        Used when the Supervisor determines a subtask is no longer required.
        Sets ``finished_at`` to the current UTC time.

        Args:
            task_id: UUID of the target ``Task``.

        Returns:
            The updated ``Task`` instance.

        Raises:
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``PENDING`` state.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _SKIP_ALLOWED, "skip")
            task = await uow.tasks.update(
                task,
                status=TaskStatus.SKIPPED,
                finished_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.info("Task skipped", extra={"task_id": str(task_id)})
        return task

    async def cancel_task(self, task_id: uuid.UUID) -> Task:
        """Transition a ``PENDING`` or ``RUNNING`` task to ``CANCELLED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            task_id: UUID of the target ``Task``.

        Returns:
            The updated ``Task`` instance.

        Raises:
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``PENDING`` or ``RUNNING``.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _CANCEL_ALLOWED, "cancel")
            task = await uow.tasks.update(
                task,
                status=TaskStatus.CANCELLED,
                finished_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.info("Task cancelled", extra={"task_id": str(task_id)})
        return task

    async def retry_task(self, task_id: uuid.UUID) -> Task:
        """Retry a ``FAILED`` task by incrementing ``retry_count``.

        Delegates to ``TaskRepository.increment_retry()`` which enforces
        that ``retry_count < max_retries`` before incrementing and resets
        ``status`` to ``PENDING``.

        Args:
            task_id: UUID of the target ``Task``.

        Returns:
            The updated ``Task`` instance with ``status=PENDING`` and
            ``retry_count`` incremented by one.

        Raises:
            NoResultFound:    If no task with ``task_id`` exists.
            InvalidStateError: If the task is not in ``FAILED`` state.
            ValueError:       If ``retry_count >= max_retries``.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            self._guard_transition(task, _RETRY_ALLOWED, "retry")
            task = await uow.tasks.increment_retry(task_id)
            await uow.commit()

        logger.info(
            "Task queued for retry",
            extra={"task_id": str(task_id), "retry_count": task.retry_count},
        )
        return task

    # ------------------------------------------------------------------
    # Read-only queries
    # ------------------------------------------------------------------

    async def get_task(self, task_id: uuid.UUID) -> Task:
        """Return a single Task by ID.

        Args:
            task_id: UUID of the target Task.

        Returns:
            The Task instance.

        Raises:
            NoResultFound: If no task with task_id exists.
        """
        async with self._uow_factory() as uow:
            return await uow.tasks.get_or_raise(task_id)

    async def update_task(
        self,
        task_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        task_metadata: dict[str, Any] | None = None,
        tool_name: str | None = None,
    ) -> Task:
        """Update mutable fields of a Task.

        Args:
            task_id: UUID of the target Task.
            title: Optional new title.
            description: Optional new description.
            task_metadata: Optional new metadata.
            tool_name: Optional new tool_name.

        Returns:
            The updated Task instance.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            kwargs = {}
            if title is not None:
                kwargs["title"] = title.strip()
            if description is not None:
                kwargs["description"] = description
            if task_metadata is not None:
                kwargs["task_metadata"] = task_metadata
            if tool_name is not None:
                kwargs["tool_name"] = tool_name
                
            if kwargs:
                task = await uow.tasks.update(task, **kwargs)
                await uow.commit()
            return task

    async def delete_task(self, task_id: uuid.UUID) -> None:
        """Delete a single Task.

        Args:
            task_id: UUID of the target Task.
        """
        async with self._uow_factory() as uow:
            task = await uow.tasks.get_or_raise(task_id)
            await uow.tasks.delete(task)
            await uow.commit()

    async def get_next_task(self, agent_run_id: uuid.UUID) -> Task | None:
        """Return the next ``PENDING`` task in a run, or ``None``.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.

        Returns:
            The lowest-position PENDING ``Task``, or ``None`` if none exist.
        """
        async with self._uow_factory() as uow:
            return await uow.tasks.get_next_pending(agent_run_id)

    async def get_tasks_for_run(self, agent_run_id: uuid.UUID) -> list[Task]:
        """Return all tasks belonging to a run, ordered by position.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.

        Returns:
            A list of ``Task`` instances ordered by ``position ASC``.
        """
        async with self._uow_factory() as uow:
            return await uow.tasks.get_by_run(agent_run_id, order_by_position=True)

    async def count_by_status(
        self,
        agent_run_id: uuid.UUID,
        status: TaskStatus,
    ) -> int:
        """Count tasks in a given state within a run.

        Args:
            agent_run_id: UUID of the parent ``AgentRun``.
            status:       The ``TaskStatus`` value to count.

        Returns:
            int: Number of tasks in the given state.
        """
        async with self._uow_factory() as uow:
            return await uow.tasks.count_by_run_and_status(agent_run_id, status)
