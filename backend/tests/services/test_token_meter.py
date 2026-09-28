"""
ASEP — Token Metering & Cost Attribution Test Suite
===================================================
Tests verifying:
1. Provider cost estimation accuracy for Groq, Gemini, OpenRouter, and fallback providers.
2. Granular token usage persistence with exact prompt, completion, and USD cost figures.
3. Monthly usage aggregation isolating per-provider token counts and total spend.
4. Calendar month boundary filtering and monthly resets.
5. Daily run rate extrapolation for end-of-month billing forecasts.
6. Sub-500ms dashboard endpoint query performance.
7. Multi-LLM supervisor routing integration with TokenMeter.
"""

from __future__ import annotations

import datetime
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.agents.supervisor import MultiLLMRouter
from src.ai_runtime.contracts import CompletionResponse, UsageInfo
from src.db.models.token_usage_log import TokenUsageLog
from src.routes.billing import router as billing_router
from src.services.token_meter import PROVIDER_RATES, TokenMeter


@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Sets up an in-memory SQLite database with StaticPool for test isolation."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(TokenUsageLog.__table__.create)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Monkeypatch the session factory in TokenMeter and supervisor
    monkeypatch.setattr("src.services.token_meter._get_session_factory", lambda: session_maker)
    monkeypatch.setattr("src.agents.supervisor._get_session_factory", lambda: session_maker)

    yield session_maker

    async with test_engine.begin() as conn:
        await conn.run_sync(TokenUsageLog.__table__.drop)
    await test_engine.dispose()


@pytest.fixture
def test_app() -> FastAPI:
    """Creates a minimal FastAPI app with billing_router mounted."""
    app = FastAPI()
    app.include_router(billing_router)
    return app


# ===========================================================================
# 1. Cost Estimation Unit Tests
# ===========================================================================

def test_estimate_cost_per_provider():
    """Verify cost estimation calculation per provider based on prompt and completion tokens."""
    # Groq ($0.59 / 1M prompt, $0.79 / 1M completion)
    groq_cost = TokenMeter.estimate_cost("groq", input_tokens=1000, output_tokens=2000)
    expected_groq = round((1000 * 0.59 / 1_000_000) + (2000 * 0.79 / 1_000_000), 6)
    assert groq_cost == expected_groq
    assert groq_cost == 0.00217

    # Gemini ($0.10 / 1M prompt, $0.40 / 1M completion)
    gemini_cost = TokenMeter.estimate_cost("gemini", input_tokens=10_000, output_tokens=5000)
    expected_gemini = round((10_000 * 0.10 / 1_000_000) + (5000 * 0.40 / 1_000_000), 6)
    assert gemini_cost == expected_gemini
    assert gemini_cost == 0.003

    # OpenRouter ($0.20 / 1M prompt, $0.20 / 1M completion)
    openrouter_cost = TokenMeter.estimate_cost("openrouter", input_tokens=5000, output_tokens=5000)
    expected_openrouter = round((5000 * 0.20 / 1_000_000) + (5000 * 0.20 / 1_000_000), 6)
    assert openrouter_cost == expected_openrouter
    assert openrouter_cost == 0.002

    # Case-insensitive provider name
    assert TokenMeter.estimate_cost("GROQ", 1000, 2000) == groq_cost
    assert TokenMeter.estimate_cost("Gemini ", 10_000, 5000) == gemini_cost

    # Fallback default provider
    fallback_cost = TokenMeter.estimate_cost("unknown-provider", 10_000, 10_000)
    assert fallback_cost > 0.0


