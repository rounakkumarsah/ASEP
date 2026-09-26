import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from src.runtime.nodes import implement_phase_node, end_node_default, security_audit_phase_node


@pytest.mark.asyncio
async def test_implement_phase_node_todo_rest_api_fallback():
    """When LLM provider fails, implement_phase_node should generate complete To-Do REST API code."""
    state = {
        "goal": "build a simple REST API for a To-Do app",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-todo-fallback",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=RuntimeError("AI provider error")):
        result = await implement_phase_node(state)

    code = result.get("generated_code", "")
    assert "FastAPI" in code
    assert "/todos" in code
    assert "TodoItem" in code
    assert result["status"] == "verified"

    messages = result.get("messages", [])
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
    assert len(assistant_msgs) >= 1
    assert "FastAPI" in assistant_msgs[-1].get("content", "")


@pytest.mark.asyncio
async def test_implement_phase_node_llm_crlf_extraction():
    """implement_phase_node should properly parse markdown code fences with CRLF line endings."""
    state = {
        "goal": "build a custom microservice",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-llm-crlf",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    mock_res = MagicMock()
    mock_res.text = "```python  \r\nimport uvicorn\r\n# CRLF custom service\r\n```"

    with patch("src.ai_runtime.service.AIRuntimeService.complete", new_callable=AsyncMock, return_value=mock_res):
        result = await implement_phase_node(state)

    code = result.get("generated_code", "")
    assert "CRLF custom service" in code


@pytest.mark.asyncio
async def test_end_node_excludes_security_audit_from_assistant_final_answer():
    """end_node_default should not treat security audit markdown tables as the final assistant answer."""
    state = {
        "goal": "build a simple REST API for a To-Do app",
        "status": "verified",
        "generated_code": "from fastapi import FastAPI\napp = FastAPI()",
        "security_passed": True,
        "messages": [
            {
                "role": "assistant",
                "content": "```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```",
            },
            {
                "role": "system",
                "content": "Security Audit Severity Table\n| Severity | Count |\n| Critical | 0 |",
            },
        ],
    }

    result = await end_node_default(state)
    messages = result.get("messages", [])
    assistant_msg = next((m for m in messages if m.get("role") == "assistant"), None)
    assert assistant_msg is not None
    assert "from fastapi import FastAPI" in assistant_msg.get("content", "")
    assert "Security Audit Severity Table" not in assistant_msg.get("content", "")


@pytest.mark.asyncio
async def test_security_audit_phase_node_emits_system_role_table():
    """security_audit_phase_node should emit the severity table under system role, not assistant."""
    state = {
        "generated_code": "def hello(): pass",
        "product_type": "api",
        "run_id": "test-sec-audit",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    result = await security_audit_phase_node(state)
    messages = result.get("messages", [])
    # Check that severity table is NOT emitted as an assistant message
    for msg in messages:
        if "severity" in msg.get("content", "").lower() or "table" in msg.get("content", "").lower():
            assert msg.get("role") == "system"


@pytest.mark.asyncio
async def test_implement_phase_node_timeout_fallback():
    """When LLM provider hangs or times out, implement_phase_node should safely fall back within timeout."""
    state = {
        "goal": "build a simple REST API for a todo app",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-todo-timeout",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    async def slow_complete(*args, **kwargs):
        await asyncio.sleep(10.0)

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=slow_complete):
        start = asyncio.get_event_loop().time()
        result = await implement_phase_node(state)
        elapsed = asyncio.get_event_loop().time() - start

    assert elapsed < 7.0
    code = result.get("generated_code", "")
    assert "FastAPI" in code
    assert "/todos" in code
    assert "TodoItem" in code
    assert result["status"] == "verified"

