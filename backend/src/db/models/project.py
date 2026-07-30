"""
ASEP — Project ORM Model
=========================
A Project belongs to an Organization and is the scope boundary for API Keys.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class Project(TimestampMixin, Base):
    """A named workspace within an Organization.

    Table:
        projects

    Relationships:
        - Belongs to one Organization (via org_id FK).
        - Has many ApiKeys scoped to it.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the owning Organization.",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable project name.",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="URL-safe unique identifier within the org.",
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="Optional project description.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Soft-disable flag.",
    )

    def __repr__(self) -> str:
        return f"Project(id={self.id!s}, slug={self.slug!r}, org_id={self.org_id!s})"
