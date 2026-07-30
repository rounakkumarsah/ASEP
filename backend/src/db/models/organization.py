"""
ASEP — Organization ORM Model
==============================
An Organization is the top-level multi-tenant boundary.
Every User belongs to at most one Organization.
Projects, Subscriptions, and API Keys are scoped to an Organization.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class Organization(TimestampMixin, Base):
    """Multi-tenant organization workspace.

    Table:
        organizations

    Relationships:
        - One Organization has many Users (via users.org_id FK).
        - One Organization has one active Subscription.
        - One Organization has many Projects.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable organization name.",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-safe unique identifier (e.g. 'acme-corp').",
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="FK to the User who created / owns this organization.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Soft-disable flag for suspended organizations.",
    )

    def __repr__(self) -> str:
        return f"Organization(id={self.id!s}, slug={self.slug!r})"
