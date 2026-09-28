"""
ASEP — Background Task Queue & Decoupled Execution Test Suite
=============================================================
Tests verifying:
1. Enqueue returns {job_id, status_url} in < 500ms without blocking.
2. Status transitions correctly: pending -> running -> completed.
3. Result retrieval fetches generated code, review, tests, and final_output.
4. Automatic retry (2x) handles transient failures before terminal failure.
5. Concurrency limit enforces maximum 100 concurrent jobs per workspace (HTTP 429).
6. Long-running execution (>15s serverless timeout threshold) runs asynchronously without timing out.
7. Server restart resilience: pending/running jobs in DB are recovered upon boot.
8. 7-day retention auto-cleanup purges older completed jobs.
"""

from __future__ import annotations

import asyncio
import datetime
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.agents.supervisor import (
    cleanup_completed_jobs,
    execute_agent_background_task,
)
from src.db.models.queue_job import QueueJob
from src.routes.agents import router as agents_router
from src.services.task_queue_service import (
    BackgroundTaskQueue,
    ConcurrencyLimitExceededError,
)


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Sets up an in-memory SQLite database with StaticPool for complete isolation."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(QueueJob.__table__.create)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    monkeypatch.setattr("src.db.postgres._get_session_factory", lambda: session_maker)
    monkeypatch.setattr("src.services.task_queue_service._get_session_factory", lambda: session_maker)
    monkeypatch.setattr("src.agents.supervisor._get_session_factory", lambda: session_maker)

    yield session_maker
    await test_engine.dispose()


@pytest.fixture
async def test_queue():
    """Provides a BackgroundTaskQueue with an in-memory APScheduler instance."""
    scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})
    queue = BackgroundTaskQueue(scheduler=scheduler)
    queue.start()
    yield queue
    try:
        scheduler.remove_all_jobs()
    except Exception:
        pass
    queue.shutdown(wait=False)


