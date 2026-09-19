import pytest
import asyncio
from src.vector.vector_service import VectorService
from src.vector import VectorRecord
from src.config.settings import get_settings

@pytest.mark.asyncio
async def test_sparse_bm25_qdrant_integration():
    settings = get_settings()
    vs = VectorService(settings.QDRANT_URL, settings.QDRANT_API_KEY)
    
    collection = "test_sparse_integration"
    # Ensure clean slate
    await vs.delete_collection(collection)
    
    # Create with sparse config
    await vs.create_collection(collection, vector_size=2)
    
    # Provide one doc with highly unique keyword not in dense semantic similarity
    text1 = "A generic document about fruits."
    text2 = "XYZZY123 unique string."
    
    # Dummy dense vectors (orthogonal, so dense search fails)
    vec1 = [1.0, 0.0]
    vec2 = [0.0, 1.0]
    
    # Upsert
    await vs.upsert_documents(collection, [
        VectorRecord(id="doc1", vector=vec1, payload={"text": text1}),
        VectorRecord(id="doc2", vector=vec2, payload={"text": text2}),
    ])
    
    # Small delay for Qdrant indexing
    await asyncio.sleep(1)
    
    # Dense search for XYZZY123 with vec1 (which is orthogonal to doc2)
    # Dense should return doc1 because vec1 matches vec1 (cosine similarity 1.0)
    dense_hits = await vs.search(collection, query_vector=vec1, limit=1)
    
    # Sparse search for XYZZY123
    sparse_query = vs.embed_sparse("XYZZY123")
    sparse_hits = await vs._client.search(
        collection_name=collection,
        query_vector=sparse_query,
        query_vector_name="sparse",
        limit=1
    )
    
    # Prove doc findable ONLY by exact keyword is returned by hybrid (sparse) but NOT by dense-only
    assert dense_hits[0].id == "doc1", "Dense search returned wrong doc"
    assert sparse_hits[0].id == "doc2", "Sparse search failed to find the exact keyword match"
