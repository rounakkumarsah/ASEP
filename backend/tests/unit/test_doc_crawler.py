"""
Tests for Autonomous Research Agent, Doc Crawler, Vector Search, and 7-day TTL Cache
=====================================================================================
Validates:
1. Automatic stack detection (FastAPI, React, Next.js).
2. Official doc crawling, latest version detection, and chunking.
3. Vector search semantic retrieval over indexed documentation.
4. 7-day TTL caching per project (in-memory & disk, expiration logic).
5. Pre-coding API pattern queries — never relying on outdated training-data.
6. Modern FastAPI generation with lifespan context manager and Pydantic v2.
7. Deprecated pattern detection and automatic modernization.
8. End-to-end execution of research_phase_node and implement_phase_node.
"""

import time
import pytest
from src.runtime.nodes import research_phase_node, implement_phase_node
from src.runtime.state import AgentState
from src.utils.doc_crawler import (
    DocCrawler,
    DocChunk,
    ProjectDocCache,
    VectorSearchIndex,
    DEFAULT_TTL_SECONDS,
    get_doc_crawler,
)


class TestDocCrawlerUnit:
    """Unit tests for the DocCrawler, Chunker, and Vector Index."""

    def test_stack_detection(self):
        crawler = DocCrawler()
        assert crawler.detect_stack("Build a FastAPI backend for auth") == "fastapi"
        assert crawler.detect_stack("Create a modern python api with pydantic") == "fastapi"
        assert crawler.detect_stack("Create a dashboard with React components") == "react"
        assert crawler.detect_stack("Next.js web app with app router") == "nextjs"
        # Product type priority
        assert crawler.detect_stack("General web app", product_type="fastapi") == "fastapi"

    def test_vector_search_indexing_and_retrieval(self):
        index = VectorSearchIndex()
        chunk1 = DocChunk(
            chunk_id="fa_1",
            stack="fastapi",
            title="Lifespan Context Manager",
            url="https://fastapi.tiangolo.com/advanced/events/",
            version="0.115.6",
            section="Lifespan",
            content="Use @asynccontextmanager async def lifespan(app: FastAPI): yield. Never use @app.on_event.",
            recommended_patterns=["@asynccontextmanager async def lifespan(app: FastAPI):"],
            anti_patterns=["@app.on_event('startup')"],
            tags=["lifespan", "startup", "events"],
        )
        chunk2 = DocChunk(
            chunk_id="fa_2",
            stack="fastapi",
            title="Pydantic V2 Model Dump",
            url="https://fastapi.tiangolo.com/tutorial/body/",
            version="0.115.6",
            section="Pydantic V2",
            content="Use model.model_dump() instead of model.dict() and Model.model_validate().",
            recommended_patterns=["model.model_dump()", "Model.model_validate()"],
            anti_patterns=["model.dict()"],
            tags=["pydantic", "model_dump"],
        )
        index.index_chunk(chunk1)
        index.index_chunk(chunk2)

        results = index.search("fastapi startup lifespan event", top_k=1)
        assert len(results) == 1
        matched_chunk, score = results[0]
        assert matched_chunk.chunk_id == "fa_1"
        assert score > 0.1

    def test_7_day_ttl_caching(self, tmp_path):
        cache = ProjectDocCache(cache_dir=tmp_path)
        project_id = "proj_test_123"
        stack = "fastapi"
        chunks = [
            DocChunk(
                chunk_id="1",
                stack="fastapi",
                title="Test Title",
                url="https://fastapi.tiangolo.com",
                version="0.115.6",
                section="Intro",
                content="Sample content",
            )
        ]

        # 1. Set cache with current time
        now = time.time()
        cached = cache.set(project_id, stack, "0.115.6", chunks, current_time=now)
        assert cached.expires_at == now + DEFAULT_TTL_SECONDS
        assert not cached.is_expired(current_time=now)

        # 2. Get cache before TTL (e.g. 3 days later)
        three_days_later = now + (3 * 24 * 3600)
        retrieved = cache.get(project_id, stack, current_time=three_days_later)
        assert retrieved is not None
        assert retrieved.version == "0.115.6"

        # 3. Cache expired after 7 days (e.g. 7 days + 1 second later)
        eight_days_later = now + (8 * 24 * 3600)
        expired_entry = cache.get(project_id, stack, current_time=eight_days_later)
        assert expired_entry is None

    def test_query_api_patterns_and_prompt_guidance(self):
        crawler = DocCrawler()
        chunks = crawler.query_api_patterns("fastapi", "lifespan events startup")
        assert len(chunks) > 0
        assert any("lifespan" in c.title.lower() or "events" in c.section.lower() for c in chunks)

        guidance = crawler.build_system_prompt_guidance("fastapi", "lifespan startup")
        assert "Official FASTAPI API Guidance" in guidance
        assert "REQUIRED CURRENT PATTERNS:" in guidance
        assert "STRICTLY FORBIDDEN:" in guidance
        assert "@app.on_event" in guidance

    def test_deprecated_pattern_detection_and_modernization(self):
        crawler = DocCrawler()
        legacy_code = (
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n\n"
            "@app.on_event('startup')\n"
            "def startup_db():\n"
            "    init_db()\n\n"
            "@app.get('/users')\n"
            "def get_users():\n"
            "    user = User(name='Alice')\n"
            "    return user.dict()\n"
        )

        modern_code, violations = crawler.validate_and_patch_code_patterns(legacy_code, "fastapi")
        assert len(violations) >= 2
        # Check that @app.on_event was eliminated
        assert "@app.on_event('startup')" not in modern_code
        # Check that .dict() was converted to .model_dump()
        assert "user.model_dump()" in modern_code
        # Check that modern lifespan was introduced
        assert "@asynccontextmanager" in modern_code
        assert "async def lifespan" in modern_code
        assert "app = FastAPI(lifespan=lifespan)" in modern_code


