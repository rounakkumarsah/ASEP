"""
ASEP — Unit Tests for Robust JSON Parsing, Model Selection, PgBouncer, and Global Exception Handler
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.ai_runtime.router import get_model_for_phase, PHASE_PREFERRED_MODELS
from src.db.postgres import CONNECTION_POOL_KWARGS, get_connection_pool
from src.runtime.nodes import parse_llm_json_safely, _try_parse_file_tree, implement_phase_node


class TestRobustJsonParsing:
    """Tests for parse_llm_json_safely and _try_parse_file_tree."""

    def test_parse_valid_json(self):
        raw = '{"name": "test-project", "version": "1.0.0"}'
        result = parse_llm_json_safely(raw)
        assert result == {"name": "test-project", "version": "1.0.0"}

    def test_parse_json_in_markdown_code_fence(self):
        raw = """```json
{
  "app/page.tsx": "export default function Page() { return <div>Hello</div>; }",
  "package.json": "{\\"name\\": \\"test\\"}"
}
```"""
        result = parse_llm_json_safely(raw)
        assert isinstance(result, dict)
        assert "app/page.tsx" in result
        assert "package.json" in result

    def test_parse_json_in_plain_markdown_fence(self):
        raw = """```
{
  "key": "value"
}
```"""
        result = parse_llm_json_safely(raw)
        assert result == {"key": "value"}

    def test_parse_malformed_json_with_repair(self):
        # Missing quotes around keys, single quotes on values, trailing commas
        raw = """```json
{
  name: 'landing-page',
  files: ['page.tsx', 'layout.tsx', ],
}
```"""
        result = parse_llm_json_safely(raw)
        assert isinstance(result, dict)
        assert result.get("name") == "landing-page"
        assert result.get("files") == ["page.tsx", "layout.tsx"]

    def test_parse_unclosed_json(self):
        raw = '{"app/page.tsx": "export default () => null", "status": "ok"'
        result = parse_llm_json_safely(raw)
        assert isinstance(result, dict)
        assert result.get("status") == "ok"

    def test_parse_empty_and_invalid_input(self):
        assert parse_llm_json_safely("") == {}
        assert parse_llm_json_safely(None) == {}

    def test_try_parse_file_tree_with_malformed_json(self):
        malformed = """```json
{
  'app/page.tsx': "export default function Page() { return <h1>Hi</h1>; }",
  'package.json': "{name: 'app'}",
}
```"""
        tree = _try_parse_file_tree(malformed)
        assert isinstance(tree, dict)
        assert "app/page.tsx" in tree
        assert "package.json" in tree


class TestModelSelection:
    """Tests ensuring preferred LLM for code generation is groq/llama-3.3-70b-versatile."""

    def test_preferred_model_for_implement(self):
        assert get_model_for_phase("implement") == "groq/llama-3.3-70b-versatile"
        assert get_model_for_phase("coding") == "groq/llama-3.3-70b-versatile"
        assert get_model_for_phase("code_generation") == "groq/llama-3.3-70b-versatile"
        assert PHASE_PREFERRED_MODELS["implement"] == "groq/llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_implement_node_switches_from_8b_to_70b(self):
        state = {
            "goal": "build a custom microservice",
            "model": "groq/llama-3.1-8b-instant",
            "product_type": "api",
            "status": "verified",
            "run_id": "test-model-selection",
            "token_usage_per_phase": {},
            "token_budget_per_phase": {},
            "token_savings": {},
            "file_history": {},
            "budget_approvals": [],
        }

        mock_complete = AsyncMock()
        mock_res = MagicMock()
        mock_res.text = "```python\n# Microservice code\nprint('hello')\n```"
        mock_complete.return_value = mock_res

        with patch("src.ai_runtime.service.AIRuntimeService.complete", mock_complete):
            result = await implement_phase_node(state)
            assert result["status"] == "verified"
            assert mock_complete.called
            # Verify the request used the 70b model rather than the 8b model
            req_arg = mock_complete.call_args[0][0]
            assert req_arg.model == "groq/llama-3.3-70b-versatile"


class TestPgBouncerPoolConfiguration:
    """Tests verifying PostgreSQL connection pool settings for PgBouncer / Vercel."""

    def test_connection_pool_kwargs_contain_prepare_threshold_and_autocommit(self):
        assert CONNECTION_POOL_KWARGS.get("prepare_threshold") == 0
        assert CONNECTION_POOL_KWARGS.get("autocommit") is True

    def test_get_connection_pool_passes_expected_kwargs(self):
        mock_pool = MagicMock()
        with patch("src.db.postgres.AsyncConnectionPool", mock_pool):
            pool = get_connection_pool("postgresql://user:pass@localhost:5432/testdb")
            assert mock_pool.called
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs["kwargs"]["prepare_threshold"] == 0
            assert call_kwargs["kwargs"]["autocommit"] is True


class TestGlobalExceptionHandler:
    """Tests verifying the global exception handler returns 500 JSON with traceback."""

    @pytest.mark.asyncio
    async def test_global_exception_handler_returns_traceback(self):
        from src.api.app import create_app

        app = create_app()

        @app.get("/test-crash")
        async def crash_endpoint():
            raise RuntimeError("Deliberate test failure for traceback verification")

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test-crash")
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "Deliberate test failure" in data["error"]
            assert data["error_code"] == "INTERNAL_SERVER_ERROR"
            assert "traceback" in data
            assert "RuntimeError" in data["traceback"]
            assert data["path"] == "/test-crash"
