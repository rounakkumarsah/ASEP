"""Utilities for safe async task execution.

Provides helpers that wrap coroutines in asyncio tasks with proper error
handling so that fire-and-forget side-effects (e.g. memory hooks) never
crash the main execution path.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


def safe_fire_and_forget(coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
    """Schedule *coro* as a background asyncio task and return it.

    Any exception raised inside *coro* is logged at WARNING level and
    silently swallowed so it never propagates to the caller.

    Args:
        coro: An unawaited coroutine to run in the background.

    Returns:
        The :class:`asyncio.Task` wrapping the coroutine, already
        scheduled on the running event loop.
    """

    async def _guarded() -> None:
        try:
            await coro
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "safe_fire_and_forget: background task raised an exception: %s",
                exc,
                exc_info=True,
            )

    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(_guarded())
    except RuntimeError:
        # No running event loop — caller is in a sync context. Fall back to
        # asyncio.run() on the guarded wrapper so the coroutine is still
        # executed (blocking) rather than silently dropped.
        logger.warning(
            "safe_fire_and_forget: no running event loop; executing coroutine synchronously."
        )

        async def _run_sync() -> None:
            await _guarded()

        # Return a completed task-like wrapper; asyncio.run blocks here.
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_run_sync())
        finally:
            loop.close()

        # Return a dummy already-done future for interface compatibility.
        fut: asyncio.Future[Any] = asyncio.Future()
        fut.set_result(None)
        return fut  # type: ignore[return-value]
