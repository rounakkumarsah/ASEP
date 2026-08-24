"""
ASEP — Subscription ORM Model
==============================
Organization-scoped subscription to a ASEP SaaS plan.

Status lifecycle:
    trialing → active → past_due → cancelled
                      ↘ cancelled
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class Subscription(TimestampMixin, Base):
    """Organization-level SaaS subscription record.

    Table:
        subscriptions

    Status values:
        trialing   — Free trial period active.
        active     — Paid and current.
        past_due   — Payment failed; grace period.
        cancelled  — Explicitly cancelled.
    """

    __tablename__ = "subscriptions"

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

    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Plan identifier: starter | pro | enterprise.",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="trialing",
        index=True,
        doc="Subscription status: trialing | active | past_due | cancelled.",
    )

    # -----------------------------------------------------------------------
    # Razorpay references (nullable for free/trial plans)
    # -----------------------------------------------------------------------
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Razorpay Order ID that activated this subscription.",
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Razorpay Payment ID for the activating payment.",
    )

    # -----------------------------------------------------------------------
    # Billing period
    # -----------------------------------------------------------------------
    current_period_start: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Start of the current billing period (UTC).",
    )

    current_period_end: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="End of the current billing period (UTC).",
    )

    cancelled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of cancellation, if applicable.",
    )

    def __repr__(self) -> str:
        return (
            f"Subscription(id={self.id!s}, org_id={self.org_id!s}, "
            f"plan={self.plan!r}, status={self.status!r})"
        )
