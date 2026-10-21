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


@pytest.mark.asyncio
async def test_planner_node_timeout_fallback():
    """When LLM provider hangs or times out, planner_node should abort within 5s."""
    from src.runtime.nodes import planner_node
    state = {
        "goal": "build a todo api",
        "run_id": "test-planner-timeout",
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
        result = await planner_node(state)
        elapsed = asyncio.get_event_loop().time() - start

    assert elapsed < 7.0
    assert result["status"] == "planned"
    assert len(result["plan"]) > 0


@pytest.mark.asyncio
async def test_durable_memories_timeout_resilience():
    """When LLM provider hangs or times out during durable memory extraction, it aborts within 5s without raising."""
    from src.runtime.memory_hooks import extract_and_store_durable_memories
    import uuid

    async def slow_complete(*args, **kwargs):
        await asyncio.sleep(10.0)

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=slow_complete):
        start = asyncio.get_event_loop().time()
        # Should not raise exception and should complete in < 7.0s
        await extract_and_store_durable_memories("run-timeout", uuid.uuid4(), "User: build todo app")
        elapsed = asyncio.get_event_loop().time() - start

    assert elapsed < 7.0


def test_extract_clean_goal_utility():
    """Verify extract_clean_goal correctly strips memory headers and past memories."""
    from src.runtime.state import extract_clean_goal

    # Clean goal passes through
    assert extract_clean_goal("Build a normal AI chat bot") == "Build a normal AI chat bot"

    # Injected memories block stripped cleanly
    polluted_goal = (
        "Relevant Past Memories:\n"
        "- [semantic] The primary goal specified in the transcript is to build a simple REST API for a todo application.\n"
        "- [episodic] Goal: Explain how you would refactor an e-commerce backend.\n"
        "Response: \n"
        "Tools: \n"
        "Status: Failed\n"
        "- [procedural] To define validation schemas, import BaseModel.\n\n"
        "Build a normal AI chat bot"
    )
    cleaned = extract_clean_goal(polluted_goal)
    assert cleaned == "Build a normal AI chat bot"
    assert "Relevant Past Memories" not in cleaned
    assert "todo" not in cleaned.lower()


