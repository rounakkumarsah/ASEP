"""
ASEP — AgentRunService
========================
Business logic for the full ``AgentRun`` lifecycle.

Responsibilities:
    - Validate inputs (goal non-empty, plan is a non-empty list of strings).
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
                  │                │
                  │           fail─┤──────► FAILED
                  │                │
                  │        timeout─┤──────► TIMED_OUT
                  │                │
                  └───cancel───────┘──────► CANCELLED
    PENDING ──cancel──────────────────────► CANCELLED
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from src.db.models.agent_run import AgentRun, RunStatus
from src.services.exceptions import InvalidStateError
from src.unit_of_work.base import AbstractUnitOfWork

logger = logging.getLogger(__name__)

# States from which each transition is permitted
_START_ALLOWED: frozenset[RunStatus] = frozenset({RunStatus.PENDING})
_COMPLETE_ALLOWED: frozenset[RunStatus] = frozenset({RunStatus.RUNNING})
_FAIL_ALLOWED: frozenset[RunStatus] = frozenset({RunStatus.RUNNING})
_CANCEL_ALLOWED: frozenset[RunStatus] = frozenset({RunStatus.PENDING, RunStatus.RUNNING})
_TIMEOUT_ALLOWED: frozenset[RunStatus] = frozenset({RunStatus.RUNNING})


class AgentRunService:
    """Service owning the business logic for ``AgentRun`` lifecycle management.

    Each public method opens its own ``async with uow`` block, executes one
    atomic business operation, and commits explicitly.  Read-only methods open
    a UoW block for the session but do not call ``commit()``.

    Args:
        uow_factory: A zero-argument callable that returns a fresh
            ``AbstractUnitOfWork`` instance.  Typically
            ``SQLAlchemyUnitOfWork`` for production or a test double.

    Example::

        service = AgentRunService(SQLAlchemyUnitOfWork)
        run = await service.create_run(goal="Analyse the Q4 report")
        run = await service.start_run(run.id)
    """

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        """Initialise with a Unit of Work factory.

        Args:
            uow_factory: Zero-argument callable returning an
                ``AbstractUnitOfWork``.  Called once per service method
                invocation.
        """
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _guard_transition(
        self,
        run: AgentRun,
        allowed: frozenset[RunStatus],
        transition: str,
    ) -> None:
        """Raise ``InvalidStateError`` if ``run.status`` is not in ``allowed``.

        Args:
            run:        The ``AgentRun`` instance being transitioned.
            allowed:    Set of statuses from which the transition is legal.
            transition: Human-readable name of the transition (e.g. ``"start"``).

        Raises:
            InvalidStateError: If ``run.status not in allowed``.
        """
        if run.status not in allowed:
            raise InvalidStateError(
                entity_type="AgentRun",
                entity_id=run.id,
                current_status=run.status.value,
                attempted_transition=transition,
            )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_run(
        self,
        goal: str,
        session_id: str | None = None,
        model_name: str | None = None,
    ) -> AgentRun:
        """Create a new ``AgentRun`` in ``PENDING`` state.

        Args:
            goal:       Plain-text description of the run's objective.
                        Must be a non-empty string.
            session_id: Optional opaque caller-session identifier.
            model_name: Optional name of the LLM model to use for this run.

        Returns:
            The persisted ``AgentRun`` instance.

        Raises:
            ValueError: If ``goal`` is empty or whitespace-only.
        """
        goal = goal.strip()
        if not goal:
            raise ValueError("AgentRun.goal must be a non-empty string.")

        run = AgentRun(
            id=uuid.uuid4(),
            goal=goal,
            status=RunStatus.PENDING,
            session_id=session_id,
            model_name=model_name,
        )
        async with self._uow_factory() as uow:
            run = await uow.agent_runs.create(run)
            await uow.commit()

        logger.info(
            "AgentRun created",
            extra={"run_id": str(run.id), "goal_preview": goal[:80]},
        )
        return run

    # ------------------------------------------------------------------
    # State transitions — mutating
    # ------------------------------------------------------------------

    async def start_run(self, run_id: uuid.UUID) -> AgentRun:
        """Transition a ``PENDING`` run to ``RUNNING``.

        Sets ``started_at`` to the current UTC time.

        Args:
            run_id: UUID of the target ``AgentRun``.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            NoResultFound:    If no run with ``run_id`` exists.
            InvalidStateError: If the run is not in ``PENDING`` state.
        """
        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            self._guard_transition(run, _START_ALLOWED, "start")
            run = await uow.agent_runs.update(
                run,
                status=RunStatus.RUNNING,
                started_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.info("AgentRun started", extra={"run_id": str(run_id)})
        return run

    async def complete_run(
        self,
        run_id: uuid.UUID,
        final_output: str | None = None,
    ) -> AgentRun:
        """Transition a ``RUNNING`` run to ``COMPLETED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            run_id:       UUID of the target ``AgentRun``.
            final_output: Optional summary or result payload of the run.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            NoResultFound:    If no run with ``run_id`` exists.
            InvalidStateError: If the run is not in ``RUNNING`` state.
        """
        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            self._guard_transition(run, _COMPLETE_ALLOWED, "complete")
            run = await uow.agent_runs.update(
                run,
                status=RunStatus.COMPLETED,
                finished_at=datetime.now(tz=timezone.utc),
                final_output=final_output,
            )
            await uow.commit()

        logger.info("AgentRun completed", extra={"run_id": str(run_id)})
        return run

    async def fail_run(
        self,
        run_id: uuid.UUID,
        error_message: str,
    ) -> AgentRun:
        """Transition a ``RUNNING`` run to ``FAILED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            run_id:        UUID of the target ``AgentRun``.
            error_message: Human-readable description of the failure.
                           Must be a non-empty string.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            ValueError:       If ``error_message`` is empty.
            NoResultFound:    If no run with ``run_id`` exists.
            InvalidStateError: If the run is not in ``RUNNING`` state.
        """
        error_message = error_message.strip()
        if not error_message:
            raise ValueError("error_message must be a non-empty string.")

        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            self._guard_transition(run, _FAIL_ALLOWED, "fail")
            run = await uow.agent_runs.update(
                run,
                status=RunStatus.FAILED,
                finished_at=datetime.now(tz=timezone.utc),
                error_message=error_message,
            )
            await uow.commit()

        logger.warning("AgentRun failed", extra={"run_id": str(run_id)})
        return run

    async def cancel_run(self, run_id: uuid.UUID) -> AgentRun:
        """Transition a ``PENDING`` or ``RUNNING`` run to ``CANCELLED``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            run_id: UUID of the target ``AgentRun``.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            NoResultFound:    If no run with ``run_id`` exists.
            InvalidStateError: If the run is not in ``PENDING`` or ``RUNNING``.
        """
        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            self._guard_transition(run, _CANCEL_ALLOWED, "cancel")
            run = await uow.agent_runs.update(
                run,
                status=RunStatus.CANCELLED,
                finished_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.info("AgentRun cancelled", extra={"run_id": str(run_id)})
        return run

    async def timeout_run(self, run_id: uuid.UUID) -> AgentRun:
        """Transition a ``RUNNING`` run to ``TIMED_OUT``.

        Sets ``finished_at`` to the current UTC time.

        Args:
            run_id: UUID of the target ``AgentRun``.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            NoResultFound:    If no run with ``run_id`` exists.
            InvalidStateError: If the run is not in ``RUNNING`` state.
        """
        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            self._guard_transition(run, _TIMEOUT_ALLOWED, "timeout")
            run = await uow.agent_runs.update(
                run,
                status=RunStatus.TIMED_OUT,
                finished_at=datetime.now(tz=timezone.utc),
            )
            await uow.commit()

        logger.warning("AgentRun timed out", extra={"run_id": str(run_id)})
        return run

    async def set_plan(
        self,
        run_id: uuid.UUID,
        plan: list[str],
    ) -> AgentRun:
        """Attach a decomposed plan (list of step descriptions) to a run.

        The plan can be set at any point in the run's lifecycle and does not
        trigger a status transition.

        Args:
            run_id: UUID of the target ``AgentRun``.
            plan:   Non-empty list of non-empty step-description strings.

        Returns:
            The updated ``AgentRun`` instance.

        Raises:
            ValueError:    If ``plan`` is empty or any element is blank.
            NoResultFound: If no run with ``run_id`` exists.
        """
        if not plan:
            raise ValueError("plan must be a non-empty list of step descriptions.")
        cleaned = [step.strip() for step in plan]
        empty_steps = [i for i, s in enumerate(cleaned) if not s]
        if empty_steps:
            raise ValueError(
                f"plan contains empty step(s) at index(es): {empty_steps}."
            )

        async with self._uow_factory() as uow:
            run = await uow.agent_runs.get_or_raise(run_id)
            run = await uow.agent_runs.update(run, plan=cleaned)
            await uow.commit()

        logger.info(
            "AgentRun plan set",
            extra={"run_id": str(run_id), "step_count": len(cleaned)},
        )
        return run

    # ------------------------------------------------------------------
    # Read-only queries
    # ------------------------------------------------------------------

    async def get_run(self, run_id: uuid.UUID) -> AgentRun:
        """Return a single ``AgentRun`` by primary key.

        Args:
            run_id: UUID of the target ``AgentRun``.

        Returns:
            The ``AgentRun`` instance.

        Raises:
            NoResultFound: If no run with ``run_id`` exists.
        """
        async with self._uow_factory() as uow:
            return await uow.agent_runs.get_or_raise(run_id)

    async def list_pending(self, limit: int = 50) -> list[AgentRun]:
        """Return up to ``limit`` PENDING runs, oldest first.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            A list of ``AgentRun`` instances.
        """
        async with self._uow_factory() as uow:
            return await uow.agent_runs.get_pending_oldest_first(limit=limit)

    async def list_running(self) -> list[AgentRun]:
        """Return all currently ``RUNNING`` runs.

        Returns:
            A list of ``AgentRun`` instances ordered by ``started_at ASC``.
        """
        async with self._uow_factory() as uow:
            return await uow.agent_runs.get_running()

    async def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentRun]:
        """Return the most recently created runs.

        Args:
            limit:  Maximum number of runs to return.
            offset: Number of runs to skip.

        Returns:
            A list of ``AgentRun`` instances ordered by ``created_at DESC``.
        """
        async with self._uow_factory() as uow:
            return await uow.agent_runs.list_recent(limit=limit, offset=offset)
