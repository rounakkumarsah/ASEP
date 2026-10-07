"""
Unit tests for WebSearch tool and Exploration Pipeline Real Metrics
===================================================================
Verifies:
- WebSearch execution with Tavily/Serper environment variables and free fallback
- Logging of all tool invocations at INFO level
- Real counts computed from actual tool calls (files, searches, duration, token savings)
- Single exploration summary generation without fake/duplicate phases
"""

import logging
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.runtime.explore_manager import (
    ExploreEvent,
    ExplorationSummary,
    ExploreManager,
    get_explore_manager,
    set_explore_manager,
)
from src.tools.web_search import WebSearchTool, execute_web_search
from src.tools.router import ToolDispatcher
from src.tools.registry import ToolRegistry


@pytest.fixture
def test_workspace(tmp_path):
    ws = tmp_path / "test_workspace"
    ws.mkdir()
    src = ws / "backend" / "src"
    src.mkdir(parents=True)
    f1 = src / "app.py"
    f1.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    f2 = src / "router.py"
    f2.write_text("class Router:\n    pass\n", encoding="utf-8")
    mgr = ExploreManager(workspace_root=str(ws))
    set_explore_manager(mgr)
    return mgr


@pytest.mark.asyncio
async def test_web_search_fallback_duckduckgo():
    """Verify web search executes and returns structured results via zero-config fallback."""
    with patch.dict(os.environ, {"TAVILY_API_KEY": "", "SERPER_API_KEY": ""}):
        res = await execute_web_search("fastapi documentation", max_results=2)
        assert res["query"] == "fastapi documentation"
        assert res["engine"] in ("duckduckgo", "fallback")
        assert res["duration_ms"] >= 0
        assert "results" in res
        assert isinstance(res["results"], list)


@pytest.mark.asyncio
async def test_web_search_tavily_dispatch():
    """Verify web search routes to Tavily when API key is set."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com", "content": "FastAPI is a modern web framework"}
        ]
    }

    with patch.dict(os.environ, {"TAVILY_API_KEY": "test-tavily-key"}), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await execute_web_search("fastapi tutorial", max_results=1)
        assert res["engine"] == "tavily"
        assert len(res["results"]) == 1
        assert res["results"][0]["title"] == "FastAPI Docs"


@pytest.mark.asyncio
async def test_web_search_tool_execution():
    """Verify WebSearchTool conforms to BaseTool interface."""
    tool = WebSearchTool()
    assert tool.name == "web_search"
    out = await tool.execute({"query": "python asyncio", "max_results": 2})
    assert out.success is True
    assert "results" in out.result
    assert out.result["query"] == "python asyncio"


@pytest.mark.asyncio
async def test_tool_logging_at_info_level(caplog):
    """Verify tool invocations log at INFO level with tool name, args, duration, result size."""
    caplog.set_level(logging.INFO)
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    dispatcher = ToolDispatcher(registry)

    with patch("src.tools.web_search.execute_web_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {
            "engine": "duckduckgo",
            "query": "pytest",
            "results": [{"title": "Pytest", "url": "https://pytest.org", "snippet": "testing framework"}],
            "count": 1,
            "duration_ms": 25,
            "result_size": 17,
        }
        await dispatcher.execute("web_search", {"query": "pytest", "max_results": 1}, granted_permissions=["web_search"])

    # Check for INFO level tool invocation log
    found_log = any(
        "Tool invocation: tool='web_search'" in record.message
        and "args=" in record.message
        and "duration=" in record.message
        and "result_size=" in record.message
        for record in caplog.records
    )
    assert found_log, f"Expected tool invocation INFO log not found in: {[r.message for r in caplog.records]}"


@pytest.mark.asyncio
async def test_explore_phase_real_metrics(test_workspace, caplog):
    """Verify explore_phase computes real counts from actual tool invocations without hardcoding."""
    caplog.set_level(logging.INFO)
    state = {"goal": "Build REST API", "thread_id": "test-real-metrics"}

    events, summary = await test_workspace.explore_phase("research", "Build REST API", state)

    # Verify real metrics
    assert summary["phase"] == "research"
    assert summary["files_explored_count"] >= 1  # app.py or router.py
    assert summary["searches_count"] >= 1       # workspace glob + grep + web search
    assert summary["duration_ms"] > 0
    assert summary["tokens_saved"] > 0
    # Make sure tokens_saved is computed from file size, not hardcoded 3200 default
    assert summary["tokens_saved"] != 3200

    # Verify tool invocation logs were emitted
    logged_tools = [
        r.message for r in caplog.records
        if "Tool invocation: tool=" in r.message
    ]
    assert len(logged_tools) >= 3, f"Expected multiple tool invocation logs, got: {logged_tools}"
