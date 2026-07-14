"""
ASEP — Distributed Lock Abstraction
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when a distributed lock cannot be acquired."""
    pass


@asynccontextmanager
async def distributed_lock(
    redis_client: Redis,
    lock_key: str,
    timeout_ms: int = 10000,
    retry_delay_ms: int = 100,
    max_retries: int = 50,
) -> AsyncGenerator[str, None]:
    """
    Acquire a distributed lock using Redis SET NX PX.
    
    Args:
        redis_client: The async Redis client.
        lock_key: The string key to lock on (e.g. 'lock:task:123').
        timeout_ms: How long the lock should be held before automatic expiry.
        retry_delay_ms: Milliseconds to wait between acquisition attempts.
        max_retries: Maximum number of attempts before raising an error.
        
    Yields:
        The unique token associated with this lock session.
        
    Raises:
        LockAcquisitionError: If the lock could not be acquired after max_retries.
    """
    token = str(uuid.uuid4())
    acquired = False
    
    for _ in range(max_retries):
        # SET key value NX PX timeout
        # NX = Only set if it does not exist
        # PX = Milliseconds expiration
        result = await redis_client.set(
            lock_key,
            token,
            nx=True,
            px=timeout_ms,
        )
        if result:
            acquired = True
            break
            
        await asyncio.sleep(retry_delay_ms / 1000.0)

    if not acquired:
        logger.warning(f"Failed to acquire lock '{lock_key}' after {max_retries} retries.")
        raise LockAcquisitionError(f"Could not acquire lock for key: {lock_key}")

    logger.debug(f"Acquired lock '{lock_key}' with token '{token}'")
    try:
        yield token
    finally:
        # We only delete the lock if our token matches to avoid releasing a lock
        # that expired and was subsequently acquired by someone else.
        
        # Redis Lua script to perform atomic verify-and-delete:
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        deleted = await redis_client.eval(script, 1, lock_key, token)
        if deleted:
            logger.debug(f"Released lock '{lock_key}' with token '{token}'")
        else:
            logger.warning(f"Failed to release lock '{lock_key}' - token mismatch or expired.")