@pytest.fixture
async def client(test_queue, monkeypatch):
    """FastAPI AsyncClient with mounted agents router."""
    monkeypatch.setattr("src.routes.agents.get_task_queue", lambda: test_queue)
    app = FastAPI()
    app.include_router(agents_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enqueue_response_time_under_500ms(test_queue, client):
    """Verifies that POST /execute-agent enqueues and responds in < 500ms."""
    payload = {
        "prompt": "Build a JWT authentication service",
        "workspace_id": "ws-speed-test",
    }

    start = time.perf_counter()
    response = await client.post("/execute-agent", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status_url"] == f"/jobs/{data['job_id']}"
    assert data["status"] == "pending"

    # Strict latency check: must return in < 500ms
    assert elapsed_ms < 500.0, f"Enqueue took {elapsed_ms:.2f}ms, exceeding 500ms limit"


@pytest.mark.asyncio
async def test_status_transitions_pending_to_running_to_completed(test_queue):
    """Verifies pending -> running -> completed status transitions and execution metrics."""
    user_id = uuid.uuid4()
    job_id = await test_queue.enqueue_agent_execution(
        user_id=user_id,
        spec={"prompt": "Generate mathematical utility functions"},
        workspace_id="ws-transition-test",
    )

    # 1. Enqueued status is 'pending'
    status = await test_queue.get_job_status(job_id)
    assert status == "pending"

    # Mock execute_graph returning successfully
    mock_final_state = {
        "code": "def add(a, b): return a + b",
        "review": "Clean and concise implementation.",
        "tests": "def test_add(): assert add(1, 2) == 3",
        "final_output": "Execution completed successfully.",
        "current_step": 3,
        "is_complete": True,
        "error": None,
        "messages": [{"sender": "code_writer", "tokens": 120}],
    }

    with patch("src.agents.supervisor.execute_graph", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_final_state
        await execute_agent_background_task(job_id)

    # 2. Completed status
    status = await test_queue.get_job_status(job_id)
    assert status == "completed"

    details = await test_queue.get_job_details(job_id)
    assert details is not None
    assert details["status"] == "completed"
    assert details["metrics"]["step_count"] == 3
    assert details["metrics"]["total_tokens"] == 120
    assert details["metrics"]["duration_ms"] >= 0
    assert details["completed_at"] is not None


@pytest.mark.asyncio
async def test_result_retrieval(test_queue, client):
    """Verifies fetch_result and GET /jobs/{job_id} retrieve code, review, and tests."""
    user_id = uuid.uuid4()
    job_id = await test_queue.enqueue_agent_execution(
        user_id=user_id,
        spec={"prompt": "Implement binary search algorithm"},
        workspace_id="ws-results-test",
    )

    expected_code = "def binary_search(arr, target):\n    pass"
    expected_review = "Looks solid."
    expected_tests = "def test_binary_search(): pass"

    with patch("src.agents.supervisor.execute_graph", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = {
            "code": expected_code,
            "review": expected_review,
            "tests": expected_tests,
            "final_output": "All done.",
            "current_step": 3,
            "is_complete": True,
            "error": None,
            "messages": [],
        }
        await execute_agent_background_task(job_id)

    # Fetch result via service
    result = await test_queue.fetch_result(job_id)
    assert result is not None
    assert result["code"] == expected_code
    assert result["review"] == expected_review
    assert result["tests"] == expected_tests

    # Fetch result via HTTP API
    res = await client.get(f"/jobs/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["result"]["code"] == expected_code
    assert data["result"]["review"] == expected_review
    assert data["result"]["tests"] == expected_tests


@pytest.mark.asyncio
async def test_error_handling_and_auto_retry_2x(test_queue):
    """Verifies job retries 2x upon failure before final failure status."""
    user_id = uuid.uuid4()
    job_id = await test_queue.enqueue_agent_execution(
        user_id=user_id,
        spec={"prompt": "Unstable job"},
        workspace_id="ws-retry-test",
    )

    with patch("src.agents.supervisor.execute_graph", new_callable=AsyncMock) as mock_exec:
        # First failure
        mock_exec.side_effect = RuntimeError("Temporary rate limit exceeded")
        res1 = await execute_agent_background_task(job_id)
        assert res1.get("status") == "retrying"

        details1 = await test_queue.get_job_details(job_id)
        assert details1["retry_count"] == 1
        assert details1["status"] == "pending"

        # Second failure
        res2 = await execute_agent_background_task(job_id)
        assert res2.get("status") == "retrying"

        details2 = await test_queue.get_job_details(job_id)
        assert details2["retry_count"] == 2
        assert details2["status"] == "pending"

        # Third failure: retries exhausted -> terminal failure
        res3 = await execute_agent_background_task(job_id)
        assert res3.get("status") == "failed"

        details3 = await test_queue.get_job_details(job_id)
        assert details3["status"] == "failed"
        assert details3["retry_count"] == 2
        assert "Temporary rate limit exceeded" in details3["error"]
        assert details3["completed_at"] is not None


@pytest.mark.asyncio
async def test_workspace_concurrency_limit_100(setup_test_db, test_queue, client):
    """Enforces maximum 100 concurrent jobs per workspace and returns 429 when exceeded."""
    session_factory = setup_test_db
    user_id = uuid.uuid4()
    workspace = "ws-concurrency-test"

    # Bulk insert 100 pending jobs for this workspace directly into DB
    async with session_factory() as session:
        bulk_jobs = [
            QueueJob(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=workspace,
                status="pending",
                spec={"prompt": f"job {i}"},
            )
            for i in range(100)
        ]
        session.add_all(bulk_jobs)
        await session.commit()

    # 101st enqueue directly on service should raise ConcurrencyLimitExceededError
    with pytest.raises(ConcurrencyLimitExceededError):
        await test_queue.enqueue_agent_execution(
            user_id=user_id,
            spec={"prompt": "overflow job"},
            workspace_id=workspace,
        )

    # 101st enqueue via HTTP returns 429
    res = await client.post("/execute-agent", json={"prompt": "overflow job", "workspace_id": workspace})
    assert res.status_code == 429
    assert "concurrent" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_mock_long_running_execution_over_15s_no_timeout(test_queue, client):
    """Simulates agent execution lasting > 15s (serverless timeout limit) and ensures no timeout."""
    payload = {
        "prompt": "Deep recursive architecture refactoring",
        "workspace_id": "ws-long-running",
    }

    # 1. HTTP enqueue returns immediately (< 500ms)
    start = time.perf_counter()
    response = await client.post("/execute-agent", json=payload)
    enqueue_elapsed = time.perf_counter() - start

    assert response.status_code == 202
    assert enqueue_elapsed < 0.5  # < 500ms
    job_id = response.json()["job_id"]

    # 2. Mock long-running supervisor execution simulating 16 seconds
    async def simulated_long_task(state):
        return {
            "code": "# Large refactored codebase",
            "review": "Approved",
            "tests": "def test_long(): assert True",
            "final_output": "Complex 16s task complete.",
            "current_step": 3,
            "is_complete": True,
            "error": None,
            "messages": [],
        }

    with patch("src.agents.supervisor.execute_graph", side_effect=simulated_long_task):
        with patch("time.perf_counter", side_effect=[100.0, 116.5]):  # 16.5s simulated duration
            await execute_agent_background_task(job_id)

    # 3. Status and results are correctly persisted
    details = await test_queue.get_job_details(job_id)
    assert details["status"] == "completed"
    assert details["metrics"]["duration_ms"] == 16500
    assert details["result"]["code"] == "# Large refactored codebase"


@pytest.mark.asyncio
async def test_survives_server_restart_recovery(setup_test_db, test_queue):
    """Verifies that pending and running jobs in the database are recovered upon server restart."""
    session_factory = setup_test_db
    user_id = uuid.uuid4()
    job1_id = uuid.uuid4()
    job2_id = uuid.uuid4()

    # Create interrupted jobs in database
    async with session_factory() as session:
        session.add(QueueJob(id=job1_id, user_id=user_id, workspace_id="ws-crash", status="pending", spec={}))
        session.add(QueueJob(id=job2_id, user_id=user_id, workspace_id="ws-crash", status="running", spec={}))
        await session.commit()

    # Server restart triggers recover_pending_jobs()
    with patch.object(test_queue.scheduler, "add_job", wraps=test_queue.scheduler.add_job) as mock_add:
        recovered = await test_queue.recover_pending_jobs()
        assert recovered == 2
        assert mock_add.call_count == 2
        # Verify job IDs were passed to scheduler
        called_job_ids = [call.kwargs.get("id") or call.args[2] if len(call.args) > 2 else call.kwargs.get("id") for call in mock_add.call_args_list]
        assert str(job1_id) in str(mock_add.call_args_list)
        assert str(job2_id) in str(mock_add.call_args_list)


@pytest.mark.asyncio
async def test_auto_cleanup_7_day_retention(setup_test_db, test_queue):
    """Verifies completed jobs older than 7 days are automatically purged."""
    session_factory = setup_test_db
    user_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)

    old_job_id = uuid.uuid4()
    recent_job_id = uuid.uuid4()

    async with session_factory() as session:
        # Job completed 8 days ago
        session.add(
            QueueJob(
                id=old_job_id,
                user_id=user_id,
                workspace_id="ws-cleanup",
                status="completed",
                spec={},
                completed_at=now - datetime.timedelta(days=8),
            )
        )
        # Job completed 2 days ago
        session.add(
            QueueJob(
                id=recent_job_id,
                user_id=user_id,
                workspace_id="ws-cleanup",
                status="completed",
                spec={},
                completed_at=now - datetime.timedelta(days=2),
            )
        )
        await session.commit()

    # Run cleanup with 7-day retention
    deleted_count = await cleanup_completed_jobs(retention_days=7)
    assert deleted_count == 1

    # Old job should be purged, recent job preserved
    assert await test_queue.get_job_status(old_job_id) is None
    assert await test_queue.get_job_status(recent_job_id) == "completed"
