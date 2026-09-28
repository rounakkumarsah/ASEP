"""
ASEP — QueueJob ORM Model
=========================
Defines the ``QueueJob`` SQLAlchemy 2.0 mapped class, which tracks background agent execution
jobs managed by APScheduler with persistent PostgreSQL job state.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


class QueueJob(Base):
    """ORM representation of an asynchronous agent execution job.

    Table:
        queue_jobs

    Primary key:
        ``id`` — UUID v4, generated application-side.

    Attributes:
        id: Unique UUID v4 job ID.
        user_id: UUID of user who requested the execution.
        workspace_id: Identifier of the workspace (used for concurrency limits).
        status: Current job status ('pending', 'running', 'completed', 'failed').
        spec: Serialized dictionary defining the execution prompt, options, etc.
        result: Serialized agent execution output (code, review, tests).
        error: Detailed error message if failed.
        retry_count: Number of retries attempted so far.
        max_retries: Maximum number of retries permitted (default: 2).
        metrics: Dictionary of execution metrics (runtime_ms, tokens, steps).
        created_at: Timestamp when job was enqueued.
        updated_at: Timestamp of last status or progress change.
        completed_at: Timestamp when execution completed or definitively failed.
    """

    __tablename__ = "queue_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ForeignKey referencing users.id.",
    )

    workspace_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="default",
        index=True,
        doc="Workspace partition identifier.",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
        doc="Execution status: pending, running, completed, failed.",
    )

    spec: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Input specification dictionary for agent execution.",
    )

    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        default=None,
        doc="Final or partial execution results (code, review, tests).",
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Failure details or traceback message if execution errored.",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Count of automatic retries performed.",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        doc="Maximum number of retries permitted before terminal failure.",
    )

    metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        default=None,
        doc="Execution telemetry: execution duration, token counts, steps.",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the job was enqueued.",
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp of final completion or terminal failure.",
    )

    __table_args__ = (
        Index("ix_queue_jobs_workspace_status", "workspace_id", "status"),
        Index("ix_queue_jobs_completed_at", "completed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"QueueJob(id={self.id!s}, user_id={self.user_id!s}, "
            f"workspace_id={self.workspace_id!r}, status={self.status!r}, "
            f"retry_count={self.retry_count})"
        )
