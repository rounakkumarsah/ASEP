"""
ASEP — HITLSession ORM Model
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base
from src.db.models.agent_run import TimestampMixin


class HITLStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class HITLAction(str, enum.Enum):
    APPROVE = "Approve"
    REJECT = "Reject"
    MODIFY = "Modify"
    RETRY = "Retry"
    ESCALATE = "Escalate"
    CANCEL = "Cancel"
    EXPIRE = "Expire"


class HITLSession(TimestampMixin, Base):
    """ORM representation of a human-in-the-loop review session."""

    __tablename__ = "hitl_sessions"

    session_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    correlation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    requesting_agent: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    requesting_tool: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[HITLStatus] = mapped_column(
        Enum(
            HITLStatus,
            name="hitl_status",
            native_enum=True,
            create_constraint=True,
        ),
        nullable=False,
        default=HITLStatus.PENDING,
    )

    decision: Mapped[HITLAction | None] = mapped_column(
        Enum(
            HITLAction,
            name="hitl_action",
            native_enum=True,
            create_constraint=True,
        ),
        nullable=True,
        default=None,
    )

    reviewer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reviewer_role: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    arguments_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latency_seconds: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    ttl_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
    )