# ===========================================================================
# 2. Token Meter Logging Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_log_usage_persists_accurate_counts_and_costs(setup_test_db):
    """Verify log_usage persists exact input/output tokens and computed cost to DB."""
    session_maker = setup_test_db
    user_id = uuid.uuid4()
    workspace_id = "ws-engineering"

    entry = await TokenMeter.log_usage(
        user_id=user_id,
        workspace_id=workspace_id,
        provider="groq",
        tokens_input=1200,
        tokens_output=800,
    )

    assert entry.id is not None
    assert entry.user_id == user_id
    assert entry.workspace_id == workspace_id
    assert entry.provider == "groq"
    assert entry.input_tokens == 1200
    assert entry.output_tokens == 800
    expected_cost = round((1200 * 0.59 / 1_000_000) + (800 * 0.79 / 1_000_000), 6)
    assert entry.cost_usd == expected_cost

    # Verify directly from DB query
    async with session_maker() as session:
        result = await session.execute(
            select(TokenUsageLog).where(TokenUsageLog.id == entry.id)
        )
        saved = result.scalar_one()
        assert saved.input_tokens == 1200
        assert saved.output_tokens == 800
        assert saved.cost_usd == expected_cost


# ===========================================================================
# 3. Monthly Usage Aggregation Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_monthly_usage_aggregation_and_breakdown(setup_test_db):
    """Verify monthly aggregation groups by provider and calculates total tokens and cost."""
    user_id = uuid.uuid4()
    current_month = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")

    # Log 2 Groq calls, 1 Gemini call, 1 OpenRouter call
    await TokenMeter.log_usage(user_id, "default", "groq", 1000, 500)      # Groq: 1500 tokens
    await TokenMeter.log_usage(user_id, "default", "groq", 2000, 1000)     # Groq: 3000 tokens
    await TokenMeter.log_usage(user_id, "default", "gemini", 5000, 2500)   # Gemini: 7500 tokens
    await TokenMeter.log_usage(user_id, "default", "openrouter", 4000, 2000)# OpenRouter: 6000 tokens

    usage = await TokenMeter.get_monthly_usage(user_id, month=current_month)

    assert usage["groq_tokens"] == 4500
    assert usage["gemini_tokens"] == 7500
    assert usage["openrouter_tokens"] == 6000
    assert usage["total_tokens"] == 18000
    assert usage["input_tokens"] == 12000
    assert usage["output_tokens"] == 6000
    assert usage["total_cost"] > 0.0
    assert usage["month"] == current_month
    assert str(usage["user_id"]) == str(user_id)
    assert "groq" in usage["breakdown"]
    assert "gemini" in usage["breakdown"]
    assert "openrouter" in usage["breakdown"]


