"""
ASEP — AgentRun ORM Model
==========================
Defines the ``AgentRun`` SQLAlchemy 2.0 mapped class, which represents a
single autonomous agent execution: from goal submission through planning,
execution, and a terminal outcome.

Design notes:
    - Uses SQLAlchemy 2.0 ``Mapped`` / ``mapped_column`` API throughout;
      the legacy ``Column`` API is intentionally absent.
    - ``RunStatus`` is persisted as a native Postgres ``ENUM`` type, giving
      DB-level constraint enforcement rather than relying solely on the
      application layer.
    - ``plan`` and ``token_usage`` are stored as ``JSONB`` to allow Postgres
      operators and GIN indexing in future queries.
    - All timestamps are timezone-aware (``TIMESTAMPTZ``).  Server-side
      defaults via ``func.now()`` are used instead of Python-side
      ``datetime.utcnow()`` (deprecated in Python 3.12).
    - ``session_id`` is a bare ``VARCHAR(255)``; a FK to a ``sessions`` table
      will be added when that model is introduced.
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
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.postgres import Base


# ---------------------------------------------------------------------------
# RunStatus
# ---------------------------------------------------------------------------


class RunStatus(str, enum.Enum):
    """Lifecycle states of a single ``AgentRun``.

    Inheriting from ``str`` means every member is simultaneously a plain
    Python string and an enum member, which simplifies JSON serialisation
    and comparison without requiring ``.value`` access.

    State machine::

        PENDING ──► RUNNING ──► COMPLETED
                       │
                       ├──► FAILED
                       ├──► CANCELLED
                       └──► TIMED_OUT

    Attributes:
        PENDING: Queued and waiting for an executor slot.
        RUNNING: Actively executing inside the LangGraph supervisor.
        COMPLETED: Finished successfully; ``final_output`` is populated.
        FAILED: Terminated with an unrecoverable error; ``error_message``
            is populated.
        CANCELLED: Stopped explicitly by the user or by the governance
            policy engine before completion.
        TIMED_OUT: Exceeded the configured wall-clock deadline without
            reaching a terminal state.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


# ---------------------------------------------------------------------------
# TimestampMixin
# ---------------------------------------------------------------------------


