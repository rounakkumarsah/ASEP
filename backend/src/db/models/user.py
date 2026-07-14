"""
ASEP — User ORM Model
=====================
Defines the ``User`` SQLAlchemy 2.0 mapped class, which represents a human
operator interacting with the platform.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    String,
    Uuid,
)
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

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address.",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Argon2 hashed password string.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the account is active.",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!s}, username={self.username!r}, email={self.email!r})"
