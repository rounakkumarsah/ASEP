"""
ASEP — Unit Tests for Query Optimizer
"""

import pytest
from unittest.mock import AsyncMock
from src.documents.query_optimizer import QueryOptimizer


@pytest.mark.asyncio
async def test_query_optimizer_expansion():
    optimizer = QueryOptimizer()
    res = await optimizer.optimize_query("GraphRAG and Vector pipeline")

    assert res.original_query == "GraphRAG and Vector pipeline"
    assert len(res.expanded_queries) >= 2
    assert "GraphRAG" in res.sub_queries[0]
    assert res.is_cached is False


@pytest.mark.asyncio
async def test_query_optimizer_cache_hit():
    mock_cache = AsyncMock()
    mock_cache.get.return_value = "Cached GraphRAG Output"

    optimizer = QueryOptimizer(cache_client=mock_cache)
    res = await optimizer.optimize_query("GraphRAG query")

    assert res.is_cached is True
    assert res.cached_response == {"result": "Cached GraphRAG Output"}
    mock_cache.get.assert_called_once()
