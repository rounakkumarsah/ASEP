"""
ASEP — Payment ORM Model
=========================
Persists Razorpay payment lifecycle data.

Columns track every state from order creation through capture / refund,
making it safe to reconcile with Razorpay's dashboard at any time.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class Payment(TimestampMixin, Base):
    """
    ORM representation of a Razorpay payment transaction.

    Table:
        payments

    Status lifecycle:
        created → authorized → captured → refunded
                             ↘ failed
    """

    __tablename__ = "payments"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Internal UUID primary key.",
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the user who initiated the payment.",
    )

    # ------------------------------------------------------------------
    # Razorpay identifiers
    # ------------------------------------------------------------------
    razorpay_order_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Razorpay Order ID (order_XXXX). Created before checkout.",
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Razorpay Payment ID (pay_XXXX). Set after successful payment.",
    )

    razorpay_signature: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="HMAC-SHA256 signature verified during payment confirmation.",
    )

    # ------------------------------------------------------------------
    # Financials
    # ------------------------------------------------------------------
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Payment amount in the smallest currency unit (paise for INR).",
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
        doc="ISO 4217 currency code.",
    )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="created",
        index=True,
        doc="Payment status: created | authorized | captured | failed | refunded.",
    )

    # ------------------------------------------------------------------
    # Optional metadata
    # ------------------------------------------------------------------
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Human-readable description of what was purchased.",
    )

    notes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Arbitrary key-value notes forwarded to Razorpay.",
    )

    def __repr__(self) -> str:
        return (
            f"Payment(id={self.id!s}, order_id={self.razorpay_order_id!r}, "
            f"status={self.status!r}, amount={self.amount})"
        )
