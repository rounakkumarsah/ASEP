"""
ASEP — UserApiKey ORM Model (BYOK)
===================================
Defines the ``UserApiKey`` SQLAlchemy 2.0 mapped model for Bring Your Own Key
(BYOK) LLM provider credentials.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class UserApiKey(TimestampMixin, Base):
    """User-scoped LLM provider credentials encrypted at rest.

    Table:
        user_api_keys

    Unique:
        (user_id, provider) ensures at most one active key per provider per user.
    """

    __tablename__ = "user_api_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_api_keys_user_id_provider"),
    )

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
        doc="FK to the owning User.",
    )

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        doc="Provider slug (e.g. 'groq', 'gemini', 'openrouter', 'openai', 'anthropic').",
    )

    encrypted_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Fernet-encrypted API key token.",
    )

    key_preview: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="Masked preview for UI display, e.g. 'sk-...abcd'.",
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the key passed the most recent liveness/auth check.",
    )

    last_validated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of the most recent key validation.",
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message or failure reason from the most recent validation failure.",
    )

    def __repr__(self) -> str:
        return (
            f"UserApiKey(id={self.id!s}, user_id={self.user_id!s}, "
            f"provider={self.provider!r}, valid={self.is_valid})"
        )
