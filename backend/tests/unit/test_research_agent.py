"""
ASEP — Autonomous Research Agent Unit Tests
============================================
10 tests verifying the DocCrawler, DOC_SOURCE_REGISTRY, TTL cache,
TF-IDF KB query, research_phase_node, and implement_phase_node RAG pre-query.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.doc_crawler import (
    DOC_SOURCE_REGISTRY,
    DocChunk,
    DocCrawler,
    KnowledgeBaseIndex,
    _build_idf,
    _compute_tf,
    _html_to_text,
    _tfidf_vector,
    _tokenize,
    doc_crawler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_crawler() -> DocCrawler:
    """Return a fresh DocCrawler instance for isolation."""
    return DocCrawler()


def _inject_static_index(crawler: DocCrawler, product_type: str, project_id: str) -> list[DocChunk]:
    """Inject static pattern chunks directly into crawler._index for testing."""
    chunks = crawler._static_fallback_chunks(product_type, project_id)
    if chunks:
        all_token_lists = [_tokenize(c.text) for c in chunks]
        idf = _build_idf(all_token_lists)
        tfidf_vecs = [_tfidf_vector(_compute_tf(tl), idf) for tl in all_token_lists]
        key = crawler._cache_key(project_id, product_type)
        crawler._index[key] = KnowledgeBaseIndex(
            chunks=chunks,
            tfidf_vectors=tfidf_vecs,
            idf=idf,
            crawled_at=datetime.utcnow(),
        )
    return chunks


# ===========================================================================
# Test 1 — DOC_SOURCE_REGISTRY has entries for expected frameworks
# ===========================================================================
def test_doc_source_registry_coverage():
    """DOC_SOURCE_REGISTRY must cover: fastapi, react, nextjs, django, vue, flask."""
    required_keys = {"fastapi", "react", "nextjs", "django", "vue", "flask"}
    for key in required_keys:
        assert key in DOC_SOURCE_REGISTRY, f"Missing key in DOC_SOURCE_REGISTRY: {key}"
        urls = DOC_SOURCE_REGISTRY[key]
        assert isinstance(urls, list) and len(urls) >= 1, (
            f"DOC_SOURCE_REGISTRY['{key}'] must have at least 1 URL, got: {urls}"
        )
        for url in urls:
            assert url.startswith("https://"), f"URL must start with https://: {url}"


# ===========================================================================
# Test 2 — _chunk() splits on paragraph boundaries, respects max-token limit
# ===========================================================================
def test_chunk_splits_on_paragraph_boundaries():
    """_chunk() must produce multiple chunks from a multi-paragraph text,
    each within the token limit."""
    crawler = _make_crawler()
    # Build a text that is clearly > _CHUNK_MAX_TOKENS (400 tokens ~ 1600 chars)
    long_text = "\n\n".join(
        f"Paragraph {i}: " + ("word " * 60)  # ~60 tokens per paragraph
        for i in range(12)
    )
    chunks = crawler._chunk(
        text=long_text,
        url="https://example.com/docs",
        product_type="fastapi",
        project_id="test-project",
    )
    assert len(chunks) >= 2, "Long text should produce at least 2 chunks"
    for chunk in chunks:
        assert chunk.tokens <= 500, (
            f"Chunk exceeds token limit: {chunk.tokens} tokens"
        )
        assert chunk.url == "https://example.com/docs"
        assert chunk.product_type == "fastapi"
        assert chunk.project_id == "test-project"
        assert isinstance(chunk.crawled_at, datetime)


# ===========================================================================
# Test 3 — crawl_and_index() with mocked HTTP returns DocChunk list
# ===========================================================================
def test_crawl_and_index_with_mock_http():
    """crawl_and_index() should return DocChunk list when HTTP is mocked."""
    crawler = _make_crawler()

    html_content = """
    <html><body>
    <h1>FastAPI Tutorial</h1>
    <p>FastAPI is a modern web framework. Use <code>@app.get</code> to define routes.
    Declare parameters with Python type hints. async def read_item(item_id: int).</p>

    <p>Use <code>@app.post</code> to create resources. Pydantic models validate request body.
    class Item(BaseModel): name: str, price: float</p>

    <p>Dependency injection with Depends. OAuth2 security with OAuth2PasswordBearer.
    HTTPException for error responses with status codes.</p>
    </body></html>
    """

    async def run():
        with patch.object(crawler, "_fetch", new_callable=AsyncMock, return_value=html_content):
            chunks = await crawler.crawl_and_index(
                product_type="fastapi",
                project_id="run-test-001",
                urls=["https://fastapi.tiangolo.com/tutorial/"],
            )
        return chunks

    chunks = asyncio.get_event_loop().run_until_complete(run())
    assert isinstance(chunks, list)
    assert len(chunks) >= 1, "At least 1 chunk should be produced from the mocked HTML"
    for chunk in chunks:
        assert isinstance(chunk, DocChunk)
        assert chunk.product_type == "fastapi"
        assert chunk.project_id == "run-test-001"
        assert len(chunk.text) > 0


# ===========================================================================
# Test 4 — query() returns top-k ranked chunks
# ===========================================================================
def test_query_returns_top_k_chunks():
    """query() should return the most relevant chunks for a given query."""
    crawler = _make_crawler()
    chunks = _inject_static_index(crawler, "fastapi", "proj-query")

    if not chunks:
        pytest.skip("No static chunks for fastapi")

    results = crawler.query(
        query_text="how to create a GET route with path parameters async def",
        product_type="fastapi",
        project_id="proj-query",
        top_k=3,
    )
    assert isinstance(results, list)
    assert len(results) >= 1, "Query should return at least 1 chunk"
    assert len(results) <= 3, "Query should return at most top_k=3 chunks"
    for chunk in results:
        assert isinstance(chunk, DocChunk)
        assert chunk.product_type == "fastapi"


# ===========================================================================
# Test 5 — is_cache_fresh() returns True within 7 days, False after
# ===========================================================================
def test_cache_ttl_fresh_and_stale():
    """is_cache_fresh() must respect the 7-day TTL."""
    crawler = _make_crawler()
    project_id = "proj-ttl"
    product_type = "fastapi"
    key = crawler._cache_key(project_id, product_type)

    # No cache yet → not fresh
    assert not crawler.is_cache_fresh(project_id, product_type)

    # Inject a fresh index (crawled_at = now)
    chunks = crawler._static_fallback_chunks(product_type, project_id)
    crawler._index[key] = KnowledgeBaseIndex(
        chunks=chunks,
        tfidf_vectors=[{}] * len(chunks),
        idf={},
        crawled_at=datetime.utcnow(),
    )
    assert crawler.is_cache_fresh(project_id, product_type), "Cache should be fresh right after indexing"

    # Simulate stale cache (crawled_at 8 days ago)
    crawler._index[key].crawled_at = datetime.utcnow() - timedelta(days=8)
    assert not crawler.is_cache_fresh(project_id, product_type), "Cache should be stale after 8 days"


# ===========================================================================
# Test 6 — refresh() evicts stale cache and re-crawls
# ===========================================================================
def test_refresh_evicts_and_recrawls():
    """refresh() should clear the old cache and produce a new index."""
    crawler = _make_crawler()
    project_id = "proj-refresh"
    product_type = "flask"
    key = crawler._cache_key(project_id, product_type)

    # Pre-populate with stale data
    old_chunks = [DocChunk(
        url="https://old.example.com",
        text="old stale documentation",
        tokens=10,
        product_type=product_type,
        project_id=project_id,
        crawled_at=datetime.utcnow() - timedelta(days=10),
    )]
    crawler._index[key] = KnowledgeBaseIndex(
        chunks=old_chunks, tfidf_vectors=[{}], idf={}, crawled_at=datetime.utcnow() - timedelta(days=10)
    )

    async def run():
        html = "<html><body><p>Flask 3.x modern patterns. Use MethodView for class-based views.</p></body></html>"
        with patch.object(crawler, "_fetch", new_callable=AsyncMock, return_value=html):
            new_chunks = await crawler.refresh(project_id, product_type)
        return new_chunks

    new_chunks = asyncio.get_event_loop().run_until_complete(run())
    assert key in crawler._index, "Index should be rebuilt after refresh"
    # Old content should be gone
    for chunk in crawler._index[key].chunks:
        assert "old stale" not in chunk.text, "Stale content should have been evicted"


# ===========================================================================
# Test 7 — research_phase_node: cache-hit emits [Research Node] message
# ===========================================================================
def test_research_phase_node_cache_hit():
    """research_phase_node should emit [Research Node] message with cache_hit=True."""
    from src.runtime.nodes import research_phase_node

    # Pre-populate doc_crawler singleton with fresh cache
    project_id = "run-cache-hit"
    product_type = "api"
    key = doc_crawler._cache_key(project_id, product_type)
    chunks = doc_crawler._static_fallback_chunks(product_type, project_id)
    doc_crawler._index[key] = KnowledgeBaseIndex(
        chunks=chunks,
        tfidf_vectors=[{}] * len(chunks),
        idf={},
        crawled_at=datetime.utcnow(),
    )

    state = {
        "goal": "Build a FastAPI REST API",
        "run_id": project_id,
        "product_type": product_type,
        "status": "orchestrating",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    result = asyncio.get_event_loop().run_until_complete(research_phase_node(state))
    assert result["status"] == "verified"
    assert result["current_phase"] == "research"
    assert "knowledge_sources" in result

    # Find the [Research Node] telemetry message
    research_msgs = [
        m for m in result.get("messages", [])
        if "[Research Node]" in m.get("content", "")
    ]
    assert len(research_msgs) >= 1, "Should emit [Research Node] telemetry message"

    telemetry = json.loads(
        research_msgs[0]["content"].replace("[Research Node]", "").strip()
    )
    assert telemetry["cache_hit"] is True
    assert telemetry["product_type"] == product_type


# ===========================================================================
# Test 8 — research_phase_node: cache-miss crawls and emits chunk count
# ===========================================================================
def test_research_phase_node_cache_miss_crawls():
    """research_phase_node should crawl and emit chunk_count > 0 on cache miss."""
    from src.runtime.nodes import research_phase_node

    project_id = "run-cache-miss-001"
    product_type = "flask"

    # Ensure no cache for this run
    key = doc_crawler._cache_key(project_id, product_type)
    doc_crawler._index.pop(key, None)

    state = {
        "goal": "Build a Flask web application",
        "run_id": project_id,
        "product_type": product_type,
        "status": "orchestrating",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    html = (
        "<html><body>"
        "<p>Flask 3.x Application. from flask import Flask. app = Flask(__name__). "
        "Use MethodView for class-based views. "
        "@app.route('/') def index(): return 'Hello World'</p>"
        "<p>Flask-SQLAlchemy for database integration. Blueprint for modular apps. "
        "Werkzeug utilities for security and testing.</p>"
        "</body></html>"
    )

    async def run():
        with patch.object(doc_crawler, "_fetch", new_callable=AsyncMock, return_value=html):
            result = await research_phase_node(state)
        return result

    result = asyncio.get_event_loop().run_until_complete(run())
    assert result["status"] == "verified"

    research_msgs = [
        m for m in result.get("messages", [])
        if "[Research Node]" in m.get("content", "")
    ]
    assert len(research_msgs) >= 1, "Should emit [Research Node] message on cache miss"

    telemetry = json.loads(
        research_msgs[0]["content"].replace("[Research Node]", "").strip()
    )
    assert telemetry["cache_hit"] is False
    assert telemetry["chunk_count"] > 0, "Should have indexed at least 1 chunk"


# ===========================================================================
# Test 9 — implement_phase_node prepends [Knowledge Base Context] message
# ===========================================================================
def test_implement_phase_node_prepends_kb_context():
    """implement_phase_node should prepend [Knowledge Base Context] from the KB."""
    from src.runtime.nodes import implement_phase_node

    project_id = "run-impl-kb"
    product_type = "fastapi"

    # Ensure the crawler has indexed FastAPI patterns
    _inject_static_index(doc_crawler, product_type, project_id)

    state = {
        "goal": "Build a FastAPI REST API with authentication",
        "run_id": project_id,
        "product_type": product_type,
        "status": "verified",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "variables": {},
    }

    result = asyncio.get_event_loop().run_until_complete(implement_phase_node(state))
    assert result["status"] == "verified"
    assert result["current_phase"] == "implement"

    messages = result.get("messages", [])
    kb_msgs = [
        m for m in messages
        if "[KB Query]" in m.get("content", "") or "[Knowledge Base Context]" in m.get("content", "")
    ]
    assert len(kb_msgs) >= 1, (
        "implement_phase_node should prepend [KB Query] or [Knowledge Base Context] message"
    )


# ===========================================================================
# Test 10 — FastAPI pattern: crawled chunks contain modern FastAPI syntax
# ===========================================================================
def test_fastapi_patterns_are_modern():
    """
    Static FastAPI pattern chunks must contain modern FastAPI syntax:
    async def, @app.get, @app.post, HTTPException, Depends, Pydantic BaseModel.
    These ensure agent never uses outdated Flask-style or Bottle-style patterns.
    """
    crawler = _make_crawler()
    chunks = crawler._static_fallback_chunks("fastapi", "verification-project")

    assert len(chunks) >= 3, "FastAPI should have at least 3 pattern chunks"

    all_text = " ".join(c.text for c in chunks)

    modern_patterns = [
        "async def",
        "@app.get",
        "@app.post",
        "HTTPException",
        "Depends",
        "BaseModel",
        "FastAPI",
    ]
    for pattern in modern_patterns:
        assert pattern in all_text, (
            f"FastAPI static chunks missing modern pattern: '{pattern}'. "
            f"Agent would fall back to training-data memory instead of current docs."
        )

    # Ensure no Flask-specific outdated patterns appear in FastAPI chunks
    flask_anti_patterns = ["@app.route(", "render_template("]
    for anti in flask_anti_patterns:
        assert anti not in all_text, (
            f"FastAPI chunks must not contain Flask pattern: '{anti}'"
        )