@pytest.mark.asyncio
class TestAutonomousResearchNodeWorkflow:
    """Integration test verifying full autonomous research and code generation."""

    async def test_fastapi_backend_autonomous_research_and_implementation(self):
        # User asks for a FastAPI backend — zero documentation provided by user
        initial_state: AgentState = {
            "goal": "Build a modern FastAPI backend with user authentication and database models",
            "project_id": "test_fastapi_proj",
            "messages": [],
            "variables": {},
        }

        # 1. Execute RESEARCH NODE
        research_result = await research_phase_node(initial_state)

        assert research_result["status"] == "verified"
        assert research_result["active_stack"] == "fastapi"
        assert research_result["crawled_chunks_count"] > 0
        assert research_result["docs_cache_ttl"] == DEFAULT_TTL_SECONDS

        # Check telemetry messages
        msg_contents = [m["content"] for m in research_result["messages"]]
        assert any("[Knowledge Ingested]" in m for m in msg_contents)
        assert any("FastAPI" in m or "fastapi" in m for m in msg_contents)

        # Merge state for next node
        merged_state: AgentState = {
            **initial_state,
            **research_result,
        }

        # 2. Execute IMPLEMENT NODE
        implement_result = await implement_phase_node(merged_state)

        assert implement_result["status"] == "verified"
        assert implement_result["retrieved_patterns_count"] > 0
        generated_code = implement_result["generated_code"]

        # 3. VERIFY: Confirm modern FastAPI patterns are present
        assert "lifespan" in generated_code, "Generated code must use modern lifespan context manager"
        assert "@asynccontextmanager" in generated_code, "Generated code must import asynccontextmanager"
        assert "FastAPI(title=" in generated_code and "lifespan=lifespan" in generated_code, (
            "FastAPI app must be instantiated with lifespan=lifespan"
        )
        assert "model_dump()" in generated_code, "Generated code must use Pydantic v2 model_dump()"

        # 4. VERIFY: Confirm outdated/deprecated syntax is strictly absent
        assert "@app.on_event('startup')" not in generated_code, "Must NOT use deprecated @app.on_event('startup')"
        assert "@app.on_event(\"startup\")" not in generated_code, "Must NOT use deprecated @app.on_event(\"startup\")"
        assert "@app.on_event('shutdown')" not in generated_code, "Must NOT use deprecated @app.on_event('shutdown')"
        assert "@app.on_event(\"shutdown\")" not in generated_code, "Must NOT use deprecated @app.on_event(\"shutdown\")"
        assert ".dict()" not in generated_code, "Must NOT use deprecated Pydantic v1 .dict()"

        # Check implement telemetry
        implement_msgs = [m["content"] for m in implement_result["messages"]]
        assert any("[Knowledge Query]" in m for m in implement_msgs)
