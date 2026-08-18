"""
ASEP — User ORM Model
=====================
Defines the ``User`` SQLAlchemy 2.0 mapped class, which represents a human
operator interacting with the platform.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    String,
    Uuid,
    DateTime,
    ForeignKey,
    Index,
    func,
)
import datetime
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class User(TimestampMixin, Base):
    """ORM representation of a human operator.

    Table:
        users

    Primary key:
        ``id`` — UUID v4, generated application-side.

    Attributes:
        id: UUID v4 primary key.
        username: Unique string identifier for the user.
        email: Unique email address.
        hashed_password: Argon2 hashed password string.
        is_active: Boolean flag indicating if the account is active.
        created_at: Inherited from ``TimestampMixin``.
        updated_at: Inherited from ``TimestampMixin``.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, generated application-side.",
    )

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username.",
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="First name of the user.",
    )

    last_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Last name of the user.",
    )

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Associated company name.",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address.",
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="Argon2 hashed password string. NULL for OAuth-only users.",
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Flag indicating if the user's email has been verified.",
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="viewer",
        nullable=False,
        doc="RBAC role assigned to the user.",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        doc="Current status of the user (active, suspended, etc.).",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="Avatar image URL.",
    )

    last_login: Mapped[datetime.datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Last login timestamp.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the account is active.",
    )

    # -----------------------------------------------------------------------
    # OAuth / Social Login
    # -----------------------------------------------------------------------
    oauth_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="OAuth provider name ('github' or 'google'). NULL for email/password users.",
    )

    oauth_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Provider-specific user ID for OAuth users. NULL for email/password users.",
    )

    # -----------------------------------------------------------------------
    # Multi-tenancy
    # -----------------------------------------------------------------------
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="FK to the Organization this user belongs to. NULL until assigned.",
    )

    __table_args__ = (
        Index("uq_users_lower_username", func.lower(username), unique=True),
        Index("uq_users_lower_email", func.lower(email), unique=True),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!s}, email={self.email!r})"
