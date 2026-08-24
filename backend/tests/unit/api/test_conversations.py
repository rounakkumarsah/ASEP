"""
Unit tests for POST /conversations/run, POST /conversations/{thread_id}/resume,
GET /conversations/{thread_id}/state, and GET /conversations/{thread_id}/history.

All LangGraph runtime calls are mocked so no real checkpointer or DB is needed.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.auth.dependencies import get_current_user
from src.db.models.user import User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_user() -> User:
    return User(
        id=uuid.uuid4(),
        username="dev",
        email="dev@test.com",
        role="admin",
        status="active",
        is_active=True,
    )


@pytest.fixture()
def test_client(mock_user: User) -> TestClient:
    """Return a TestClient with the current_user dependency overridden."""
    app = create_app()

    async def _mock_current_user() -> User:
        return mock_user

    app.dependency_overrides[get_current_user] = _mock_current_user
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot(
    values: dict[str, Any] | None = None,
    next_nodes: tuple[str, ...] = (),
) -> MagicMock:
    """Build a minimal fake LangGraph StateSnapshot."""
    snap = MagicMock()
    snap.values = values or {
        "status": "running",
        "run_id": str(uuid.uuid4()),
        "human_input": None,
        "messages": [],
        "variables": {},
    }
    snap.next = next_nodes
    snap.config = {"configurable": {"checkpoint_id": str(uuid.uuid4())}}
    snap.metadata = {"step": 1, "created_at": "2026-01-01T00:00:00Z"}
    return snap


async def _noop_stream() -> AsyncGenerator[dict[str, Any], None]:
    yield {"start": {"status": "started"}}
    yield {"process": {"status": "running"}}


# ---------------------------------------------------------------------------
# Tests — POST /conversations/run
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_run_streams_sse(test_client: TestClient):
    """POST /run should return a 200 text/event-stream with [DONE] terminator."""
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.execute_run = MagicMock(return_value=_noop_stream())
        mock_rt.return_value = runtime

        resp = test_client.post(
            "/api/v1/conversations/run",
            json={"goal": "Summarise Q4 financials", "thread_id": thread_id},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "data:" in body
    assert "[DONE]" in body
    assert thread_id in body


@pytest.mark.asyncio
async def test_start_run_generates_thread_id_when_omitted(test_client: TestClient):
    """POST /run without thread_id should auto-assign one (visible in X-Thread-Id header)."""
    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.execute_run = MagicMock(return_value=_noop_stream())
        mock_rt.return_value = runtime

        resp = test_client.post(
            "/api/v1/conversations/run",
            json={"goal": "Deploy staging environment"},
        )

    assert resp.status_code == 200
    assert "X-Thread-Id" in resp.headers
    # Validate it is a UUID
    uuid.UUID(resp.headers["X-Thread-Id"])


@pytest.mark.asyncio
async def test_start_run_requires_auth():
    """POST /run without a user should return 401."""
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/v1/conversations/run",
        json={"goal": "Do something"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — POST /conversations/{thread_id}/resume
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_run_streams_sse(test_client: TestClient):
    """POST /{thread_id}/resume should resume and stream updates."""
    thread_id = str(uuid.uuid4())

    async def _resume_stream() -> AsyncGenerator[dict, None]:
        yield {"validate": {"human_input": "approve"}}
        yield {"end": {"status": "completed"}}

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        # get_state returns a non-empty dict so the 404 guard passes
        runtime.get_state = AsyncMock(return_value={"status": "paused"})
        runtime.resume_run = MagicMock(return_value=_resume_stream())
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/{thread_id}/resume",
            json={"decision": "approve"},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "[DONE]" in body
    assert "approve" in body


@pytest.mark.asyncio
async def test_resume_run_404_when_thread_missing(test_client: TestClient):
    """POST /{thread_id}/resume on an unknown thread should return 404."""
    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.get_state = AsyncMock(return_value=None)
        mock_rt.return_value = runtime

        resp = test_client.post(
            "/api/v1/conversations/nonexistent-thread/resume",
            json={"decision": "approve"},
        )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — GET /conversations/{thread_id}/state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_state_returns_snapshot(test_client: TestClient):
    """GET /{thread_id}/state should return a ThreadStateResponse."""
    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    snapshot = _make_snapshot(
        values={
            "status": "paused",
            "run_id": run_id,
            "human_input": None,
            "messages": [],
            "variables": {},
        },
        next_nodes=("validate",),
    )

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.graph = MagicMock()
        runtime.graph.aget_state = AsyncMock(return_value=snapshot)
        mock_rt.return_value = runtime

        resp = test_client.get(f"/api/v1/conversations/{thread_id}/state")

    assert resp.status_code == 200
    data = resp.json()
    assert data["thread_id"] == thread_id
    assert data["status"] == "paused"
    assert data["is_paused"] is True
    assert "validate" in data["next"]
    assert data["run_id"] == run_id


@pytest.mark.asyncio
async def test_get_state_404_on_missing_thread(test_client: TestClient):
    """GET /{thread_id}/state should return 404 when no snapshot exists."""
    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.graph = MagicMock()
        runtime.graph.aget_state = AsyncMock(return_value=None)
        mock_rt.return_value = runtime

        resp = test_client.get("/api/v1/conversations/ghost-thread/state")

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — GET /conversations/{thread_id}/history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_history_returns_entries(test_client: TestClient):
    """GET /{thread_id}/history should return a list of checkpoint snapshots."""
    thread_id = str(uuid.uuid4())

    async def _history_gen(*_args, **_kwargs):
        for i in range(3):
            snap = _make_snapshot(next_nodes=())
            snap.metadata = {"step": i, "created_at": "2026-01-01T00:00:00Z"}
            yield snap

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.graph = MagicMock()
        runtime.graph.aget_state_history = _history_gen
        mock_rt.return_value = runtime

        resp = test_client.get(f"/api/v1/conversations/{thread_id}/history")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["step"] == 0


@pytest.mark.asyncio
async def test_get_history_404_when_empty(test_client: TestClient):
    """GET /{thread_id}/history returns 404 when no checkpoints exist."""

    async def _empty_gen(*_args, **_kwargs):
        return
        yield  # make it an async generator

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.graph = MagicMock()
        runtime.graph.aget_state_history = _empty_gen
        mock_rt.return_value = runtime

        resp = test_client.get("/api/v1/conversations/ghost-thread/history")

    assert resp.status_code == 404
