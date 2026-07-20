import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

async def check_rate_limit(
    redis: Redis,
    key: str,
    max_attempts: int,
    window_seconds: int,
) -> bool:
    """
    Basic Redis sliding window rate-limiter.
    Returns True if execution is allowed, False if blocked by rate limit.
    """
    try:
        current = await redis.get(key)
        if current is not None and int(current) >= max_attempts:
            logger.warning(f"Rate limit hit for key: {key}")
            return False

        # Multi/Exec pipeline to increment and expire safely
        async with redis.pipeline(transaction=True) as pipe:
            await pipe.incr(key)
            # Only set expire if it is a new key (or refresh window)
            await pipe.expire(key, window_seconds)
            await pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Error checking rate limit in Redis: {e}")
        # In case of Redis down, fail open so service doesn't break
        return True
