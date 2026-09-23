import uuid
import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from unittest.mock import MagicMock, patch, AsyncMock

async def _noop_stream():
    yield {}

@pytest.mark.asyncio
async def test_start_run_returns_run_id(test_client: TestClient):
    """POST /run should return 202 with run_id and thread_id."""
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.execute_step = AsyncMock(return_value={"status": "running", "events": [{"some": "event"}]})
        mock_rt.return_value = runtime

        resp = test_client.post(
            "/api/v1/conversations/run",
            json={"goal": "Summarise Q4 financials", "thread_id": thread_id},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert "run_id" in data
    assert data["thread_id"] == thread_id
    assert data["status"] == "running"
    assert "events" in data
    uuid.UUID(data["run_id"])


@pytest.mark.asyncio
async def test_start_run_generates_thread_id_when_omitted(test_client: TestClient):
    """POST /run without thread_id should auto-assign one (visible in response body)."""
    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.execute_step = AsyncMock(return_value={"status": "running", "events": []})
        mock_rt.return_value = runtime

        resp = test_client.post(
            "/api/v1/conversations/run",
            json={"goal": "Deploy staging environment"},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert "thread_id" in data
    uuid.UUID(data["thread_id"])


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


@pytest.mark.asyncio
async def test_run_step_returns_events(test_client: TestClient):
    """POST /run/{run_id}/step should execute next node and return events."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.execute_step = AsyncMock(return_value={"status": "done", "events": [{"final": "result"}]})
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert len(data["events"]) == 1
    assert data["events"][0] == {"final": "result"}

@pytest.mark.asyncio
async def test_resume_run(test_client: TestClient):
    """POST /run/{thread_id}/resume should accept string inputs"""
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        runtime.resume_run = MagicMock(return_value=_noop_stream())
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{thread_id}/resume",
            json={"feedback": "approve"},
        )
        assert resp.status_code == 200
        # Check standard HTTP responses
        assert resp.json() == {"status": "ok", "message": "Resumed execution"}

