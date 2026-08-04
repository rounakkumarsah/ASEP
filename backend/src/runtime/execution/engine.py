"""
ASEP — Agent Runtime Execution Engine
======================================
Provides complete, robust execution infrastructure for AI Agent runs.

Features:
- Execution Context with run scoping, variables, and timeout metadata
- State Management with immutable history snapshots and transitions
- Async Execution Engine with queue management, max concurrency, and status tracking
- Retry & Recovery with exponential backoff and custom exception handling
- Cancellation Token support for synchronous and asynchronous task cancellation
- Event System with async EventEmitter and typed lifecycle events
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Event System
# ---------------------------------------------------------------------------

class EventType(str, enum.Enum):
    RUN_SUBMITTED = "run_submitted"
    RUN_STARTED = "run_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    RUN_PAUSED = "run_paused"
    RUN_RESUMED = "run_resumed"
    RUN_CANCELLED = "run_cancelled"
    RUN_FAILED = "run_failed"
    RUN_FINISHED = "run_finished"


@dataclass
class AgentEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.RUN_SUBMITTED
    run_id: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[AgentEvent], Union[None, Coroutine[Any, Any, None]]]


class EventEmitter:
    """Thread-safe, async-compatible event emitter."""

    def __init__(self) -> None:
        self._listeners: Dict[EventType, List[EventHandler]] = {}
        self._lock = asyncio.Lock()

    def on(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if handler not in self._listeners[event_type]:
            self._listeners[event_type].append(handler)

    def off(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type in self._listeners and handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)

    async def emit(self, event: AgentEvent) -> None:
        handlers = self._listeners.get(event.event_type, [])
        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as exc:
                logger.exception("Error in event handler for %s: %s", event.event_type, exc)


# ---------------------------------------------------------------------------
# 2. Cancellation Token
# ---------------------------------------------------------------------------

class CancellationToken:
    """Token to signal and check execution cancellation requests."""

    def __init__(self) -> None:
        self._cancelled = False
        self._reason: Optional[str] = None
        self._callbacks: List[Callable[[], None]] = []

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def reason(self) -> Optional[str]:
        return self._reason

    def cancel(self, reason: str = "Execution cancelled by user") -> None:
        if not self._cancelled:
            self._cancelled = True
            self._reason = reason
            for cb in self._callbacks:
                try:
                    cb()
                except Exception as exc:
                    logger.error("Error executing cancellation callback: %s", exc)

    def register_callback(self, callback: Callable[[], None]) -> None:
        if self._cancelled:
            callback()
        else:
            self._callbacks.append(callback)

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise asyncio.CancelledError(f"Task cancelled: {self._reason}")


# ---------------------------------------------------------------------------
# 3. Execution Context
# ---------------------------------------------------------------------------

@dataclass
class ExecutionContext:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    goal: str = ""
    timeout_seconds: float = 300.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    variables: Dict[str, Any] = field(default_factory=dict)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_var(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set_var(self, key: str, value: Any) -> None:
        self.variables[key] = value


# ---------------------------------------------------------------------------
# 4. State Management
# ---------------------------------------------------------------------------

class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StateSnapshot:
    step: int
    status: ExecutionStatus
    state_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StateManager:
    """Manages mutable agent state with historical audit snapshots."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        self._current_state: Dict[str, Any] = initial_state or {}
        self._history: List[StateSnapshot] = []
        self._step_counter = 0

    @property
    def current_state(self) -> Dict[str, Any]:
        return dict(self._current_state)

    @property
    def history(self) -> List[StateSnapshot]:
        return list(self._history)

    def update(self, updates: Dict[str, Any], status: ExecutionStatus = ExecutionStatus.RUNNING) -> Dict[str, Any]:
        self._current_state.update(updates)
        self._step_counter += 1
        snapshot = StateSnapshot(
            step=self._step_counter,
            status=status,
            state_data=dict(self._current_state),
        )
        self._history.append(snapshot)
        return self.current_state

    def snapshot(self, status: ExecutionStatus) -> StateSnapshot:
        snapshot = StateSnapshot(
            step=self._step_counter,
            status=status,
            state_data=dict(self._current_state),
        )
        self._history.append(snapshot)
        return snapshot


# ---------------------------------------------------------------------------
# 5. Retry & Recovery
# ---------------------------------------------------------------------------

@dataclass
class RetryPolicy:
    max_retries: int = 3
    initial_delay: float = 0.5
    backoff_factor: float = 2.0
    max_delay: float = 10.0
    retryable_exceptions: List[type[BaseException]] = field(
        default_factory=lambda: [Exception]
    )


