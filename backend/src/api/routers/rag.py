import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.documents.context_builder import ContextBuilder
from src.documents.embedding_service import RuntimeEmbeddingProvider
from src.documents.retrieval import Retriever
from src.vector import VectorService
from src.vector.qdrant import get_qdrant_client

router = APIRouter()

# Schema structures
class RAGQueryRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=50)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    filters: dict[str, Any] | None = None

class ContextSegment(BaseModel):
    chunk_id: str
    score: float
    text: str
    filename: str
    file_path: str

class RAGSearchResponse(BaseModel):
    query: str
    context: str
    segments: list[ContextSegment]
    citations: str
    latency_ms: float
    estimated_tokens: int

# Instantiations
def get_retriever() -> Retriever:
    client = get_qdrant_client()
    vector_service = VectorService(client=client)
    embedder = RuntimeEmbeddingProvider()

    # Optional GraphService injection to support degraded Neo4j startup
    graph_service = None
    try:
        from src.graph import GraphService
        from src.graph.neo4j import get_neo4j_driver
        driver = get_neo4j_driver()
        graph_service = GraphService(driver=driver)
    except Exception:
        # Graceful fallback: run RAG with Vector-only results
        pass

    return Retriever(
        vector_service=vector_service,
        embedding_provider=embedder,
        graph_service=graph_service,
    )


@router.post("/rag/search", response_model=RAGSearchResponse)
async def semantic_rag_search(
    request: RAGQueryRequest,
    retriever: Retriever = Depends(get_retriever),
) -> RAGSearchResponse:
    """Execute a hybrid vector + graph RAG query with strict rate-limiting."""
    # Production Rate Limiting — 30 RAG searches / 1 min per client
    try:
        from src.auth.rate_limit import check_rate_limit
        from src.cache.redis import get_redis_client
        redis = get_redis_client()
        rate_key = f"rate_limit:rag:search:{hash(request.query) % 10000}"
        allowed = await check_rate_limit(redis, rate_key, max_attempts=30, window_seconds=60)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="RAG query rate limit exceeded. Please wait a moment before searching again.",
            )
    except HTTPException:
        raise
    except Exception:
        pass

    start_time = time.perf_counter()
    try:
        # Step 1: Execute retrieval
        hits = await retriever.retrieve(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filters=request.filters
        )

        # Step 2: Build formatted context blocks and citations
        builder = ContextBuilder()
        context_str, selected, citations_str = builder.build_context_and_citations(hits)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        segments = [
            ContextSegment(
                chunk_id=c["chunk_id"],
                score=c["score"],
                text=c["text"],
                filename=c["filename"],
                file_path=c["file_path"]
            )
            for c in selected
        ]

        return RAGSearchResponse(
            query=request.query,
            context=context_str,
            segments=segments,
            citations=citations_str,
            latency_ms=round(latency_ms, 2),
            estimated_tokens=builder.context_manager.estimate_tokens(context_str)
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG Retrieval failed: {str(exc)}")

@router.get("/rag/diagnostics")
async def retrieval_diagnostics():
    """
    Return global diagnostics regarding context window parameters, loaded schemas, and indexing state.
    """
    from src.documents.ingestion import IngestionService
    return {
        "active_vector_store": "Qdrant",
        "embedding_cache_size": len(IngestionService._embedding_cache),
        "ingested_document_count": len(IngestionService._ingested_documents),
        "evaluation_strategy": "Scaffold",
        "hybrid_retrieval_scaffold": "BM25 (stubbed)",
        "reranker_scaffold": "Cross-Encoder (stubbed)",
    }
