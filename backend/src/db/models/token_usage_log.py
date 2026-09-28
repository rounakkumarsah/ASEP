"""
ASEP — TokenUsageLog ORM Model
==============================
Defines the ``TokenUsageLog`` SQLAlchemy 2.0 mapped class, which tracks granular
token consumption and cost attribution per user, workspace, and model provider.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


class TokenUsageLog(Base):
    """ORM representation of a granular LLM token usage and cost log.

    Table:
        token_usage_logs

    Primary key:
        ``id`` — UUID v4, generated application-side.

    Attributes:
        id: UUID v4 primary key.
        user_id: UUID of user consuming tokens (ForeignKey to users.id).
        workspace_id: String identifier of the workspace / partition.
        provider: AI model provider (e.g. groq, gemini, openrouter).
        input_tokens: Number of prompt/input tokens consumed.
        output_tokens: Number of completion/output tokens generated.
        cost_usd: Estimated cost of the interaction in USD.
        timestamp: Timestamp of the token usage event.
    """

    __tablename__ = "token_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side.",
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
        server_default="default",
        doc="Workspace partition identifier.",
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="unknown",
        server_default="unknown",
        doc="Name of the AI provider (groq, gemini, openrouter).",
    )

    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Input / prompt tokens consumed.",
    )

    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        doc="Output / completion tokens generated.",
    )

    cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
        doc="Estimated USD cost of the call.",
    )

    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of token usage event.",
    )

    __table_args__ = (
        Index("ix_token_usage_logs_user_ts_provider", "user_id", "timestamp", "provider"),
        Index("ix_token_usage_logs_workspace_ts", "workspace_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"TokenUsageLog(id={self.id!s}, user_id={self.user_id!s}, "
            f"workspace_id={self.workspace_id!r}, provider={self.provider!r}, "
            f"input={self.input_tokens}, output={self.output_tokens}, cost={self.cost_usd})"
        )
