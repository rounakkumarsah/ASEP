"""
ASEP — Task ORM Model
======================
Defines the ``Task`` SQLAlchemy 2.0 mapped class, which represents a single
atomic unit of work within an ``AgentRun``.

An ``AgentRun`` decomposes its goal into an ordered list of subtasks (the
plan).  Each element in that list is persisted as a ``Task`` row, giving the
platform fine-grained observability over execution progress, retries, and
per-step telemetry.

Design notes:
    - Uses SQLAlchemy 2.0 ``Mapped`` / ``mapped_column`` API throughout;
      the legacy ``Column`` API is intentionally absent.
    - ``TaskStatus`` and ``TaskPriority`` are stored as native Postgres
      ``ENUM`` types — DB-level constraint enforcement, not just application-
      level validation.
    - The JSONB ``metadata`` column is mapped to the Python attribute
      ``task_metadata`` to avoid shadowing SQLAlchemy's reserved
      ``DeclarativeBase.metadata`` attribute.
    - ``task_metadata`` is aliased to the Postgres column ``metadata`` via
      ``mapped_column("metadata", ...)``, keeping the DB schema clean.
    - ``position`` provides a stable, zero-based ordinal that mirrors the
      task's index in ``AgentRun.plan``.  A ``UNIQUE (agent_run_id, position)``
      constraint guarantees no two tasks occupy the same plan slot within a
      single run.
    - The relationship to ``AgentRun`` is declared **unidirectionally** on the
      ``Task`` (many) side only.  The reciprocal ``AgentRun.tasks`` attribute
      will be wired in a dedicated ``agent_run.py`` update to keep each change
      set atomic and reviewable.
    - ``lazy="selectin"`` is used on the relationship so that ``AsyncSession``
      callers receive a populated ``agent_run`` attribute without triggering
      a ``MissingGreenlet`` error from implicit lazy-loading in async context.
    - All timestamps are timezone-aware (``TIMESTAMPTZ``).  Server-side
      defaults via ``func.now()`` govern them — not Python-side
      ``datetime.utcnow()`` (deprecated in Python 3.12).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.models.agent_run import AgentRun, TimestampMixin
from src.db.postgres import Base


# ---------------------------------------------------------------------------
# TaskStatus
# ---------------------------------------------------------------------------


class TaskStatus(str, enum.Enum):
    """Lifecycle states of a single ``Task``.

    Inheriting from ``str`` means every member is simultaneously a plain
    Python string and an enum member, which simplifies JSON serialisation
    and direct string comparison without requiring ``.value`` access.

    ``TaskStatus`` is intentionally independent of ``RunStatus``.  In
    particular, ``SKIPPED`` has no equivalent at the run level — it models
    the Supervisor's deliberate decision to bypass a subtask (e.g. the
    subtask became redundant after a prior step succeeded with broader
    output).

    State machine::

        PENDING ──► RUNNING ──► COMPLETED
                        │
                        ├──► FAILED
                        ├──► SKIPPED
                        └──► CANCELLED

    Attributes:
        PENDING: Queued within its parent run; waiting for an executor slot.
        RUNNING: Actively executing inside a worker agent.
        COMPLETED: Finished successfully; ``result`` is populated.
        FAILED: Terminated with an unrecoverable error; ``error_message``
            is populated.  May be retried if ``retry_count < max_retries``.
        SKIPPED: Deliberately bypassed by the Supervisor; ``result`` and
            ``error_message`` remain ``None``.
        CANCELLED: Stopped explicitly by the user or the governance policy
            engine before reaching a terminal outcome.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# TaskPriority
# ---------------------------------------------------------------------------


