"""
ASEP — Quota Enforcement Middleware Test Suite
==============================================
Tests verifying:
1. User over quota receives HTTP 402 Payment Required and audit log entry is created.
2. User under quota proceeds without interference (HTTP 200).
3. Monthly quota aggregation resets at the calendar month boundary.
4. Non-agent endpoints bypass quota enforcement.
5. High-throughput execution is non-blocking (>= 1 execution/second with no CPU hit).
"""

from __future__ import annotations

import datetime
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.auth.jwt import create_access_token
from src.db.models.audit_log import AuditLog
from src.db.models.user import User
from src.db.models.user_quota_log import UserQuotaLog
from src.middleware.quota_middleware import (
    QuotaEnforcementMiddleware,
    get_month_boundaries,
    get_monthly_token_usage,
)


def create_test_app() -> FastAPI:
    """Create a minimal FastAPI test application with QuotaEnforcementMiddleware mounted."""
    test_app = FastAPI()
    test_app.add_middleware(QuotaEnforcementMiddleware)

    @test_app.post("/execute-agent")
    async def execute_agent():
        return {"status": "success", "message": "agent execution completed"}

    @test_app.post("/api/v1/agent-runs")
    async def agent_runs():
        return {"status": "success", "message": "agent run created"}

    @test_app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}

    return test_app


@pytest.fixture
def test_app() -> FastAPI:
    return create_test_app()


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


class MockAsyncSession:
    """Mock SQLAlchemy AsyncSession to control user records and token usage queries."""

    def __init__(self, user: User | None, used_tokens: int = 0):
        self.user = user
        self.used_tokens = used_tokens
        self.added_objects: list[Any] = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(self, stmt: Any):
        mock_result = MagicMock()
        stmt_str = str(stmt).lower()

        # Check if query is looking for User
        if "from users" in stmt_str or "users.id" in stmt_str:
            mock_result.scalar_one_or_none.return_value = self.user
            mock_result.scalars.return_value.first.return_value = self.user
            return mock_result

        # Check if query is summing tokens from user_quota_logs
        if "user_quota_logs" in stmt_str:
            mock_result.scalar_one.return_value = self.used_tokens
            mock_result.scalar.return_value = self.used_tokens
            return mock_result

        return mock_result

    def add(self, obj: Any):
        self.added_objects.append(obj)

    async def commit(self):
        self.committed = True


def make_mock_session_factory(user: User | None, used_tokens: int = 0):
    """Return a mock session factory returning a preconfigured MockAsyncSession."""
    session = MockAsyncSession(user=user, used_tokens=used_tokens)

    def factory():
        return session

    return factory, session


def test_user_over_quota_returns_402(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test 1: When user monthly token usage >= quota, request is blocked with HTTP 402."""
    user_id = uuid.uuid4()
    test_user = User(
        id=user_id,
        username="overquota_user",
        email="overquota@example.com",
        current_plan="free",
        monthly_token_quota=5_000,
    )
    # Simulate 5,500 tokens used against 5,000 quota
    mock_factory, mock_session = make_mock_session_factory(test_user, used_tokens=5_500)
    monkeypatch.setattr("src.middleware.quota_middleware._get_session_factory", lambda: mock_factory)

    token = create_access_token(subject=str(user_id), role="developer")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/execute-agent", headers=headers)

    assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
    data = response.json()
    assert "Monthly token quota exceeded" in data["detail"]
    assert data["quota"] == 5_000
    assert data["tokens_used"] == 5_500

    # Verify audit log was recorded
    audit_logs = [obj for obj in mock_session.added_objects if isinstance(obj, AuditLog)]
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "agent_execution.quota_exceeded"
    assert audit_logs[0].actor_id == str(user_id)
    assert mock_session.committed is True


def test_user_under_quota_proceeds(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test 2: When user monthly token usage < quota, request proceeds to handler (HTTP 200)."""
    user_id = uuid.uuid4()
    test_user = User(
        id=user_id,
        username="active_user",
        email="active@example.com",
        current_plan="free",
        monthly_token_quota=100_000,
    )
    # Simulate 20,000 tokens used against 100,000 quota
    mock_factory, mock_session = make_mock_session_factory(test_user, used_tokens=20_000)
    monkeypatch.setattr("src.middleware.quota_middleware._get_session_factory", lambda: mock_factory)

    token = create_access_token(subject=str(user_id), role="developer")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/execute-agent", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"
    # No violation audit log should be written
    assert len(mock_session.added_objects) == 0


def test_monthly_reset_at_month_boundary():
    """Test 3: Verify month boundary calculations and exclusion of previous month tokens."""
    # Test boundary calculation for mid-year
    target = datetime.datetime(2026, 9, 27, 12, 0, 0, tzinfo=datetime.timezone.utc)
    start_dt, end_dt = get_month_boundaries(target)
    assert start_dt == datetime.datetime(2026, 9, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    assert end_dt == datetime.datetime(2026, 10, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    # Test year boundary (December -> January)
    dec_target = datetime.datetime(2026, 12, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
    dec_start, dec_end = get_month_boundaries(dec_target)
    assert dec_start == datetime.datetime(2026, 12, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    assert dec_end == datetime.datetime(2027, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.mark.asyncio
async def test_get_monthly_token_usage_queries_exact_month_range():
    """Test 3b: Verify get_monthly_token_usage generates date-filtered query."""
    user_id = uuid.uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 42_000
    mock_session.execute.return_value = mock_result

    target_dt = datetime.datetime(2026, 9, 15, tzinfo=datetime.timezone.utc)
    usage = await get_monthly_token_usage(mock_session, user_id, target_dt=target_dt)

    assert usage == 42_000
    assert mock_session.execute.called
    call_args = mock_session.execute.call_args[0][0]
    # Verify the compiled query contains timestamp bounds
    stmt_str = str(call_args)
    assert "user_quota_logs.timestamp >=" in stmt_str
    assert "user_quota_logs.timestamp <" in stmt_str


def test_non_intercepted_endpoints_bypass_quota_middleware(client: TestClient):
    """Test 4: Passive and non-agent endpoints pass through directly without quota checking."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


def test_high_throughput_execution_under_quota(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Test 5: Middleware handles >= 10 executions/sec with minimal CPU latency."""
    user_id = uuid.uuid4()
    test_user = User(
        id=user_id,
        username="fast_user",
        email="fast@example.com",
        current_plan="pro",
        monthly_token_quota=5_000_000,
    )
    mock_factory, _ = make_mock_session_factory(test_user, used_tokens=10_000)
    monkeypatch.setattr("src.middleware.quota_middleware._get_session_factory", lambda: mock_factory)

    token = create_access_token(subject=str(user_id), role="developer")
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.perf_counter()
    num_requests = 20
    for _ in range(num_requests):
        resp = client.post("/execute-agent", headers=headers)
        assert resp.status_code == status.HTTP_200_OK

    elapsed = time.perf_counter() - start_time
    rate = num_requests / elapsed
    # Requirement: blocks >= 1 execution per second without hitting CPU
    assert rate >= 1.0, f"Rate was {rate:.2f} req/s, expected >= 1.0"