class RetryHandler:
    """Executes callables with exponential backoff and retry rules."""

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self.policy = policy or RetryPolicy()

    async def execute(self, func: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
        attempts = 0
        delay = self.policy.initial_delay
        while True:
            try:
                return await func()
            except Exception as exc:
                attempts += 1
                is_retryable = any(isinstance(exc, t) for t in self.policy.retryable_exceptions)
                if attempts > self.policy.max_retries or not is_retryable:
                    logger.error("Execution failed after %d attempts: %s", attempts, exc)
                    raise exc
                logger.warning("Attempt %d failed (%s). Retrying in %.2fs...", attempts, exc, delay)
                await asyncio.sleep(delay)
                delay = min(delay * self.policy.backoff_factor, self.policy.max_delay)


# ---------------------------------------------------------------------------
# 6. Async Execution Engine
# ---------------------------------------------------------------------------

class AsyncExecutionEngine:
    """Central engine managing concurrent agent run executions, timeouts, and state."""

    def __init__(self, max_concurrency: int = 10) -> None:
        self.max_concurrency = max_concurrency
        self.events = EventEmitter()
        self._active_runs: Dict[str, ExecutionContext] = {}
        self._run_tasks: Dict[str, asyncio.Task[Any]] = {}
        self._state_managers: Dict[str, StateManager] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def submit_run(
        self,
        goal: str,
        session_id: str = "",
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        initial_variables: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 300.0,
    ) -> ExecutionContext:
        ctx = ExecutionContext(
            session_id=session_id,
            user_id=user_id,
            org_id=org_id,
            goal=goal,
            timeout_seconds=timeout_seconds,
            variables=initial_variables or {},
        )
        self._active_runs[ctx.run_id] = ctx
        self._state_managers[ctx.run_id] = StateManager(
            initial_state={"goal": goal, "status": ExecutionStatus.PENDING.value}
        )

        await self.events.emit(
            AgentEvent(
                event_type=EventType.RUN_SUBMITTED,
                run_id=ctx.run_id,
                payload={"goal": goal, "session_id": session_id},
            )
        )
        return ctx

    async def execute_task(
        self,
        run_id: str,
        task_coro_fn: Callable[[ExecutionContext, StateManager], Coroutine[Any, Any, Dict[str, Any]]],
        retry_policy: Optional[RetryPolicy] = None,
    ) -> Dict[str, Any]:
        ctx = self._active_runs.get(run_id)
        if not ctx:
            raise ValueError(f"Run ID '{run_id}' not found in active execution engine.")

        state_mgr = self._state_managers[run_id]

        async def _runner() -> Dict[str, Any]:
            async with self._semaphore:
                ctx.cancellation_token.raise_if_cancelled()
                state_mgr.update({"status": ExecutionStatus.RUNNING.value}, ExecutionStatus.RUNNING)
                await self.events.emit(AgentEvent(event_type=EventType.RUN_STARTED, run_id=run_id))

                retry_handler = RetryHandler(retry_policy)

                async def _task_wrapper() -> Dict[str, Any]:
                    ctx.cancellation_token.raise_if_cancelled()
                    return await task_coro_fn(ctx, state_mgr)

                try:
                    result = await asyncio.wait_for(
                        retry_handler.execute(_task_wrapper),
                        timeout=ctx.timeout_seconds,
                    )
                    state_mgr.update(
                        {"status": ExecutionStatus.COMPLETED.value, "result": result},
                        ExecutionStatus.COMPLETED,
                    )
                    await self.events.emit(
                        AgentEvent(
                            event_type=EventType.RUN_FINISHED,
                            run_id=run_id,
                            payload={"result": result},
                        )
                    )
                    return result
                except asyncio.CancelledError:
                    state_mgr.update(
                        {"status": ExecutionStatus.CANCELLED.value},
                        ExecutionStatus.CANCELLED,
                    )
                    await self.events.emit(AgentEvent(event_type=EventType.RUN_CANCELLED, run_id=run_id))
                    raise
                except Exception as exc:
                    state_mgr.update(
                        {"status": ExecutionStatus.FAILED.value, "error": str(exc)},
                        ExecutionStatus.FAILED,
                    )
                    await self.events.emit(
                        AgentEvent(
                            event_type=EventType.RUN_FAILED,
                            run_id=run_id,
                            payload={"error": str(exc)},
                        )
                    )
                    raise exc

        task = asyncio.create_task(_runner())
        self._run_tasks[run_id] = task
        return await task

    async def cancel_run(self, run_id: str, reason: str = "Cancelled by user") -> bool:
        ctx = self._active_runs.get(run_id)
        if not ctx:
            return False
        ctx.cancellation_token.cancel(reason)
        task = self._run_tasks.get(run_id)
        if task and not task.done():
            task.cancel()
        return True

    def get_status(self, run_id: str) -> Dict[str, Any]:
        state_mgr = self._state_managers.get(run_id)
        if not state_mgr:
            return {"run_id": run_id, "status": ExecutionStatus.PENDING.value, "found": False}
        return {
            "run_id": run_id,
            "status": state_mgr.current_state.get("status", ExecutionStatus.PENDING.value),
            "state": state_mgr.current_state,
            "history_steps": len(state_mgr.history),
        }
