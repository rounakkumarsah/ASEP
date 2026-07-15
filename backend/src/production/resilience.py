"""
ASEP — Production Resilience
"""

import asyncio
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class CircuitBreakerError(Exception):
    pass


class CircuitBreaker:
    """Defensive circuit breaker to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failures = 0
        self.state = "CLOSED"
        self._last_failure_time = 0.0
        
    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        now = asyncio.get_event_loop().time()
        if self.state == "OPEN":
            if now - self._last_failure_time > self.recovery_timeout_sec:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN.")
                
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as exc:
            self.failures += 1
            self._last_failure_time = now
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker tripped OPEN after {self.failures} failures.")
            raise exc


class RetryPolicy:
    """Async retry policy with exponential backoff."""
    
    @staticmethod
    async def execute(func: Callable[..., Any], max_attempts: int = 3, base_delay: float = 1.0, *args: Any, **kwargs: Any) -> Any:
        attempt = 1
        while attempt <= max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_attempts:
                    raise exc
                delay = base_delay * (2 ** (attempt - 1))
                logger.debug(f"Action failed, retrying in {delay}s (Attempt {attempt}/{max_attempts})")
                await asyncio.sleep(delay)
                attempt += 1
