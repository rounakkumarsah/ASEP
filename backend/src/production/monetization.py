"""
ASEP — Freemium Rate Limiter & Razorpay Monetization
=====================================================
Redis-backed rate limiting middleware (Free=10 queries/day),
Razorpay checkout link generation, and webhook tier upgrade processing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from typing import Any

from src.cache.redis import get_redis_client
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    remaining_queries: int
    current_tier: str
    reset_seconds: int


class FreemiumRateLimiter:
    """Redis-backed rate limiter enforcing 10 queries/day for Free tier users."""

    def __init__(self, free_daily_limit: int = 10) -> None:
        self.free_limit = free_daily_limit

    async def check_rate_limit(self, user_id: str, tier: str = "free") -> RateLimitResult:
        if tier.lower() in ["pro", "enterprise"]:
            return RateLimitResult(allowed=True, remaining_queries=999999, current_tier=tier, reset_seconds=0)

        redis = get_redis_client()
        day_key = time.strftime("%Y-%m-%d")
        key = f"rate_limit:{user_id}:{day_key}"

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 86400)

            remaining = max(0, self.free_limit - count)
            allowed = count <= self.free_limit

            if not allowed:
                logger.warning("Free tier rate limit exceeded for user %s (%d/%d)", user_id, count, self.free_limit)

            return RateLimitResult(
                allowed=allowed,
                remaining_queries=remaining,
                current_tier=tier,
                reset_seconds=86400,
            )
        except Exception as exc:
            logger.debug("Rate limit check fallback (Redis unavailable): %s", exc)
            return RateLimitResult(allowed=True, remaining_queries=self.free_limit, current_tier=tier, reset_seconds=0)

    async def get_usage(self, user_id: str, tier: str = "free") -> RateLimitResult:
        """Inspect current daily usage without consuming a credit."""
        if tier.lower() in ["pro", "enterprise"]:
            return RateLimitResult(allowed=True, remaining_queries=999999, current_tier=tier, reset_seconds=0)

        redis = get_redis_client()
        day_key = time.strftime("%Y-%m-%d")
        key = f"rate_limit:{user_id}:{day_key}"

        try:
            if not redis:
                return RateLimitResult(allowed=True, remaining_queries=self.free_limit, current_tier=tier, reset_seconds=86400)

            count_str = await redis.get(key)
            count = int(count_str) if count_str is not None else 0
            remaining = max(0, self.free_limit - count)
            return RateLimitResult(
                allowed=count < self.free_limit,
                remaining_queries=remaining,
                current_tier=tier,
                reset_seconds=86400,
            )
        except Exception as exc:
            logger.debug("Quota check fallback (Redis unavailable): %s", exc)
            return RateLimitResult(allowed=True, remaining_queries=self.free_limit, current_tier=tier, reset_seconds=0)


class RazorpayMonetizationManager:
    """Razorpay Checkout and Webhook Tier Upgrade Integration."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_checkout_url(self, user_id: str, plan_tier: str = "pro") -> dict[str, Any]:
        """Generate Razorpay order parameters for frontend checkout modal."""
        amount_in_paise = 299900 if plan_tier == "pro" else 999900  # ₹2,999 or ₹9,999
        order_id = f"order_{user_id[:8]}_{int(time.time())}"

        logger.info("Generated Razorpay checkout order %s for user %s (tier=%s)", order_id, user_id, plan_tier)
        return {
            "order_id": order_id,
            "key_id": self.settings.RAZORPAY_KEY_ID or "rzp_test_mock_key",
            "amount": amount_in_paise,
            "currency": "INR",
            "plan_tier": plan_tier,
        }

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature using HMAC SHA-256."""
        secret = self.settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            logger.warning("RAZORPAY_WEBHOOK_SECRET not configured — skipping signature check.")
            return True

        expected_sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)
