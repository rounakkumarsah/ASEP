"""
Tests for Sandbox API Router and RestrictedExecutor Graceful Fallbacks.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routers.sandbox import (
    router as sandbox_router,
    SandboxRunRequest,
    TerminalRequest,
    ExecuteRequest,
    stream_python_execution,
)
from src.services.restricted_code_sandbox import (
    RestrictedExecutor,
    RestrictedSandboxResult,
)
from src.tools.python_sandbox import PythonSandboxTool


app = FastAPI()
app.include_router(sandbox_router)
client = TestClient(app)


def test_restricted_sandbox_result_dual_interface():
    """Verify RestrictedSandboxResult supports both dictionary and attribute access."""
    data = {
        "success": True,
        "stdout": "output test\n",
        "result": 42,
        "error": None,
        "execution_time_ms": 1.5,
    }
    res = RestrictedSandboxResult(data)

    # Dict access
    assert res["success"] is True
    assert res["stdout"] == "output test\n"
    assert res["result"] == 42
    assert res["error"] is None
    assert res["exit_code"] == 0
    assert res["stderr"] == ""

    # Attribute access
    assert res.success is True
    assert res.stdout == "output test\n"
    assert res.exit_code == 0
    assert res.stderr == ""
    assert res.tests_passed is True
    assert res.warnings == []


def test_sandbox_config_exports_restricted_executor():
    """Verify src.config.sandbox_config re-exports RestrictedExecutor and RestrictedSandboxResult."""
    from src.config.sandbox_config import (
        RestrictedExecutor as ReExportedExecutor,
        RestrictedSandboxResult as ReExportedResult,
    )
    assert ReExportedExecutor is RestrictedExecutor
    assert ReExportedResult is RestrictedSandboxResult


@pytest.mark.asyncio
async def test_stream_python_execution_fallback_when_docker_unreachable():
    """Verify that when Docker is unreachable, execution falls back to RestrictedExecutor."""
    with patch("docker.from_env", side_effect=FileNotFoundError(2, "No such file or directory")):
        req = SandboxRunRequest(code="print('Hello from Restricted Sandbox')")
        response = await stream_python_execution(req)

        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        
        full_output = "".join(chunks)
        assert "Docker daemon unreachable" not in full_output
        assert "Running in isolated RestrictedPython sandbox..." in full_output
        assert "Hello from Restricted Sandbox" in full_output
        assert "[Process exited with code 0]" in full_output
        assert "[DONE]" in full_output


@pytest.mark.asyncio
async def test_stream_python_execution_serverless_env_bypass_docker(monkeypatch):
    """Verify that in serverless (VERCEL=1), Docker connection is not even attempted."""
    monkeypatch.setenv("VERCEL", "1")
    req = SandboxRunRequest(code="x = 10 * 5\nprint(f'Computed: {x}')")
    response = await stream_python_execution(req)

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    
    full_output = "".join(chunks)
    assert "Computed: 50" in full_output
    assert "[Process exited with code 0]" in full_output


@pytest.mark.asyncio
async def test_stream_python_execution_syntax_error_handled_gracefully():
    """Verify syntax error in sandbox code streams clean error without crashing."""
    with patch("docker.from_env", side_effect=Exception("Docker down")):
        req = SandboxRunRequest(code="def invalid_func(: pass")
        response = await stream_python_execution(req)

        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)

        full_output = "".join(chunks)
        assert "SyntaxError" in full_output
        assert "[Process exited with code 1]" in full_output


def test_terminal_execute_python_command():
    """Verify /terminal/execute runs python commands via RestrictedExecutor."""
    response = client.post(
        "/sandbox/terminal/execute",
        json={"command": "python -c \"print('Hello from CLI')\""},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Hello from CLI" in data["stdout"]
    assert data["exit_code"] == 0
    assert data["stderr"] == ""


def test_execute_code_endpoint():
    """Verify /execute endpoint executes code via RestrictedExecutor."""
    response = client.post(
        "/sandbox/execute",
        json={"code": "res = 2 ** 8\nprint(res)"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "256" in data["stdout"]
    assert data["success"] is True
    assert data["exit_code"] == 0


@pytest.mark.asyncio
async def test_python_sandbox_tool_fallback_on_serverless(monkeypatch):
    """Verify PythonSandboxTool uses RestrictedExecutor on serverless."""
    monkeypatch.setenv("VERCEL", "1")
    tool = PythonSandboxTool()
    res = await tool.execute({"code": "print('Tool executed safely')"})
    assert res.success is True
    assert "Tool executed safely" in res.result["output"]
    assert res.result["execution_mode"] == "restricted_python"
