"""
ASEP — UserQuotaLog ORM Model
=============================
Defines the ``UserQuotaLog`` SQLAlchemy 2.0 mapped class, which tracks token usage
per user and model provider for quota enforcement and usage aggregation.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


class UserQuotaLog(Base):
    """ORM representation of a token usage log record.

    Table:
        user_quota_logs

    Primary key:
        ``id`` — UUID v4, generated application-side.

    Attributes:
        id: UUID v4 primary key.
        user_id: UUID of user consuming tokens (ForeignKey to users.id).
        tokens_used: Number of tokens consumed in the interaction.
        provider_name: AI model provider (e.g. openai, anthropic, gemini).
        timestamp: Timestamp of usage event.
    """

    __tablename__ = "user_quota_logs"

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

    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total tokens consumed in this call.",
    )

    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="unknown",
        doc="Name of the AI provider or execution model.",
    )

    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of token usage.",
    )

    __table_args__ = (
        Index("ix_user_quota_logs_user_timestamp", "user_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"UserQuotaLog(id={self.id!s}, user_id={self.user_id!s}, "
            f"tokens_used={self.tokens_used}, provider={self.provider_name!r})"
        )