@pytest.mark.asyncio
async def test_implement_phase_node_chatbot_fallback_not_todo():
    """When building an AI chatbot and LLM provider fails, generate an AI chatbot service, NOT a Todo app."""
    state = {
        "goal": "Build a normal AI chat bot",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-chatbot-not-todo",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=RuntimeError("LLM unavailable")):
        result = await implement_phase_node(state)

    code = result.get("generated_code", "")
    assert "FastAPI" in code
    assert "/chat" in code
    assert "ChatMessage" in code
    # Critical: Must NOT be a Todo app!
    assert "/todos" not in code
    assert "TodoItem" not in code
    assert "todos_db" not in code


@pytest.mark.asyncio
async def test_implement_phase_node_ecommerce_fallback_not_todo():
    """When building an E-Commerce website and LLM provider fails, generate an E-Commerce store API, NOT a Todo app."""
    state = {
        "goal": "Build a E-Commerce website",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-ecommerce-not-todo",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=RuntimeError("LLM unavailable")):
        result = await implement_phase_node(state)

    code = result.get("generated_code", "")
    assert "FastAPI" in code
    assert "/products" in code
    assert "Product" in code
    assert "/orders" in code
    # Critical: Must NOT be a Todo app!
    assert "/todos" not in code
    assert "TodoItem" not in code


@pytest.mark.asyncio
async def test_implement_phase_node_sanitizes_polluted_memory_goal():
    """When memory-polluted goal with old Todo memories is passed, implement_phase_node sanitizes it and produces the real objective."""
    state = {
        "goal": (
            "Relevant Past Memories:\n"
            "- [semantic] The primary goal specified in the transcript is to build a simple REST API for a todo application.\n"
            "- [episodic] Goal: Explain in 3 short bullet points how you would refactor a monolithic e-commerce backend into microservices.\n"
            "Status: Failed\n\n"
            "Build a normal AI chat bot"
        ),
        "product_type": "api",
        "status": "verified",
        "run_id": "test-polluted-sanitization",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=RuntimeError("LLM unavailable")):
        result = await implement_phase_node(state)

    code = result.get("generated_code", "")
    assert "/chat" in code
    assert "ChatMessage" in code
    # Critical: Must NOT be hijacked by the old Todo memory!
    assert "/todos" not in code
    assert "TodoItem" not in code


@pytest.mark.asyncio
async def test_implement_node_domain_guard_rejects_python_and_retries_with_aggressive_prompt():
    """Domain guard triggers on Next.js/Tailwind prompt when LLM outputs Python/FastAPI, retrying with aggressive frontend prompt."""
    from src.runtime.nodes import implement_node

    state = {
        "goal": "Build a modern landing page for a coffee shop using Next.js and Tailwind",
        "product_type": "website",
        "status": "verified",
        "run_id": "test-domain-guard-retry",
        "project_id": "test_coffee_shop_proj",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    call_prompts = []

    async def fake_complete(req):
        nonlocal call_prompts
        user_content = req.messages[0].content
        call_prompts.append(user_content)
        mock_res = MagicMock()
        if len(call_prompts) == 1:
            # First attempt: LLM outputs FastAPI main.py (violation)
            mock_res.text = "```python\n# main.py\nfrom fastapi import FastAPI\napp = FastAPI()\n```"
        else:
            # Second attempt: LLM complies after aggressive system prompt
            mock_res.text = "```tsx\n// page.tsx (.tsx)\nimport React from 'react';\nexport default function CoffeeShop() { return <div className='bg-amber-50'>Artisan Coffee</div>; }\n```"
        return mock_res

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=fake_complete):
        result = await implement_node(state)

    # Must have triggered retry with the aggressive prompt
    assert len(call_prompts) >= 2
    assert "You are a frontend developer. You ONLY write React/Next.js/Tailwind code. DO NOT write Python." in call_prompts[1]

    # Result must be page.tsx and contain .tsx
    assert result["filepath"] == "page.tsx"
    assert ".tsx" in result["generated_code"]
    assert "from fastapi" not in result["generated_code"]
    assert "main.py" not in result["generated_code"]
    assert "Artisan Coffee" in result["generated_code"]


@pytest.mark.asyncio
async def test_implement_node_coffee_shop_landing_page_fallback_is_tsx():
    """Fallback when LLM is offline produces Next.js component (.tsx), NOT FastAPI E-Commerce even with 'shop' in goal."""
    from src.runtime.nodes import implement_node

    state = {
        "goal": "Build a modern landing page for a coffee shop using Next.js and Tailwind",
        "product_type": "website",
        "status": "verified",
        "run_id": "test-coffee-shop-fallback",
        "project_id": "coffee_shop_new_proj",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
    }

    with patch("src.ai_runtime.service.AIRuntimeService.complete", side_effect=RuntimeError("LLM unavailable")):
        result = await implement_node(state)

    assert result["filepath"] == "page.tsx"
    assert ".tsx" in result["generated_code"]
    assert "from fastapi" not in result["generated_code"]
    assert "main.py" not in result["generated_code"]
    assert "artisan coffee" in result["generated_code"].lower() or "coffee" in result["generated_code"].lower()


@pytest.mark.asyncio
async def test_explore_node_and_research_node_empty_workspace_isolation(tmp_path):
    """Empty workspace reports 'Empty workspace. Starting from scratch.' and never reads ASEP root backend/src."""
    from src.runtime.nodes import explore_node, research_phase_node
    from src.runtime.explore_manager import get_explore_manager
    import uuid

    unique_project_id = f"isolated_test_proj_{uuid.uuid4().hex[:8]}"

    state = {
        "goal": "Build a modern landing page for a coffee shop using Next.js and Tailwind",
        "current_phase": "explore",
        "project_id": unique_project_id,
        "workspace_id": unique_project_id,
        "thread_id": f"thread_{unique_project_id}",
    }

    res_explore = await explore_node(state)
    assert res_explore["status"] == "explored"
    assert res_explore["exploration_summary"]["architecture_understanding"] == "Empty workspace. Starting from scratch."
    assert res_explore["exploration_summary"]["relevant_files"] == []
    assert any("Empty workspace. Starting from scratch." in ev.get("detail", "") for ev in res_explore["exploration_events"])

    # Check global explore manager received it
    mgr = get_explore_manager()
    summary = mgr.get_summary(f"thread_{unique_project_id}", "explore")
    assert summary is not None
    assert summary["architecture_understanding"] == "Empty workspace. Starting from scratch."

    # Now test research_phase_node with empty workspace
    state_research = {
        "goal": "Build a modern landing page for a coffee shop using Next.js and Tailwind",
        "current_phase": "research",
        "project_id": unique_project_id,
        "workspace_id": unique_project_id,
        "thread_id": f"thread_{unique_project_id}",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    res_research = await research_phase_node(state_research)
    assert res_research["status"] == "verified"
    assert res_research["exploration_summary"]["architecture_understanding"] == "Empty workspace. Starting from scratch."
    assert res_research["exploration_summary"]["relevant_files"] == []
    assert not any("backend/src" in f for f in res_research["exploration_summary"]["relevant_files"])


@pytest.mark.asyncio
async def test_implement_node_alias_and_delegation():
    """Verify implement_node is exported from src.runtime.nodes and behaves as an alias to implement_phase_node."""
    from src.runtime.nodes import implement_node
    import inspect

    assert callable(implement_node)
    assert inspect.iscoroutinefunction(implement_node)


@pytest.mark.asyncio
async def test_implement_multi_file_nextjs_written_to_workspace():
    """Verify multi-file Next.js generation writes all artifact files to disk in workspaces/<project_id>/."""
    import uuid
    import json
    from pathlib import Path
    from src.runtime.nodes import implement_node, critic_node

    unique_project_id = f"test_proj_multi_{uuid.uuid4().hex[:8]}"
    state = {
        "goal": "Build a modern landing page for an organic tea brand using Next.js and Tailwind CSS",
        "product_type": "website",
        "project_id": unique_project_id,
        "workspace_id": unique_project_id,
        "thread_id": f"thread_{unique_project_id}",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": ["web-website-build"],
    }

    mock_llm_json = json.dumps({
        "package.json": json.dumps({"name": "organic-tea", "dependencies": {"next": "^14.2.0", "react": "^18.3.0"}}),
        "app/page.tsx": "import React from 'react';\nexport default function TeaPage() { return <main><h1>Pure Tea</h1></main>; }",
        "app/layout.tsx": "export default function RootLayout({ children }: { children: React.ReactNode }) { return <html><body>{children}</body></html>; }",
        "app/globals.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;",
    })
    mock_res = MagicMock()
    mock_res.text = f"```json\n{mock_llm_json}\n```"

    with patch("src.ai_runtime.service.AIRuntimeService.complete", new_callable=AsyncMock, return_value=mock_res):
        result = await implement_node(state)

    assert result["status"] == "verified"
    artifacts = result["artifacts"]
    assert "package.json" in artifacts
    assert "app/page.tsx" in artifacts
    assert "app/layout.tsx" in artifacts
    assert "app/globals.css" in artifacts

    # Verify primary entrypoint filepath and generated_code
    assert result["filepath"] == "app/page.tsx"
    assert result["generated_code"] == artifacts["app/page.tsx"]

    # Verify files were physically written to disk under workspaces/<project_id>/
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    workspace_dir = repo_root / "workspaces" / unique_project_id
    assert workspace_dir.exists()
    assert (workspace_dir / "package.json").exists()
    assert (workspace_dir / "app" / "page.tsx").exists()
    assert (workspace_dir / "app" / "layout.tsx").exists()
    assert (workspace_dir / "app" / "globals.css").exists()

    content_page = (workspace_dir / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "Pure Tea" in content_page

    # Now verify critic_node validates the workspace statically
    state["artifacts"] = artifacts
    state["generated_code"] = artifacts["app/page.tsx"]
    state["filepath"] = "app/page.tsx"

    critic_res = await critic_node(state)
    assert critic_res["status"] == "verified"
    assert critic_res["critic_result"]["passed"] is True
    assert "Frontend static validation passed" in critic_res["critic_result"]["stdout"]

    # Clean up test workspace directory
    import shutil
    shutil.rmtree(workspace_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_critic_node_frontend_validation_errors():
    """Verify critic_node detects invalid package.json syntax and missing page components."""
    from src.runtime.nodes import critic_node
    import uuid

    proj_id = f"test_proj_err_{uuid.uuid4().hex[:8]}"

    # Test 1: Invalid package.json (malformed JSON)
    bad_json_state = {
        "goal": "Build landing page",
        "project_id": proj_id,
        "filepath": "page.tsx",
        "active_skills": ["web-website-build"],
        "artifacts": {
            "package.json": "{ bad json: missing quotes }",
            "app/page.tsx": "export default function Page() { return <div>Home</div>; }",
        },
    }
    res_bad_json = await critic_node(bad_json_state)
    assert res_bad_json["status"] == "healing"
    assert "JSONDecodeError" in res_bad_json["critic_result"]["stderr"]

    # Test 2: Missing page component
    missing_page_state = {
        "goal": "Build landing page",
        "project_id": proj_id,
        "filepath": "package.json",
        "active_skills": ["web-website-build"],
        "artifacts": {
            "package.json": '{"name": "test"}',
        },
    }
    res_missing_page = await critic_node(missing_page_state)
    assert res_missing_page["status"] == "healing"
    assert "Missing app/page.tsx" in res_missing_page["critic_result"]["stderr"]


@pytest.mark.asyncio
async def test_python_sandbox_tool_frontend_bypass():
    """Verify PythonSandboxTool detects frontend code and validates statically without Python syntax errors."""
    from src.tools.python_sandbox import PythonSandboxTool

    tool = PythonSandboxTool()

    # Next.js TSX code
    tsx_code = (
        "import React from 'react';\n"
        "export default function Hero() {\n"
        "  return <section><h1>Welcome</h1></section>;\n"
        "}"
    )
    res_tsx = await tool.execute({"code": tsx_code})
    assert res_tsx.success is True
    assert "validated successfully" in res_tsx.result["output"].lower()

    # Broken TSX code (unclosed brace)
    bad_tsx = (
        "import React from 'react';\n"
        "export default function Hero() {\n"
        "  return <section><h1>Welcome</h1></section>;\n"
    )
    res_bad = await tool.execute({"code": bad_tsx})
    assert res_bad.success is False
    assert "SyntaxError" in res_bad.error

    # package.json
    res_pkg = await tool.execute({"code": '{"name": "nextjs-demo", "version": "1.0.0"}'})
    assert res_pkg.success is True


@pytest.mark.asyncio
async def test_restricted_executor_tsx_validation_edge_cases():
    """Verify RestrictedExecutor catches unclosed brackets and handles apostrophes in comments."""
    from src.services.restricted_code_sandbox import RestrictedExecutor

    # 1. Unclosed brace
    valid, err = RestrictedExecutor.validate_syntax("export default function Page() { return 1;")
    assert valid is False
    assert "Unclosed bracket" in err

    # 2. Comment with apostrophe followed by extra closing bracket
    valid, err = RestrictedExecutor.validate_syntax("// It's an awesome coffee shop\nexport default function Page() { return 1; } }")
    assert valid is False
    assert "Unmatched closing bracket" in err

    # 3. Valid TSX with comment containing apostrophe
    valid, err = RestrictedExecutor.validate_syntax("// It's an awesome coffee shop\nexport default function Page() { return 1; }")
    assert valid is True
    assert err is None






