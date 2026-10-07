import uuid
import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from unittest.mock import MagicMock, patch, AsyncMock


from src.db.models.user import User
from src.auth.dependencies import get_current_user

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
    app = create_app()
    async def _mock_current_user() -> User:
        return mock_user
    app.dependency_overrides[get_current_user] = _mock_current_user
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()

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
async def test_run_step_initial_step_passes_goal_and_is_first(test_client: TestClient):
    """POST /run/{run_id}/step should identify is_first=True when graph state is empty and pass goal."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt, \
         patch("src.api.dependencies.get_uow_factory") as mock_uow_factory:

        runtime = MagicMock()
        runtime.graph.aget_state = AsyncMock(return_value=None)
        runtime.execute_step = AsyncMock(return_value={"status": "running", "events": []})
        mock_rt.return_value = runtime

        mock_uow = AsyncMock()
        mock_run_record = MagicMock()
        mock_run_record.goal = "Analyze market data"
        mock_uow.agent_runs.get = AsyncMock(return_value=mock_run_record)
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_uow
        mock_context.__aexit__.return_value = None
        mock_uow_factory.return_value = MagicMock(return_value=mock_context)

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id},
        )

        assert resp.status_code == 200
        runtime.execute_step.assert_called_once()
        call_kwargs = runtime.execute_step.call_args.kwargs
        assert call_kwargs["run_id"] == run_id
        assert call_kwargs["thread_id"] == thread_id
        assert call_kwargs["goal"] == "Analyze market data"
        assert call_kwargs["is_first"] is True


@pytest.mark.asyncio
async def test_run_step_subsequent_step_sets_is_first_false(test_client: TestClient):
    """POST /run/{run_id}/step should set is_first=False when graph state has values."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        mock_state = MagicMock()
        mock_state.values = {"messages": ["hello"]}
        runtime.graph.aget_state = AsyncMock(return_value=mock_state)
        runtime.execute_step = AsyncMock(return_value={"status": "done", "events": []})
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id},
        )

        assert resp.status_code == 200
        runtime.execute_step.assert_called_once()
        assert runtime.execute_step.call_args.kwargs["is_first"] is False


@pytest.mark.asyncio
async def test_run_step_max_steps_guard(test_client: TestClient):
    """POST /run/{run_id}/step with step_index > 40 should hit max_steps guard."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id, "step_index": 41},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "max_steps_exceeded"
    assert "Task too large — try breaking it down" in data["error"]
    runtime.execute_step.assert_not_called()


@pytest.mark.asyncio
async def test_run_step_max_duration_guard(test_client: TestClient):
    """POST /run/{run_id}/step exceeding max_duration should hit duration guard."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    from src.api.routers.conversations import _run_start_times
    import time
    # Set run start time to 500 seconds ago (limit is 480s)
    _run_start_times[run_id] = time.time() - 500.0

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt:
        runtime = MagicMock()
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id, "step_index": 1},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "max_steps_exceeded"
    assert "Task too large — try breaking it down" in data["error"]
    runtime.execute_step.assert_not_called()


@pytest.mark.asyncio
async def test_run_step_observability_logging(test_client: TestClient, caplog):
    """POST /run/{run_id}/step logs step observability at INFO level."""
    import logging
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    with patch("src.api.routers.conversations.get_langgraph_runtime") as mock_rt, \
         caplog.at_level(logging.INFO, logger="opensep.conversations"):
        runtime = MagicMock()
        runtime.graph.aget_state = AsyncMock(return_value=MagicMock(values={"messages": ["hi"]}))
        runtime.execute_step = AsyncMock(
            return_value={"status": "running", "events": [{"orchestrator": {}}], "nodes_executed": ["orchestrator"]}
        )
        mock_rt.return_value = runtime

        resp = test_client.post(
            f"/api/v1/conversations/run/{run_id}/step",
            json={"thread_id": thread_id, "step_index": 2},
        )

    assert resp.status_code == 200
    # Check that required observability keywords are logged at INFO level
    log_text = caplog.text
    assert f"POST /run/{run_id}/step observability" in log_text
    assert "step_index=2" in log_text
    assert "active_node_name=orchestrator" in log_text
    assert "llm_provider_response_status=" in log_text
    assert "tokens_used=" in log_text
    assert "tool_calls_made=" in log_text
    assert "finish_reason=" in log_text


@pytest.mark.asyncio
async def test_get_run_status_endpoint(test_client: TestClient):
    """GET /run/{run_id}/status returns the run status."""
    run_id = str(uuid.uuid4())

    with patch("src.api.dependencies.get_uow_factory") as mock_uow_factory:
        mock_uow = AsyncMock()
        mock_run_record = MagicMock()
        mock_run_record.status.value = "running"
        mock_run_record.error_message = None
        mock_uow.agent_runs.get = AsyncMock(return_value=mock_run_record)
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_uow
        mock_context.__aexit__.return_value = None
        mock_uow_factory.return_value = MagicMock(return_value=mock_context)

        resp = test_client.get(f"/api/v1/conversations/run/{run_id}/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["status"] == "running"
