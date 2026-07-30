"""
ASEP — API Key ORM Model
=========================
Project-scoped API keys for programmatic access to the ASEP platform.

Security design:
    - The full key is generated once and NEVER stored.
    - Only the SHA-256 hash is persisted in the database.
    - The key_prefix (first 8 chars) is stored for display/identification.
    - Clients authenticate by presenting the full key; the backend hashes
      it and compares against key_hash using hmac.compare_digest.
"""

from __future__ import annotations

import uuid
import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class ApiKey(TimestampMixin, Base):
    """Project-scoped API key for programmatic ASEP access.

    Table:
        api_keys

    Key lifecycle:
        created → [used] → revoked (is_active=False)

    Security guarantees:
        - ``key_hash`` is SHA-256(full_key). The full key is never stored.
        - ``key_prefix`` is the first 8 characters for display only.
        - Comparison uses ``hmac.compare_digest`` to prevent timing attacks.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the owning Project.",
    )

    # Owner for direct user-lookup without joining projects
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the User who created this key.",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable label for this key (e.g. 'CI/CD pipeline').",
    )

    key_prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="First 8 characters of the key — shown in UI for identification.",
    )

    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hex digest of the full API key.",
    )

    scopes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Optional JSON list of permission scopes (e.g. ['read', 'write']).",
    )

    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Optional expiry timestamp. None = no expiry.",
    )

    last_used_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent successful authentication with this key.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="False = revoked. Revoked keys are never deleted — kept for audit.",
    )

    def __repr__(self) -> str:
        return (
            f"ApiKey(id={self.id!s}, prefix={self.key_prefix!r}, "
            f"project_id={self.project_id!s}, active={self.is_active})"
        )
