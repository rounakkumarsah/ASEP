"""
ASEP — Unit Tests for Hybrid Retrieval Pipeline
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.documents.hybrid_retrieval import (
    HybridRetrievalPipeline,
    LexicalBM25Retriever,
    ReciprocalRankFusion,
)
from src.vector import VectorSearchResult



def test_reciprocal_rank_fusion():
    list1 = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    list2 = [{"chunk_id": "c2"}, {"chunk_id": "c3"}]

    fused = ReciprocalRankFusion.fuse([list1, list2], k=60)
    assert len(fused) == 3
    # c2 appears in both lists, should have highest score
    assert fused[0]["chunk_id"] == "c2"


def test_bm25_retriever():
    bm25 = LexicalBM25Retriever()
    docs = [
        {"chunk_id": "c1", "text": "GraphRAG is a hybrid retrieval architecture."},
        {"chunk_id": "c2", "text": "PostgreSQL database connection pool."},
    ]

    res = bm25.search_bm25("GraphRAG hybrid", docs)
    assert len(res) == 1
    assert res[0]["chunk_id"] == "c1"


@pytest.mark.asyncio
async def test_hybrid_retrieval_pipeline():
    mock_vector = AsyncMock()
    mock_vector.search.return_value = [
        VectorSearchResult(id="c1", score=0.9, payload={"text": "GraphRAG architecture", "document_id": "d1"}, version=1),
    ]

    mock_embedder = AsyncMock()
    mock_embedder.embed_query.return_value = [0.1, 0.2]

    pipeline = HybridRetrievalPipeline(
        vector_service=mock_vector,
        embedding_provider=mock_embedder,
        graph_service=None,
    )

    results = await pipeline.search_hybrid("GraphRAG query")
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    mock_vector.search.assert_called_once()
