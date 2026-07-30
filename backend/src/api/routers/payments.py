"""
ASEP — Payments Router
========================
Handles Razorpay payment creation, server-side verification, and webhooks.

Security guarantees:
  - RAZORPAY_KEY_SECRET is NEVER returned to the client.
  - Payment signature uses HMAC-SHA256 (razorpay_order_id|razorpay_payment_id).
  - Webhook signature uses HMAC-SHA256 over the raw request body.
  - All secrets are read exclusively from environment settings.

Switching from Test → Live Mode:
  - Change RAZORPAY_KEY_ID  (rzp_test_* → rzp_live_*)
  - Change RAZORPAY_KEY_SECRET
  - Change RAZORPAY_WEBHOOK_SECRET
  - No source code changes required.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid

import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.config.settings import get_settings
from src.db.models.payment import Payment
from src.db.postgres import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CreateOrderRequest(BaseModel):
    """Payload to create a new Razorpay order."""

    amount: int = Field(
        ...,
        ge=100,
        description="Amount in paise (smallest INR unit). Minimum 100 = ₹1.",
        examples=[49900],
    )
    currency: str = Field(default="INR", max_length=3, description="ISO 4217 currency code.")
    description: str | None = Field(default=None, max_length=500)
    notes: dict | None = Field(default=None, description="Arbitrary key-value pairs forwarded to Razorpay.")


class CreateOrderResponse(BaseModel):
    """Returned to the frontend after order creation. Contains NO secret."""

    order_id: str = Field(description="Razorpay Order ID (order_XXXX).")
    amount: int = Field(description="Amount in paise.")
    currency: str
    key_id: str = Field(description="Public Razorpay Key ID — safe to use in the checkout widget.")


class VerifyPaymentRequest(BaseModel):
    """Payload sent by the frontend after the Razorpay Checkout callback."""

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    payment_id: str
    message: str


class PaymentRecord(BaseModel):
    """Public representation of a payment record."""

    id: str
    razorpay_order_id: str
    razorpay_payment_id: str | None
    amount: int
    currency: str
    status: str
    description: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_razorpay_client() -> razorpay.Client:
    """
    Return an authenticated Razorpay client.

    Raises HTTP 503 if credentials are not configured,
    giving a clear error instead of an obscure AttributeError.
    """
    settings = get_settings()
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Razorpay credentials are not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured. Contact the platform administrator.",
        )
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify the Razorpay payment signature using HMAC-SHA256.

    Message: ``{razorpay_order_id}|{razorpay_payment_id}``
    Key:     ``RAZORPAY_KEY_SECRET``

    Uses ``hmac.compare_digest`` to prevent timing attacks.
    """
    settings = get_settings()
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify a Razorpay webhook event signature.

    In development (RAZORPAY_WEBHOOK_SECRET not set) this returns True to
    allow local testing without a real webhook. In production the secret
    MUST be configured — the endpoint will reject unsigned requests.
    """
    settings = get_settings()
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        if settings.APP_ENV == "production":
            logger.error("CRITICAL: RAZORPAY_WEBHOOK_SECRET is required in production environment.")
            return False
        logger.warning(
            "RAZORPAY_WEBHOOK_SECRET is not set — skipping webhook signature check. "
            "This is only acceptable in development."
        )
        return True  # Dev fallback only
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/create-order",
    response_model=CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Razorpay payment order",
)
async def create_order(
    payload: CreateOrderRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CreateOrderResponse:
    """
    Create a Razorpay order and persist a ``Payment`` record with status=``created``.

    The response includes the **public** ``key_id`` only.
    ``RAZORPAY_KEY_SECRET`` is never returned to the client.
    """
    # Production Rate Limiting — 10 order creations / 5 mins per user
    try:
        from src.cache.redis import get_redis_client
        from src.auth.rate_limit import check_rate_limit
        redis = get_redis_client()
        rate_key = f"rate_limit:payments:create_order:{current_user.id}"
        allowed = await check_rate_limit(redis, rate_key, max_attempts=10, window_seconds=300)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a few minutes before creating another payment order.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Redis rate limit check bypassed: %s", str(e))

    settings = get_settings()
    client = _get_razorpay_client()

    receipt = str(uuid.uuid4())
    try:
        order = client.order.create(
            {
                "amount": payload.amount,
                "currency": payload.currency,
                "receipt": receipt,
                "notes": payload.notes or {},
            }
        )
    except Exception as exc:
        logger.error("Razorpay order creation failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create payment order. Please try again.",
        ) from exc

    # Persist payment record
    payment = Payment(
        user_id=current_user.id,
        razorpay_order_id=order["id"],
        amount=payload.amount,
        currency=payload.currency,
        status="created",
        description=payload.description,
        notes=payload.notes,
    )
    db.add(payment)
    await db.flush()

    logger.info(
        "Razorpay order created",
        extra={"order_id": order["id"], "user_id": str(current_user.id), "amount": payload.amount},
    )

    return CreateOrderResponse(
        order_id=order["id"],
        amount=payload.amount,
        currency=payload.currency,
        key_id=settings.RAZORPAY_KEY_ID,  # type: ignore[arg-type]
    )


@router.post(
    "/verify",
    response_model=VerifyPaymentResponse,
    summary="Verify a completed Razorpay payment",
)
async def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> VerifyPaymentResponse:
    """
    Verify the HMAC-SHA256 signature returned by Razorpay Checkout,
    then mark the payment as ``captured`` in the database.

    The client must send exactly what Razorpay's ``handler`` callback provides.
    """
    # 1. Verify signature — reject immediately on mismatch
    if not _verify_payment_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        logger.warning(
            "Razorpay signature verification failed",
            extra={"order_id": payload.razorpay_order_id, "user_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: invalid signature.",
        )

    # 2. Fetch the payment record owned by this user
    result = await db.execute(
        select(Payment).where(
            Payment.razorpay_order_id == payload.razorpay_order_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )

    # 3. Idempotent update — don't overwrite an already-captured payment
    if payment.status != "captured":
        payment.razorpay_payment_id = payload.razorpay_payment_id
        payment.razorpay_signature = payload.razorpay_signature
        payment.status = "captured"
        await db.flush()

    logger.info(
        "Payment verified and captured",
        extra={
            "order_id": payload.razorpay_order_id,
            "payment_id": payload.razorpay_payment_id,
            "user_id": str(current_user.id),
        },
    )

    return VerifyPaymentResponse(
        success=True,
        payment_id=payload.razorpay_payment_id,
        message="Payment verified successfully.",
    )


@router.get(
    "/history",
    response_model=list[PaymentRecord],
    summary="List payment history for the authenticated user",
)
async def get_payment_history(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 20,
) -> list[Payment]:
    """Return the most recent payments for the current user."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(min(limit, 100))
    )
    return list(result.scalars().all())


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Razorpay webhook event handler",
)
async def razorpay_webhook(
    request: Request,
    db: DbSession,
) -> dict:
    """
    Receive and process Razorpay webhook events.

    **Setup in Razorpay Dashboard:**
      - URL: ``https://<your-domain>/api/v1/payments/webhook``
      - Set ``RAZORPAY_WEBHOOK_SECRET`` to the secret you configure there.
      - Enable events: ``payment.captured``, ``payment.failed``, ``refund.created``.

    This endpoint is strictly idempotent — duplicate event IDs are skipped via Redis cache.
    """
    from src.cache.redis import get_redis_client

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not _verify_webhook_signature(body, signature):
        logger.warning("Razorpay webhook: invalid signature rejected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature.",
        )

    try:
        event = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload.",
        ) from exc

    # Idempotency check using x-razorpay-event-id or payload event id
    event_id: str | None = request.headers.get("X-Razorpay-Event-Id") or event.get("event_id")
    if event_id:
        redis = get_redis_client()
        # Store event ID in Redis for 24 hours to prevent duplicate processing
        is_new = await redis.set(f"razorpay_event:{event_id}", "processed", nx=True, ex=86400)
        if not is_new:
            logger.info("Duplicate Razorpay webhook event skipped", extra={"event_id": event_id})
            return {"status": "ok", "message": "Duplicate event skipped"}

    event_type: str = event.get("event", "")
    payload = event.get("payload", {})

    logger.info("Razorpay webhook received", extra={"event": event_type})

    if event_type == "payment.captured":
        entity = payload.get("payment", {}).get("entity", {})
        order_id: str | None = entity.get("order_id")
        payment_id: str | None = entity.get("id")

        if order_id and payment_id:
            result = await db.execute(select(Payment).where(Payment.razorpay_order_id == order_id))
            payment = result.scalar_one_or_none()
            if payment and payment.status != "captured":
                payment.razorpay_payment_id = payment_id
                payment.status = "captured"
                await db.flush()
                logger.info("Webhook: payment captured", extra={"order_id": order_id})

                # Activate/upsert org subscription if payment has a plan note
                notes_plan = entity.get("notes", {}).get("plan") if isinstance(entity.get("notes"), dict) else None
                if notes_plan and payment.user_id:
                    from sqlalchemy import select as _select
                    from src.db.models.subscription import Subscription
                    from src.db.models.user import User as UserModel
                    import datetime

                    user_result = await db.execute(_select(UserModel).where(UserModel.id == payment.user_id))
                    user = user_result.scalar_one_or_none()
                    if user and user.org_id:
                        now = datetime.datetime.now(datetime.timezone.utc)
                        sub_result = await db.execute(
                            _select(Subscription).where(
                                Subscription.org_id == user.org_id,
                                Subscription.plan == notes_plan,
                            )
                        )
                        subscription = sub_result.scalar_one_or_none()
                        if not subscription:
                            subscription = Subscription(
                                id=uuid.uuid4(),
                                org_id=user.org_id,
                                plan=notes_plan,
                                status="active",
                                razorpay_order_id=order_id,
                                razorpay_payment_id=payment_id,
                                current_period_start=now,
                                current_period_end=now + datetime.timedelta(days=30),
                            )
                            db.add(subscription)
                        else:
                            subscription.status = "active"
                            subscription.razorpay_payment_id = payment_id
                            subscription.current_period_end = now + datetime.timedelta(days=30)
                        await db.flush()
                        logger.info("Subscription activated", extra={"org_id": str(user.org_id), "plan": notes_plan})

    elif event_type == "payment.failed":
        entity = payload.get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")

        if order_id:
            result = await db.execute(select(Payment).where(Payment.razorpay_order_id == order_id))
            payment = result.scalar_one_or_none()
            if payment and payment.status not in {"captured", "refunded"}:
                payment.status = "failed"
                await db.flush()
                logger.info("Webhook: payment failed", extra={"order_id": order_id})

    elif event_type == "refund.created":
        entity = payload.get("refund", {}).get("entity", {})
        payment_id = entity.get("payment_id")

        if payment_id:
            result = await db.execute(
                select(Payment).where(Payment.razorpay_payment_id == payment_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                payment.status = "refunded"
                await db.flush()
                logger.info("Webhook: payment refunded", extra={"payment_id": payment_id})

    return {"status": "ok"}


@router.get(
    "/subscription",
    summary="Get current organization subscription",
)
async def get_subscription(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Return the active subscription for the current user's organization."""
    from src.db.models.subscription import Subscription
    from sqlalchemy import select
    if not current_user.org_id:
        return {"subscription": None}
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.org_id == current_user.org_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return {"subscription": None}
    return {
        "subscription": {
            "id": str(sub.id),
            "plan": sub.plan,
            "status": sub.status,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        }
    }
