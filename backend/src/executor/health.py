"""
ASEP — Executor Health Check
"""

import asyncio
import logging

from src.executor.dispatcher import HandlerRegistry
from src.executor.retries import RetryPolicy
from src.executor.scheduler import DependencyScheduler
from src.executor.worker import TaskWorker

logger = logging.getLogger(__name__)


async def executor_health_check() -> bool:
    """Verifies that executor components instantiate correctly and asyncio primitives work.

    Returns:
        True if core components initialise and basic retry logic executes, False otherwise.
    """
    try:
        # Verify HandlerRegistry
        registry = HandlerRegistry()
        assert registry.get("any_task_id") is not None

        # Verify RetryPolicy and with_retry on a trivially succeeding coroutine
        from src.executor.retries import with_retry
        policy = RetryPolicy(max_attempts=1, timeout_seconds=1.0)

        async def always_succeeds() -> dict:
            return {"ok": True}

        result, error, attempts = await with_retry(always_succeeds, policy, task_id="health")
        assert error is None and result == {"ok": True}

        # Verify asyncio.Event cooperative primitives
        event = asyncio.Event()
        event.set()
        assert event.is_set()
        event.clear()
        assert not event.is_set()

        logger.info("Executor health check passed")
        return True

    except Exception as e:
        logger.warning(f"Executor health check failed: {e}")
        return False
