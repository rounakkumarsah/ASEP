import pytest
import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from src.documents.ingestion import IngestionService
from src.vector import VectorRecord

@pytest.fixture
def mock_dependencies():
    graph_svc = AsyncMock()
    vector_svc = AsyncMock()
    embedder = AsyncMock()
    return graph_svc, vector_svc, embedder

@pytest.fixture
def ingestion_service(mock_dependencies):
    graph_svc, vector_svc, embedder = mock_dependencies
    svc = IngestionService(graph_svc, vector_svc, embedder)
    # mock chunker to return some chunks
    mock_chunk = MagicMock()
    mock_chunk.chunk_id = "chunk_1"
    mock_chunk.parent_id = "doc_1"
    mock_chunk.content = "test chunk"
    mock_chunk.content_hash = "hash1"
    mock_chunk.metadata = MagicMock()
    mock_chunk.metadata.dict.return_value = {"filename": "test.txt"}
    
    svc.chunker.chunk_document = MagicMock(return_value=[mock_chunk])
    return svc

@pytest.mark.asyncio
async def test_embedding_api_failure(ingestion_service, mock_dependencies):
    graph_svc, vector_svc, embedder = mock_dependencies
    embedder.embed_documents.side_effect = Exception("Embedding API Down")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"unique content 1")
        tmp_path = tmp.name
    
    try:
        with pytest.raises(HTTPException) as exc:
            await ingestion_service.ingest_document(tmp_path)
        assert exc.value.status_code == 503
        assert "Embedding API unavailable" in exc.value.detail
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

@pytest.mark.asyncio
async def test_neo4j_graph_failure(ingestion_service, mock_dependencies):
    graph_svc, vector_svc, embedder = mock_dependencies
    embedder.embed_documents.return_value = [[0.1, 0.2]]
    graph_svc.execute_write.side_effect = Exception("Neo4j Down")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"unique content 2")
        tmp_path = tmp.name
        
    try:
        with pytest.raises(HTTPException) as exc:
            await ingestion_service.ingest_document(tmp_path)
        assert exc.value.status_code == 503
        assert "Graph Database unavailable" in exc.value.detail
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

@pytest.mark.asyncio
async def test_qdrant_storage_failure_triggers_cleanup(ingestion_service, mock_dependencies):
    graph_svc, vector_svc, embedder = mock_dependencies
    embedder.embed_documents.return_value = [[0.1, 0.2]]
    
    if hasattr(vector_svc, "batch_upsert"):
        vector_svc.batch_upsert.side_effect = Exception("Qdrant Down")
    else:
        vector_svc.upsert.side_effect = Exception("Qdrant Down")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"unique content 3")
        tmp_path = tmp.name
        
    try:
        with pytest.raises(HTTPException) as exc:
            await ingestion_service.ingest_document(tmp_path)
            
        assert exc.value.status_code == 503
        assert "Storage services unavailable" in exc.value.detail
        
        cleanup_calls = [
            call for call in graph_svc.execute_write.call_args_list
            if "DETACH DELETE" in call[0][0]
        ]
        assert len(cleanup_calls) >= 2, "Graph cleanup queries were not executed"
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