class TimestampMixin:
    """Reusable mixin that adds ``created_at`` and ``updated_at`` columns.

    Designed for use with SQLAlchemy 2.0 declarative models.  Both columns
    use server-side ``func.now()`` defaults so the database clock governs
    timestamps rather than the application server clock, which may drift in
    distributed deployments.

    Usage::

        class MyModel(TimestampMixin, Base):
            __tablename__ = "my_table"
            id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Attributes:
        created_at: Timezone-aware UTC timestamp set once on INSERT.
        updated_at: Timezone-aware UTC timestamp refreshed on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timezone-aware UTC timestamp set once on INSERT.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timezone-aware UTC timestamp refreshed automatically on every UPDATE.",
    )


# ---------------------------------------------------------------------------
# AgentRun
# ---------------------------------------------------------------------------


class AgentRun(TimestampMixin, Base):
    """ORM representation of a single autonomous agent execution.

    Each row records the full lifecycle of one run: who requested it,
    what goal was given, what plan was produced, what happened during
    execution, and the final outcome.

    Table:
        agent_runs

    Primary key:
        ``id`` — UUID v4, generated application-side so callers can construct
        the identifier before the INSERT is committed.

    Status transitions:
        Only the ``ExecutionEngine`` and the ``Supervisor`` node should
        mutate ``status``; the model itself enforces no Python-level
        transition guards (that logic belongs in the service layer).

    Attributes:
        id: UUID primary key.  Generated by ``uuid.uuid4`` on the Python
            side before the row is persisted.
        session_id: Optional opaque caller-session handle (no FK yet;
            will be constrained when the Session model is introduced).
        goal: The verbatim high-level task description supplied by the user.
        status: Current lifecycle state.  Defaults to ``RunStatus.PENDING``.
        plan: JSON array of ordered subtask strings produced by the Planner
            node.  ``None`` until the Planner has completed.
        current_step: Zero-based index into ``plan`` indicating the step the
            Supervisor is currently dispatching.  Constrained to ``>= 0``.
        final_output: The agent's textual response to the user.  ``None``
            until the run reaches ``COMPLETED``.
        error_message: Human-readable description of the failure.  ``None``
            unless the run is in ``FAILED`` or ``TIMED_OUT`` status.
        token_usage: Optional JSON object recording LLM token consumption.
            Expected shape: ``{"prompt": int, "completion": int, "total": int}``.
        model_name: Identifier of the LLM that served this run
            (e.g. ``"llama3.2"``).  ``None`` until the run starts.
        started_at: Timezone-aware timestamp set when status transitions to
            ``RUNNING``.  ``None`` while the run is still ``PENDING``.
        finished_at: Timezone-aware timestamp set when any terminal status
            (``COMPLETED``, ``FAILED``, ``CANCELLED``, ``TIMED_OUT``) is
            reached.  Always ``>= started_at`` when both are non-null
            (enforced by a DB-level check constraint).
        created_at: Inherited from ``TimestampMixin``.
        updated_at: Inherited from ``TimestampMixin``.
    """

    __tablename__ = "agent_runs"

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
    # Caller context
    # ------------------------------------------------------------------

    session_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc=(
            "Opaque caller-session identifier.  VARCHAR(255) with no FK "
            "constraint until the Session model is introduced."
        ),
    )

    # ------------------------------------------------------------------
    # Task definition
    # ------------------------------------------------------------------

    goal: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Verbatim high-level task description supplied by the user.",
    )

    # ------------------------------------------------------------------
    # Lifecycle state
    # ------------------------------------------------------------------

    status: Mapped[RunStatus] = mapped_column(
        Enum(
            RunStatus,
            name="run_status",          # Postgres ENUM type name
            native_enum=True,           # Use a real Postgres ENUM (not VARCHAR)
            create_constraint=True,     # Emit CREATE TYPE on DDL generation
            validate_strings=True,      # Reject unknown values on load
        ),
        nullable=False,
        default=RunStatus.PENDING,
        doc="Current lifecycle state; defaults to PENDING on creation.",
    )

    # ------------------------------------------------------------------
    # Execution plan
    # ------------------------------------------------------------------

    plan: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc=(
            "Ordered list of subtask strings produced by the Planner node.  "
            "Stored as JSONB to allow future operator queries.  "
            "None until the Planner has completed."
        ),
    )

    current_step: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc=(
            "Zero-based index of the plan step currently being dispatched "
            "by the Supervisor.  Constrained to >= 0 at the DB level."
        ),
    )

    # ------------------------------------------------------------------
    # Outcomes
    # ------------------------------------------------------------------

    final_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Agent's textual response to the user.  None until COMPLETED.",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "Human-readable failure description.  "
            "None unless status is FAILED or TIMED_OUT."
        ),
    )

    # ------------------------------------------------------------------
    # LLM telemetry
    # ------------------------------------------------------------------

    token_usage: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc=(
            "LLM token consumption.  "
            "Expected shape: {\"prompt\": int, \"completion\": int, \"total\": int}.  "
            "None until the run starts consuming tokens."
        ),
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Identifier of the LLM that served this run (e.g. 'llama3.2').",
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
            "Timezone-aware timestamp set when any terminal status is reached.  "
            "Always >= started_at when both columns are non-null "
            "(enforced by ck_agent_run_finished_after_started)."
        ),
    )

    # ------------------------------------------------------------------
    # Indexes and check constraints
    # ------------------------------------------------------------------

    __table_args__ = (
        # Constraints -------------------------------------------------------

        CheckConstraint(
            "current_step >= 0",
            name="ck_agent_run_step_non_negative",
        ),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name="ck_agent_run_finished_after_started",
        ),

        # Indexes -----------------------------------------------------------

        # Single-column: filter by current lifecycle state (dashboard, queue)
        Index("ix_agent_run_status", "status"),

        # Single-column: retrieve all runs for a given caller session
        Index("ix_agent_run_session_id", "session_id"),

        # Single-column: time-ordered listing with cursor-based pagination
        Index("ix_agent_run_created_at", "created_at"),

        # Composite: "give me the oldest PENDING runs" — avoids a full scan
        # when the queue poller polls for work
        Index("ix_agent_run_status_created_at", "status", "created_at"),
    )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation.

        Returns:
            str: A string of the form
                ``AgentRun(id=..., status=..., goal=...)``.
        """
        goal_preview = (self.goal[:40] + "…") if len(self.goal) > 40 else self.goal
        return (
            f"AgentRun("
            f"id={self.id!s}, "
            f"status={self.status!r}, "
            f"goal={goal_preview!r}"
            f")"
        )
