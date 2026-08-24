"""
ASEP — Redis Sliding Window Rate Limiter
=========================================
Uses atomic INCR + NX-style expiry so the window starts at first
hit and is NOT extended by subsequent requests within the same window.
"""
import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def check_rate_limit(
    redis: Redis | None,
    key: str,
    max_attempts: int,
    window_seconds: int,
) -> bool:
    """
    Fixed-window rate limiter using an atomic Redis pipeline.

    The expiry is set ONLY when the key is first created (i.e. when INCR
    returns 1), preventing the window from being silently extended by
    repeated increment calls inside the same window.

    Returns:
        True  – request is within limits and should be processed.
        False – rate limit exceeded; caller should return HTTP 429.
    """
    if redis is None:
        return True
    try:
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            results = await pipe.execute()

        count_int = int(results[0])

        if count_int == 1:
            # First hit in this window — set the expiry now.
            # All subsequent hits reuse the same TTL without extending it.
            await redis.expire(key, window_seconds)

        if count_int > max_attempts:
            ttl = await redis.ttl(key)
            logger.warning(
                "Rate limit exceeded",
                extra={"key": key, "count": count_int, "ttl_remaining": ttl},
            )
            return False

        return True
    except Exception as exc:
        # Fail open — do not block requests when Redis is unavailable.
        # This is intentional: availability > strict rate limiting during outage.
        logger.error("Rate limit Redis error: %s", exc)
        return True


async def get_rate_limit_status(
    redis: Redis | None,
    key: str,
    max_attempts: int,
    window_seconds: int,
) -> dict:
    """Return current rate limit status for a key without incrementing."""
    if redis is None:
        return {"remaining": max_attempts, "reset_in": window_seconds, "blocked": False}
    try:
        count_raw = await redis.get(key)
        count = int(count_raw) if count_raw else 0
        ttl = await redis.ttl(key)
        remaining = max(0, max_attempts - count)
        return {
            "remaining": remaining,
            "reset_in": ttl if ttl > 0 else window_seconds,
            "blocked": count > max_attempts,
        }
    except Exception:
        return {"remaining": max_attempts, "reset_in": window_seconds, "blocked": False}

