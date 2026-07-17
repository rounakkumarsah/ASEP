from __future__ import annotations
import pytest
import os
import tempfile
from typing import Generator
from src.documents.chunking import ChunkingEngine
from src.documents.context_builder import ContextBuilder
from src.documents.evaluation import RAGEvaluator
from src.documents.embedding_service import RuntimeEmbeddingProvider
from src.documents.ingestion import IngestionService
from src.documents.retrieval import Retriever
from src.vector import VectorService
from src.vector.qdrant import get_qdrant_client
from src.graph import GraphService
from unittest.mock import MagicMock

def test_chunking_and_metadata():
    engine = ChunkingEngine(chunk_size=100, chunk_overlap=20)
    text = "Hello world. This is a simple document designed to test hierarchical parent-child recursive splitters."
    
    records = engine.chunk_document(
        document_id="doc-1",
        content=text,
        filename="test.txt",
        file_path="/path/test.txt",
    )
    
    assert len(records) > 1
    # Verify metadata fields are preserved
    for r in records:
        assert r.metadata.document_id == "doc-1"
        assert r.metadata.filename == "test.txt"
        assert r.parent_id is not None
        assert len(r.chunk_id) == 64  # Hex sha256 hash length

def test_context_builder_and_citations():
    builder = ContextBuilder(token_budget=100)
    
    chunks = [
        {"chunk_id": "c1", "text": "Apple computer designs consumer electronics.", "score": 0.9, "filename": "apple.txt", "document_id": "d1"},
        {"chunk_id": "c2", "text": "Orange is a citrus fruit rich in Vitamin C.", "score": 0.8, "filename": "orange.txt", "document_id": "d2"},
        {"chunk_id": "c1", "text": "Apple computer designs consumer electronics.", "score": 0.9, "filename": "apple.txt", "document_id": "d1"}, # Duplicate
    ]
    
    context, selected, citations = builder.build_context_and_citations(chunks)
    
    # Verify deduplication
    assert len(selected) == 2
    assert "Apple computer" in context
    assert "Orange" in context
    assert "[1] apple.txt" in citations
    assert "[2] orange.txt" in citations

def test_rag_evaluator_metrics():
    evaluator = RAGEvaluator()
    
    retrieved = ["doc1", "doc2", "doc3", "doc4"]
    ground_truth = ["doc2", "doc4"]
    
    recall = evaluator.compute_recall_at_k(retrieved, ground_truth, k=4)
    precision = evaluator.compute_precision_at_k(retrieved, ground_truth, k=4)
    mrr = evaluator.compute_mrr(retrieved, ground_truth)
    ndcg = evaluator.compute_ndcg(retrieved, ground_truth)
    
    assert recall == 1.0
    assert precision == 0.5
    assert mrr == 0.5  # doc2 is at index 1 (1-based position 2 -> 1/2)
    assert ndcg > 0.0

@pytest.mark.asyncio
async def test_incremental_indexing_and_cache():
    # Setup temporary file
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as f:
        f.write("Incremental indexing test content. ASEP platform RAG engine.")
        temp_path = f.name
        
    try:
        async def mock_async(*args, **kwargs):
            return MagicMock()
            
        async def mock_embed(texts):
            return [[0.1] * 128 for _ in texts]

        graph_service = MagicMock()
        graph_service.execute_write = mock_async
        
        vector_service = MagicMock()
        vector_service.batch_upsert = mock_async
        
        embedder = MagicMock()
        embedder.embed_documents = mock_embed
        
        service = IngestionService(
            graph_service=graph_service,
            vector_service=vector_service,
            embedding_provider=embedder
        )
        
        # Reset caching states for test predictability
        IngestionService._embedding_cache.clear()
        IngestionService._ingested_documents.clear()
        
        # Ingest 1st time
        res1 = await service.ingest_document(temp_path)
        assert res1["status"] == "ingested"
        
        # Ingest 2nd time (unchanged) -> Incremental index skip!
        res2 = await service.ingest_document(temp_path)
        assert res2["status"] == "unchanged"
        assert res2["chunks_ingested"] == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
