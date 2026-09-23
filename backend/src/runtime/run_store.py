"""
ASEP — Run Event Store
=======================
In-memory buffer that accumulates LangGraph streaming events per ``run_id``.

On Vercel serverless, SSE (Server-Sent Events) are fully buffered and the
30-second function timeout kills the connection before the agent completes.
The solution is to:

1. Accept the run request and immediately return ``{run_id, status: queued}``.
2. Execute the LangGraph agent as a background ``asyncio.Task``.
3. Push events into this in-memory store as they arrive.
4. Expose a ``GET /conversations/run/{run_id}/status`` polling endpoint
   that returns batched events and the current status.

Events older than ``MAX_AGE_SECONDS`` are evicted to prevent memory growth.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("opensep.run_store")

MAX_AGE_SECONDS = 3600  # 1 hour


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class RunState:
    run_id: str
    thread_id: str
    status: RunStatus = RunStatus.QUEUED
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    # Cursor: how many events the client has already consumed
    # Not used by the server — clients pass their own cursor in GET params.


_store: dict[str, RunState] = {}
_lock = asyncio.Lock()


async def create_run(run_id: str, thread_id: str) -> RunState:
    """Register a new run in the store (status = QUEUED)."""
    state = RunState(run_id=run_id, thread_id=thread_id)
    async with _lock:
        _store[run_id] = state
        _evict_old_runs()
    return state


async def set_status(run_id: str, status: RunStatus, error: str | None = None) -> None:
    """Update run status (called from the background task)."""
    async with _lock:
        if run_id in _store:
            _store[run_id].status = status
            _store[run_id].updated_at = time.time()
            if error:
                _store[run_id].error = error


async def append_event(run_id: str, event: dict[str, Any]) -> None:
    """Append a streaming event to the run's event buffer."""
    async with _lock:
        if run_id in _store:
            _store[run_id].events.append(event)
            _store[run_id].updated_at = time.time()


async def get_run(run_id: str) -> RunState | None:
    """Return a shallow copy of the run state (safe for reading)."""
    async with _lock:
        state = _store.get(run_id)
        if state is None:
            return None
        # Return a copy so callers can read without holding the lock
        return RunState(
            run_id=state.run_id,
            thread_id=state.thread_id,
            status=state.status,
            events=list(state.events),
            error=state.error,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )


def _evict_old_runs() -> None:
    """Remove runs older than MAX_AGE_SECONDS (called while holding _lock)."""
    cutoff = time.time() - MAX_AGE_SECONDS
    expired = [rid for rid, s in _store.items() if s.created_at < cutoff]
    for rid in expired:
        del _store[rid]
        logger.debug("Evicted expired run %s from store", rid)
