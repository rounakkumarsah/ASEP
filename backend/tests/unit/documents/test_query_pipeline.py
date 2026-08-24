"""
ASEP — Unit Tests for Retrieval Pipeline
"""

from unittest.mock import AsyncMock

import pytest

from src.documents.hybrid_retrieval import HybridSearchResult
from src.documents.query_pipeline import QueryIntentAnalyzer, RetrievalPipeline, RetrievalStrategy


def test_query_intent_analyzer():
    analyzer = QueryIntentAnalyzer()

    strat1 = analyzer.analyze_intent("How is user authentication connected to JWT tokens?")
    assert strat1 in [RetrievalStrategy.HYBRID, RetrievalStrategy.MULTI_HOP_GRAPH]

    strat2 = analyzer.analyze_intent("What is the PostgreSQL connection string?")
    assert strat2 == RetrievalStrategy.HYBRID


@pytest.mark.asyncio
async def test_retrieval_pipeline_execution():
    mock_hybrid = AsyncMock()
    mock_hybrid.search_hybrid.return_value = [
        HybridSearchResult(
            chunk_id="c1",
            score=0.95,
            text="JWT token verification logic",
            document_id="doc1",
            filename="auth.py",
        )
    ]

    pipeline = RetrievalPipeline(hybrid_pipeline=mock_hybrid)
    out = await pipeline.execute_retrieval("Explain auth architecture")

    assert out.query == "Explain auth architecture"
    assert len(out.citations) == 1
    assert out.citations[0].filename == "auth.py"
    assert out.latency_ms >= 0.0
