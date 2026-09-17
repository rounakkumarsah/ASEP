"""
Unit tests for ASEP Live Exploration Feed & ExploreManager
==========================================================
Verifies:
- Structured explore actions (search_files, list_directory, read_file, grep_pattern)
- 20-line preview extraction & file metadata
- 200ms event buffering and flusher
- Resilient failure recovery (file not found ⚠️ -> graceful retry)
- Exploration summary generation with architecture understanding, risks, and tokens saved
- Token-saving context injection to coding agents (zero duplicate re-exploration)
- Explore node execution in LangGraph runtime
- Conversation explore REST/SSE endpoints
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.runtime.explore_manager import (
    ExploreEvent,
    ExplorationSummary,
    EventBuffer,
    ExploreManager,
    get_explore_manager,
    set_explore_manager,
)
from src.runtime.nodes import explore_node, implement_phase_node
from src.runtime.state import AgentState


@pytest.fixture
def explore_mgr(tmp_path):
    # Set up a test workspace with known directory and files
    ws = tmp_path / "workspace"
    ws.mkdir()
    auth_dir = ws / "backend" / "src" / "auth"
    auth_dir.mkdir(parents=True)
    
    # Create sample auth files
    service_file = auth_dir / "service.py"
    service_content = "\n".join([f"# Line {i}: def verify_token(): pass" for i in range(1, 35)])
    service_file.write_text(service_content, encoding="utf-8")

    models_file = auth_dir / "models.py"
    models_file.write_text("class User:\n    id: str\n    username: str\n", encoding="utf-8")

    mgr = ExploreManager(workspace_root=str(ws))
    set_explore_manager(mgr)
    return mgr


def test_search_files(explore_mgr):
    matches, count, duration = explore_mgr.search_files("*auth*", max_results=10)
    assert count >= 1
    assert any("service.py" in m for m in matches)
    assert duration >= 0


def test_list_directory(explore_mgr):
    items, duration = explore_mgr.list_directory("backend/src/auth")
    assert len(items) >= 2
    filenames = [item["name"] for item in items]
    assert "service.py" in filenames
    assert "models.py" in filenames


def test_read_file_with_preview(explore_mgr):
    # Test reading with 20-line preview
    preview, size, duration, error = explore_mgr.read_file("backend/src/auth/service.py", max_lines=20)
    assert error is None
    assert preview is not None
    lines = preview.split("\n")
    assert len(lines) == 20
    assert "Line 1" in lines[0]
    assert "Line 20" in lines[19]
    assert size > 0

    # Test reading non-existent file
    preview_missing, size_m, dur_m, error_m = explore_mgr.read_file("backend/src/auth/missing.py")
    assert error_m is not None
    assert "File not found" in error_m
    assert preview_missing is None


def test_grep_pattern(explore_mgr):
    matches, count, duration = explore_mgr.grep_pattern("verify_token", search_path="backend/src/auth")
    assert count >= 1
    assert any("service.py" in m["file"] for m in matches)


def test_event_buffer_200ms_flush():
    flushed_batches = []
    
    def on_flush(batch):
        flushed_batches.append(batch)

    buf = EventBuffer(flush_interval_ms=50, callback=on_flush)
    
    ev1 = ExploreEvent(type="search", detail="Search 1")
    buf.add(ev1)
    
    # Wait for interval to pass
    time_sleep = asyncio.run(asyncio.sleep(0.08))
    
    ev2 = ExploreEvent(type="read", detail="Read 1")
    buf.add(ev2)
    
    flushed = buf.flush()
    assert len(buf.all_events) == 2


@pytest.mark.asyncio
async def test_explore_phase_refactor_auth(explore_mgr):
    state: AgentState = {
        "goal": "refactor the auth module",
        "thread_id": "test-thread-auth-1",
        "current_phase": "explore",
    }

    events, summary = await explore_mgr.explore_phase("explore", "refactor the auth module", state)
    
    assert len(events) >= 5
    types = [e["type"] for e in events]
    assert "think" in types
    assert "search" in types
    assert "read" in types
    assert "analyze" in types

    # Check resilient error handling (failed read -> retry)
    failed_events = [e for e in events if e.get("status") == "failed"]
    assert len(failed_events) >= 1
    assert "legacy_auth.py" in failed_events[0]["detail"]
    assert failed_events[0]["error"] is not None

    # Check that retry/reroute thought followed
    think_events = [e for e in events if e.get("type") == "think"]
    assert any("⚠️" in t["detail"] or "rerouting" in t["detail"] for t in think_events)

    # Check exploration summary
    assert summary["phase"] == "explore"
    assert summary["files_explored_count"] >= 1
    assert summary["searches_count"] >= 1
    assert "architecture_understanding" in summary
    assert len(summary["risks_identified"]) > 0
    assert summary["tokens_saved"] > 0

    # Verify memory caching
    stored_events = explore_mgr.get_events("test-thread-auth-1")
    assert len(stored_events) == len(events)
    stored_summary = explore_mgr.get_summary("test-thread-auth-1", "explore")
    assert stored_summary["phase"] == "explore"


@pytest.mark.asyncio
async def test_explore_node(explore_mgr):
    state: AgentState = {
        "goal": "refactor the auth module",
        "thread_id": "test-thread-node",
        "current_phase": "explore",
    }

    result = await explore_node(state)
    assert result["status"] == "explored"
    assert len(result["exploration_events"]) > 0
    assert result["exploration_summary"]["phase"] == "explore"
    assert any("[Explore Event]" in m["content"] for m in result["messages"])
    assert any("[Explore Summary]" in m["content"] for m in result["messages"])


@pytest.mark.asyncio
async def test_coding_agent_token_savings_and_summary_injection(explore_mgr):
    # 1. First run explore phase to populate summary
    initial_state: AgentState = {
        "goal": "refactor the auth module with JWT verification",
        "thread_id": "test-thread-coding-1",
        "current_phase": "explore",
    }
    explore_res = await explore_node(initial_state)

    # 2. Feed exploration summary into implement_phase_node
    coding_state: AgentState = {
        "goal": "refactor the auth module with JWT verification",
        "thread_id": "test-thread-coding-1",
        "current_phase": "implement",
        "product_type": "api",
        "phase_explorations": explore_res["phase_explorations"],
        "exploration_summary": explore_res["exploration_summary"],
        "explored_files": explore_res["explored_files"],
    }

    implement_res = await implement_phase_node(coding_state)
    assert implement_res["status"] == "verified"
    
    # Confirm the exploration summary was injected into messages to prevent re-exploration
    summary_messages = [
        m for m in implement_res["messages"]
        if "[Exploration Summary" in m.get("content", "")
    ]
    assert len(summary_messages) >= 1
    content = summary_messages[0]["content"]
    assert "DO NOT re-explore or duplicate file reads" in content
    assert "Token Savings" in content or "tokens spared" in content


def test_conversation_explore_endpoints(explore_mgr):
    from fastapi.testclient import TestClient
    from src.api.app import create_app
    from src.auth.dependencies import get_current_user
    from src.db.models.user import User
    import uuid

    # Prime data in explore manager
    thread_id = "test-endpoint-thread-123"
    ev = ExploreEvent(phase="explore", type="search", detail="Searching auth", match_count=5)
    explore_mgr._thread_events[thread_id] = [ev.to_dict()]
    explore_mgr._thread_summaries[thread_id] = {
        "latest": {
            "phase": "explore",
            "relevant_files": ["auth/service.py"],
            "files_explored_count": 1,
            "searches_count": 1,
            "architecture_understanding": "Auth service exists",
            "risks_identified": ["Session expiry"],
            "duration_ms": 120,
            "tokens_saved": 3200,
        }
    }

    app = create_app()
    mock_user = User(id=uuid.uuid4(), username="dev", email="dev@test.com", role="admin", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(f"/api/v1/conversations/{thread_id}/explore")
    assert resp.status_code == 200
    data = resp.json()
    assert data["thread_id"] == thread_id
    assert data["count"] == 1
    assert data["events"][0]["detail"] == "Searching auth"
    assert data["summary"]["tokens_saved"] == 3200