# ===========================================================================
# 4. Monthly Reset & Boundary Filtering Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_monthly_boundary_filtering_and_resets(setup_test_db):
    """Verify queries for a specific month only return records from that month."""
    session_maker = setup_test_db
    user_id = uuid.uuid4()

    # Insert August record
    august_ts = datetime.datetime(2026, 8, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
    # Insert September record
    september_ts = datetime.datetime(2026, 9, 10, 10, 0, 0, tzinfo=datetime.timezone.utc)

    async with session_maker() as session:
        session.add_all([
            TokenUsageLog(
                user_id=user_id,
                workspace_id="default",
                provider="groq",
                input_tokens=1000,
                output_tokens=1000,
                cost_usd=0.00138,
                timestamp=august_ts,
            ),
            TokenUsageLog(
                user_id=user_id,
                workspace_id="default",
                provider="gemini",
                input_tokens=2000,
                output_tokens=2000,
                cost_usd=0.00100,
                timestamp=september_ts,
            ),
        ])
        await session.commit()

    # Query August
    aug_usage = await TokenMeter.get_monthly_usage(user_id, month="2026-08")
    assert aug_usage["groq_tokens"] == 2000
    assert aug_usage["gemini_tokens"] == 0
    assert aug_usage["total_tokens"] == 2000

    # Query September (verifying reset of August usage)
    sep_usage = await TokenMeter.get_monthly_usage(user_id, month="2026-09")
    assert sep_usage["groq_tokens"] == 0
    assert sep_usage["gemini_tokens"] == 4000
    assert sep_usage["total_tokens"] == 4000


# ===========================================================================
# 5. Billing Forecast Unit Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_monthly_forecast_run_rate():
    """Verify daily run rate extrapolation and projected month-end cost."""
    user_id = uuid.uuid4()

    # Mock get_monthly_usage to return $3.00 cost
    with patch.object(TokenMeter, "get_monthly_usage", new_callable=AsyncMock) as mock_usage:
        mock_usage.return_value = {
            "groq_tokens": 10000,
            "gemini_tokens": 20000,
            "openrouter_tokens": 5000,
            "total_cost": 3.00,
            "total_tokens": 35000,
            "month": "2026-09",
            "user_id": str(user_id),
        }

        forecast = await TokenMeter.get_monthly_forecast(user_id=user_id, month="2026-09")

        assert forecast["current_cost"] == 3.00
        assert forecast["days_in_month"] == 30
        assert forecast["projected_cost"] >= 0.0
        assert forecast["run_rate_per_day"] >= 0.0
        assert forecast["confidence"] in ["high", "medium", "low"]


# ===========================================================================
# 6. Dashboard Endpoints & Latency Tests (< 500ms)
# ===========================================================================

@pytest.mark.asyncio
async def test_dashboard_endpoints_sub_500ms(test_app: FastAPI, setup_test_db):
    """Verify GET /billing/usage and /billing/forecast execute in < 500ms."""
    user_id = uuid.uuid4()

    # Pre-populate 50 usage records
    for i in range(50):
        await TokenMeter.log_usage(
            user_id=user_id,
            workspace_id="test-ws",
            provider="groq" if i % 2 == 0 else "gemini",
            tokens_input=500,
            tokens_output=200,
        )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test /billing/usage response time
        start_time = time.perf_counter()
        resp_usage = await client.get(f"/billing/usage?user_id={user_id}")
        duration_usage = (time.perf_counter() - start_time) * 1000

        assert resp_usage.status_code == 200
        data_usage = resp_usage.json()
        assert data_usage["total_tokens"] == 50 * 700
        assert duration_usage < 500.0, f"/billing/usage took {duration_usage:.2f}ms (>500ms)"

        # 2. Test /billing/forecast response time
        start_time = time.perf_counter()
        resp_forecast = await client.get(f"/billing/forecast?user_id={user_id}")
        duration_forecast = (time.perf_counter() - start_time) * 1000

        assert resp_forecast.status_code == 200
        data_forecast = resp_forecast.json()
        assert data_forecast["current_cost"] > 0.0
        assert duration_forecast < 500.0, f"/billing/forecast took {duration_forecast:.2f}ms (>500ms)"


# ===========================================================================
# 7. Supervisor Integration Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_supervisor_integration_logs_to_token_meter(setup_test_db):
    """Verify MultiLLMRouter.execute_task triggers TokenMeter.log_usage with prompt & completion tokens."""
    session_maker = setup_test_db
    user_id = uuid.uuid4()

    mock_provider = AsyncMock()
    mock_provider.name = "groq"
    mock_provider.complete.return_value = CompletionResponse(
        text="print('hello')",
        usage=UsageInfo(
            total_tokens=500,
            prompt_tokens=200,
            completion_tokens=300,
        ),
        model="llama-3.3-70b-versatile",
        provider="groq",
    )

    mock_registry = MagicMock()
    mock_registry.providers = {"groq": mock_provider}

    router = MultiLLMRouter(registry=mock_registry)
    with patch.object(router, "get_vector_context", new_callable=AsyncMock) as mock_ctx, \
         patch.object(router, "log_quota_usage", new_callable=AsyncMock):
        mock_ctx.return_value = ""

        output, tokens, prov = await router.execute_task(
            task_type="code_writer",
            user_prompt="Write hello world",
            system_prompt="You are a coder",
            user_id=user_id,
            workspace_id="test-workspace",
        )

        assert tokens == 500
        assert prov == "groq"

    # Query token_usage_logs to verify record was logged
    async with session_maker() as session:
        result = await session.execute(
            select(TokenUsageLog).where(TokenUsageLog.user_id == user_id)
        )
        logs = result.scalars().all()
        assert len(logs) == 1
        log = logs[0]
        assert log.provider == "groq"
        assert log.input_tokens == 200
        assert log.output_tokens == 300
        assert log.workspace_id == "test-workspace"
        expected_cost = round((200 * 0.59 / 1_000_000) + (300 * 0.79 / 1_000_000), 6)
        assert log.cost_usd == expected_cost
