"""
ASEP — Unit Tests for Phase P3
===============================
Tests document parsing, image extraction, Redis rate limiting, GraphRAG semantic caching,
and Razorpay webhook signature verification under zero-cost constraints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.agents.research_swarm import ResearchSwarm
from src.production.graphrag_engine import LocalGraphRAGEngine
from src.production.ingestion_service import UniversalIngestionService
from src.production.monetization import FreemiumRateLimiter, RazorpayMonetizationManager


@pytest.mark.asyncio
async def test_universal_document_parsing():
    ingest = UniversalIngestionService()

    # Plain text parsing
    text = await ingest.parse_document(b"Hello ASEP Document", "sample.txt")
    assert "Hello ASEP Document" in text

    # CSV parsing
    csv_bytes = b"id,name\n1,ASEP\n2,GraphRAG"
    csv_text = await ingest.parse_document(csv_bytes, "data.csv")
    assert "ASEP" in csv_text


@pytest.mark.asyncio
async def test_image_screenshot_extraction():
    ingest = UniversalIngestionService(gemini_api_key=None)
    img_bytes = b"\x89PNG\r\n\x1a\nFakeImageBytes"

    extracted = await ingest.parse_image_screenshot(img_bytes, "error.png")
    assert "Simulated Vision Extraction" in extracted or "Extraction" in extracted


@pytest.mark.asyncio
async def test_freemium_rate_limiter():
    limiter = FreemiumRateLimiter(free_daily_limit=2)

    with patch("src.production.monetization.get_redis_client") as mock_redis:
        redis_mock = AsyncMock()
        redis_mock.incr.side_effect = [1, 2, 3]
        mock_redis.return_value = redis_mock

        res1 = await limiter.check_rate_limit("user_100", tier="free")
        assert res1.allowed is True

        res2 = await limiter.check_rate_limit("user_100", tier="free")
        assert res2.allowed is True

        res3 = await limiter.check_rate_limit("user_100", tier="free")
        assert res3.allowed is False
        assert res3.remaining_queries == 0


@pytest.mark.asyncio
async def test_razorpay_monetization_manager():
    mgr = RazorpayMonetizationManager()

    # Checkout parameter generation
    order = mgr.generate_checkout_url("user_abc", plan_tier="pro")
    assert "order_user_abc" in order["order_id"]
    assert order["amount"] == 299900

    # Webhook signature verification when secret is None or configured
    with patch.object(mgr.settings, "RAZORPAY_WEBHOOK_SECRET", None):
        is_valid = mgr.verify_webhook_signature(b"{}", "mock_sig")
        assert is_valid is True


@pytest.mark.asyncio
async def test_graphrag_semantic_cache():
    engine = LocalGraphRAGEngine()

    with patch("src.production.graphrag_engine.get_redis_client") as mock_redis:
        redis_mock = AsyncMock()
        redis_mock.get.return_value = "Cached Code Fix Solution"
        mock_redis.return_value = redis_mock

        hit = await engine.get_semantic_cache("TypeError in main.py line 10")
        assert hit.is_hit is True
        assert hit.cached_solution == "Cached Code Fix Solution"


@pytest.mark.asyncio
async def test_research_swarm_execution():
    swarm = ResearchSwarm()
    with patch("src.agents.research_swarm.get_redis_client") as mock_redis:
        redis_mock = AsyncMock()
        redis_mock.incr.return_value = 1
        mock_redis.return_value = redis_mock

        report = await swarm.run_general_research("GraphRAG architecture")
        assert "GraphRAG architecture" in report.topic_or_issue
        assert "Comprehensive Deep Research Report" in report.summary

