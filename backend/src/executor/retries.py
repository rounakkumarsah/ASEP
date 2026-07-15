"""
ASEP — Retry Policy with Exponential Backoff
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configurable retry behaviour with exponential backoff."""
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0
    timeout_seconds: float | None = 30.0


async def with_retry(
    coro_factory: Callable[[], Coroutine[Any, Any, T]],
    policy: RetryPolicy,
    task_id: str = "unknown",
) -> tuple[T | None, str | None, int]:
    """Execute a coroutine factory with exponential backoff retries and optional timeout.

    Args:
        coro_factory: A zero-argument callable returning a fresh coroutine on each call.
        policy:       The retry configuration to apply.
        task_id:      Task identifier for logging.

    Returns:
        A 3-tuple of (result, error_message, attempts_made).
        On success: (result, None, n).  On final failure: (None, error_msg, n).
    """
    delay = policy.initial_delay_seconds
    last_error: str | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            logger.debug(f"[{task_id}] Attempt {attempt}/{policy.max_attempts}")

            coro = coro_factory()
            if policy.timeout_seconds is not None:
                result = await asyncio.wait_for(coro, timeout=policy.timeout_seconds)
            else:
                result = await coro

            logger.info(f"[{task_id}] Succeeded on attempt {attempt}")
            return result, None, attempt

        except asyncio.TimeoutError:
            last_error = f"Timed out after {policy.timeout_seconds}s on attempt {attempt}"
            logger.warning(f"[{task_id}] {last_error}")
            # Timeout is not retried — treat as final failure immediately
            return None, last_error, attempt

        except asyncio.CancelledError:
            # Propagate cancellation — do not retry
            raise

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(f"[{task_id}] Attempt {attempt} failed: {last_error}")

            if attempt < policy.max_attempts:
                sleep_time = min(delay, policy.max_delay_seconds)
                logger.debug(f"[{task_id}] Retrying in {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                delay *= policy.backoff_multiplier

    return None, last_error, policy.max_attempts
