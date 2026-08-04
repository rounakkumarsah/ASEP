"""
ASEP — Unit Tests for Execution Engine
"""

import asyncio
import pytest
from src.runtime.execution.engine import (
    AgentEvent,
    AsyncExecutionEngine,
    CancellationToken,
    EventEmitter,
    ExecutionContext,
    ExecutionStatus,
    EventType,
    RetryHandler,
    RetryPolicy,
    StateManager,
)


@pytest.mark.asyncio
async def test_event_emitter():
    emitter = EventEmitter()
    received_events = []

    def handler(event: AgentEvent):
        received_events.append(event)

    emitter.on(EventType.RUN_STARTED, handler)
    event = AgentEvent(event_type=EventType.RUN_STARTED, run_id="r-123")
    await emitter.emit(event)

    assert len(received_events) == 1
    assert received_events[0].run_id == "r-123"


@pytest.mark.asyncio
async def test_cancellation_token():
    token = CancellationToken()
    assert not token.is_cancelled

    token.cancel("User cancelled test")
    assert token.is_cancelled
    assert token.reason == "User cancelled test"

    with pytest.raises(asyncio.CancelledError):
        token.raise_if_cancelled()


@pytest.mark.asyncio
async def test_state_manager():
    sm = StateManager(initial_state={"step": 0})
    sm.update({"step": 1, "data": "abc"}, status=ExecutionStatus.RUNNING)

    assert sm.current_state["step"] == 1
    assert len(sm.history) == 1
    assert sm.history[0].status == ExecutionStatus.RUNNING


@pytest.mark.asyncio
async def test_retry_handler_success_after_retry():
    policy = RetryPolicy(max_retries=2, initial_delay=0.01, backoff_factor=1.0)
    handler = RetryHandler(policy)

    attempts = 0

    async def flaky_fn():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Temporary glitch")
        return "success"

    res = await handler.execute(flaky_fn)
    assert res == "success"
    assert attempts == 2


@pytest.mark.asyncio
async def test_async_execution_engine_full_flow():
    engine = AsyncExecutionEngine(max_concurrency=2)
    ctx = await engine.submit_run(goal="Test goal", session_id="s-1")

    async def my_task(context, state_mgr):
        state_mgr.update({"output": "hello world"})
        return {"output": "hello world"}

    res = await engine.execute_task(ctx.run_id, my_task)
    assert res["output"] == "hello world"

    status = engine.get_status(ctx.run_id)
    assert status["status"] == ExecutionStatus.COMPLETED.value