class TaskPriority(str, enum.Enum):
    """Priority weights for ``Task`` queue ordering within an ``AgentRun``.

    Inheriting from ``str`` follows the same pattern as ``TaskStatus`` and
    ``RunStatus``: members are usable directly as strings in serialisation
    and comparison contexts.

    The numeric ordering interpretation (which priority level pre-empts
    which) is the responsibility of the ``ExecutionEngine``; this model
    stores the label only.

    Attributes:
        LOW: Background / best-effort.  Processed only when no higher-
            priority work is available.
        NORMAL: Default priority for all tasks unless explicitly overridden
            by the Planner or Supervisor.
        HIGH: Elevated.  Dispatched ahead of ``NORMAL`` tasks.
        CRITICAL: Highest priority.  Pre-empts all other tasks; used for
            time-sensitive corrections or governance-triggered interventions.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class Task(TimestampMixin, Base):
    """ORM representation of a single atomic unit of work within an ``AgentRun``.

    Each ``Task`` row corresponds to one element in ``AgentRun.plan``.
    The ``position`` column preserves the plan's original ordering and is
    protected by a ``UNIQUE (agent_run_id, position)`` constraint.

    Table:
        tasks

    Primary key:
        ``id`` — UUID v4, generated application-side so callers can
        construct the identifier before the INSERT is committed.

    Foreign key:
        ``agent_run_id`` → ``agent_runs.id``.  ``ON DELETE CASCADE``
        ensures all tasks are removed when their parent run is deleted.

    Relationship:
        ``agent_run`` — unidirectional many-to-one to ``AgentRun``.
        The reciprocal ``AgentRun.tasks`` will be added in a dedicated
        ``agent_run.py`` update.

    Attributes:
        id: UUID v4 primary key, generated on the Python side before INSERT.
        agent_run_id: Non-nullable FK to ``agent_runs.id``.  Cascades on
            delete.
        position: Zero-based ordinal mirroring the task's index in
            ``AgentRun.plan``.  Constrained to ``>= 0``; unique within a
            run via ``uq_task_agent_run_position``.
        title: Short human-readable label for the subtask (max 500 chars).
        description: Optional full subtask description; may include context
            injected by the Planner node.
        status: Current lifecycle state.  Defaults to ``TaskStatus.PENDING``.
        priority: Queue ordering weight.  Defaults to ``TaskPriority.NORMAL``.
        task_metadata: Arbitrary agent-supplied JSONB context (tool
            parameters, constraints, intermediate artefacts).  Stored in the
            Postgres column ``metadata``; mapped to ``task_metadata`` in
            Python to avoid shadowing ``DeclarativeBase.metadata``.
        tool_name: Identifier of the worker agent or tool assigned to
            execute this task (e.g. ``"code_writer"``).  ``None`` until the
            Supervisor dispatches the task.
        result: Textual output produced when the task reaches ``COMPLETED``.
            ``None`` for all other states.
        error_message: Human-readable failure description.  ``None`` unless
            the task is in ``FAILED`` status.
        retry_count: Number of times this task has been retried after
            ``FAILED``.  Constrained to ``<= max_retries`` and ``>= 0``.
        max_retries: Maximum number of retry attempts before the task is
            considered permanently failed.  Defaults to ``3``.
        started_at: Timezone-aware timestamp set when status transitions to
            ``RUNNING``.  ``None`` while the task is still ``PENDING``.
        finished_at: Timezone-aware timestamp set when any terminal state
            (``COMPLETED``, ``FAILED``, ``SKIPPED``, ``CANCELLED``) is
            reached.  Always ``>= started_at`` when both are non-null
            (enforced by ``ck_task_finished_after_started``).
        created_at: Inherited from ``TimestampMixin``.  Set once on INSERT.
        updated_at: Inherited from ``TimestampMixin``.  Refreshed on UPDATE.
        agent_run: Many-to-one relationship to the parent ``AgentRun``.
            Loaded via ``selectin`` strategy so that ``AsyncSession`` callers
            receive a populated attribute without explicit ``joinedload`` /
            ``selectinload`` options.
    """

    __tablename__ = "tasks"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side before INSERT.",
    )

    # ------------------------------------------------------------------
    # Parent run reference
    # ------------------------------------------------------------------

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        doc=(
            "Non-nullable FK to agent_runs.id.  "
            "ON DELETE CASCADE removes all child tasks when the run is deleted."
        ),
    )

    # ------------------------------------------------------------------
    # Plan ordering
    # ------------------------------------------------------------------

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc=(
            "Zero-based ordinal mirroring this task's index in AgentRun.plan.  "
            "Constrained to >= 0; unique within a run via uq_task_agent_run_position."
        ),
    )

    # ------------------------------------------------------------------
    # Task definition
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Short human-readable label for the subtask (max 500 chars).",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "Optional full subtask description.  "
            "May include context injected by the Planner node."
        ),
    )

    # ------------------------------------------------------------------
    # Lifecycle state and priority
    # ------------------------------------------------------------------

    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",      # Postgres ENUM type name
            native_enum=True,        # Use a real Postgres ENUM (not VARCHAR)
            create_constraint=True,  # Emit CREATE TYPE on DDL generation
            validate_strings=True,   # Reject unknown values on load
        ),
        nullable=False,
        default=TaskStatus.PENDING,
        doc="Current lifecycle state.  Defaults to PENDING on creation.",
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            name="task_priority",    # Postgres ENUM type name
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=TaskPriority.NORMAL,
        doc="Queue ordering weight.  Defaults to NORMAL.",
    )

    # ------------------------------------------------------------------
    # Agent-supplied context (JSONB)
    # ------------------------------------------------------------------

    task_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",                  # Postgres column name — avoids Base.metadata clash
        JSONB,
        nullable=True,
        doc=(
            "Arbitrary agent-supplied JSONB context (tool parameters, constraints, "
            "intermediate artefacts).  Stored in the Postgres column 'metadata'; "
            "mapped to 'task_metadata' in Python to avoid shadowing "
            "DeclarativeBase.metadata."
        ),
    )

    # ------------------------------------------------------------------
    # Execution assignment
    # ------------------------------------------------------------------

    tool_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc=(
            "Identifier of the worker agent or tool assigned to execute this task "
            "(e.g. 'code_writer').  None until the Supervisor dispatches the task."
        ),
    )

    # ------------------------------------------------------------------
    # Outcomes
    # ------------------------------------------------------------------

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Textual output produced when the task reaches COMPLETED.  None otherwise.",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable failure description.  None unless status is FAILED.",
    )

    # ------------------------------------------------------------------
    # Retry tracking
    # ------------------------------------------------------------------

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc=(
            "Number of times this task has been retried after FAILED.  "
            "Constrained to >= 0 and <= max_retries."
        ),
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        doc=(
            "Maximum retry attempts before the task is considered permanently failed.  "
            "Constrained to >= 0."
        ),
    )

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timezone-aware timestamp set when status transitions to RUNNING.",
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc=(
            "Timezone-aware timestamp set when any terminal state is reached.  "
            "Always >= started_at when both are non-null "
            "(enforced by ck_task_finished_after_started)."
        ),
    )

    # ------------------------------------------------------------------
    # Relationship
    # ------------------------------------------------------------------

    agent_run: Mapped[AgentRun] = relationship(
        "AgentRun",
        foreign_keys=[agent_run_id],
        # selectin is required for AsyncSession: implicit lazy="select" raises
        # MissingGreenlet when the attribute is accessed outside an awaitable
        # context.  Callers can suppress loading entirely with noload() option.
        lazy="selectin",
        doc=(
            "Many-to-one relationship to the parent AgentRun.  "
            "Unidirectional — AgentRun.tasks back-reference is wired separately."
        ),
    )

    # ------------------------------------------------------------------
    # Unique constraints, check constraints, and indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Unique constraints ------------------------------------------------

        # No two tasks may occupy the same plan slot within a single run
        UniqueConstraint(
            "agent_run_id",
            "position",
            name="uq_task_agent_run_position",
        ),

        # Check constraints ------------------------------------------------

        CheckConstraint(
            "position >= 0",
            name="ck_task_position_non_negative",
        ),
        CheckConstraint(
            "retry_count >= 0",
            name="ck_task_retry_count_non_negative",
        ),
        CheckConstraint(
            "max_retries >= 0",
            name="ck_task_max_retries_non_negative",
        ),
        CheckConstraint(
            "retry_count <= max_retries",
            name="ck_task_retry_count_lte_max",
        ),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name="ck_task_finished_after_started",
        ),

        # Indexes ----------------------------------------------------------

        # Fetch all tasks belonging to a run (most common query path)
        Index("ix_task_agent_run_id", "agent_run_id"),

        # Filter tasks by current lifecycle state (dashboard, queue polling)
        Index("ix_task_status", "status"),

        # Priority-queue polling by the ExecutionEngine
        Index("ix_task_priority", "priority"),

        # Ordered task list for a given run (cursor-based pagination)
        Index("ix_task_agent_run_position", "agent_run_id", "position"),

        # Dispatcher hot path: highest-priority PENDING task across all runs
        Index("ix_task_status_priority", "status", "priority"),
    )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation.

        Returns:
            str: A string of the form
                ``Task(id=..., status=..., priority=..., position=..., title=...)``.
        """
        title_preview = (self.title[:40] + "…") if len(self.title) > 40 else self.title
        return (
            f"Task("
            f"id={self.id!s}, "
            f"status={self.status!r}, "
            f"priority={self.priority!r}, "
            f"position={self.position!r}, "
            f"title={title_preview!r}"
            f")"
        )
