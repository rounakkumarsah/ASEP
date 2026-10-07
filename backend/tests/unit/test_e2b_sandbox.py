import os
from unittest.mock import MagicMock, patch
import pytest

from src.services.e2b_sandbox import (
    SandboxExecutionResult,
    execute_code_with_fallback,
    get_e2b_api_key,
    is_e2b_configured,
)
from src.utils.self_healing import SandboxRunner
from src.runtime.nodes import implement_phase_node


def test_is_e2b_configured():
    with patch.dict(os.environ, {}, clear=True):
        assert not is_e2b_configured()

    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_test_key_123"}):
        assert is_e2b_configured()
        assert get_e2b_api_key() == "e2b_test_key_123"


@pytest.mark.asyncio
async def test_execute_code_fallback_when_no_key():
    """When E2B_API_KEY is absent, seamlessly execute via RestrictedExecutor."""
    with patch.dict(os.environ, {}, clear=True):
        code = "result = 2 + 2\nprint('Result is 4')\n"
        res = await execute_code_with_fallback(code)
        assert res.exit_code == 0
        assert res.success is True
        assert res.execution_mode == "restricted_python"
        assert "Result is 4" in res.stdout
        assert len(res.stdout_lines) >= 1


@pytest.mark.asyncio
async def test_execute_code_fallback_error_handling():
    """Syntax or runtime errors in fallback sandbox return exit_code 1 without raising."""
    with patch.dict(os.environ, {}, clear=True):
        code = "print(undefined_variable_xyz)"
        res = await execute_code_with_fallback(code)
        assert res.exit_code != 0
        assert res.success is False
        assert "undefined_variable_xyz" in (res.stderr or res.error or "")


@pytest.mark.asyncio
async def test_execute_code_with_e2b_cloud_sandbox():
    """When E2B_API_KEY is configured, use E2B code execution."""
    mock_execution = MagicMock()
    mock_execution.logs.stdout = ["Hello from E2B cloud!"]
    mock_execution.logs.stderr = []
    mock_execution.error = None

    mock_sandbox = MagicMock()
    mock_sandbox.run_code.return_value = mock_execution
    mock_sandbox.__enter__.return_value = mock_sandbox
    mock_sandbox.__exit__.return_value = None

    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_valid_key"}):
        with patch("e2b_code_interpreter.Sandbox.create", return_value=mock_sandbox):
            res = await execute_code_with_fallback("print('Hello from E2B cloud!')")
            assert res.execution_mode == "e2b"
            assert res.exit_code == 0
            assert res.success is True
            assert "Hello from E2B cloud!" in res.stdout


@pytest.mark.asyncio
async def test_execute_code_e2b_failure_falls_back_seamlessly():
    """When E2B fails, seamlessly fallback to local sandbox."""
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_key_causing_network_error"}):
        with patch("src.services.e2b_sandbox.execute_e2b_sync", side_effect=RuntimeError("E2B cluster timeout")):
            res = await execute_code_with_fallback("print('Fallback ran successfully')")
            assert res.execution_mode == "restricted_python"
            assert res.exit_code == 0
            assert "Fallback ran successfully" in res.stdout


@pytest.mark.asyncio
async def test_implement_phase_node_executes_code_and_streams_events():
    """After Implement phase, generated code is executed and stdout/stderr events are emitted."""
    state = {
        "goal": "Write a python calculator function",
        "product_type": "api",
        "status": "verified",
        "run_id": "test-implement-exec",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
        "active_skills": [],
        "skill_instructions": [],
        "skill_citations": [],
        "code_context": "def calc(a, b):\n    return a + b\nprint('Calc test: 10 + 20 =', calc(10, 20))\n",
    }

    result = await implement_phase_node(state)
    assert result["status"] == "verified"
    assert "execution_result" in result
    assert result["execution_result"]["exit_code"] == 0

    messages = result.get("messages", [])
    # Check that execution messages were appended
    assert any("[Sandbox]" in m.get("content", "") for m in messages)
    stdout_msgs = [m for m in messages if m.get("role") == "stdout" or m.get("type") == "output"]
    assert len(stdout_msgs) >= 1
    assert any("Calc test" in m.get("content", "") for m in messages)
    assert any("[Sandbox Exit]" in m.get("content", "") for m in messages)


def test_sandbox_runner_wires_e2b():
    """SandboxRunner.run_code prioritizes E2B if E2B_API_KEY is configured."""
    mock_e2b_res = SandboxExecutionResult(
        exit_code=0,
        stdout="E2B output line",
        stderr="",
        stdout_lines=["E2B output line"],
        execution_mode="e2b",
    )
    with patch("src.services.e2b_sandbox.is_e2b_configured", return_value=True):
        with patch("src.services.e2b_sandbox.execute_e2b_sync", return_value=mock_e2b_res):
            res = SandboxRunner.run_code("print('testing runner')")
            assert res.exit_code == 0
            assert res.execution_mode == "e2b"
            assert "E2B output line" in res.stdout


@pytest.mark.asyncio
async def test_execute_code_fallback_invokes_streaming_callbacks():
    """Fallback execution properly calls on_stdout and on_stderr callbacks."""
    out_lines = []
    err_lines = []

    with patch.dict(os.environ, {}, clear=True):
        code = "print('line 1')\nprint('line 2')\n"
        res = await execute_code_with_fallback(
            code,
            on_stdout=lambda l: out_lines.append(l),
            on_stderr=lambda l: err_lines.append(l),
        )
        assert res.exit_code == 0
        assert len(out_lines) >= 2
        assert "line 1" in out_lines[0]
        assert "line 2" in out_lines[1]


@pytest.mark.asyncio
async def test_execute_e2b_sync_captures_results():
    """execute_e2b_sync captures expression return text from execution.results."""
    from src.services.e2b_sandbox import execute_e2b_sync

    mock_res_item = MagicMock()
    mock_res_item.text = "42"

    mock_execution = MagicMock()
    mock_execution.logs.stdout = []
    mock_execution.logs.stderr = []
    mock_execution.results = [mock_res_item]
    mock_execution.error = None

    mock_sandbox = MagicMock()
    mock_sandbox.run_code.return_value = mock_execution
    mock_sandbox.__enter__.return_value = mock_sandbox
    mock_sandbox.__exit__.return_value = None

    captured = []
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_key_results"}):
        with patch("e2b_code_interpreter.Sandbox.create", return_value=mock_sandbox):
            res = execute_e2b_sync("21 * 2", on_stdout=lambda l: captured.append(l))
            assert res.exit_code == 0
            assert "42" in res.stdout
            assert "42" in captured


@pytest.mark.asyncio
async def test_terminal_execute_uses_e2b_sandbox():
    """POST /api/v1/sandbox/terminal/execute routes python code via E2B when key is present."""
    from src.api.routers.sandbox import terminal_execute, TerminalRequest

    mock_e2b_res = SandboxExecutionResult(
        exit_code=0,
        stdout="Routed via E2B",
        stderr="",
        execution_mode="e2b",
    )
    with patch("src.services.e2b_sandbox.execute_code_with_fallback", return_value=mock_e2b_res):
        req = TerminalRequest(command="python -c 'print(\"Routed via E2B\")'")
        resp = await terminal_execute(req)
        assert resp["exit_code"] == 0
        assert resp["stdout"] == "Routed via E2B"


@pytest.mark.asyncio
async def test_stream_python_execution_with_e2b():
    """POST /api/v1/sandbox/python/stream streams E2B events when E2B_API_KEY is configured."""
    from src.api.routers.sandbox import stream_python_execution, SandboxRunRequest

    mock_e2b_res = SandboxExecutionResult(
        exit_code=0,
        stdout="Hello stream line 1\nHello stream line 2",
        stderr="",
        execution_mode="e2b",
    )
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_stream_key"}):
        with patch("src.services.e2b_sandbox.execute_e2b_sync", return_value=mock_e2b_res):
            req = SandboxRunRequest(code="print('Hello stream')")
            resp = await stream_python_execution(req)
            body_chunks = []
            async for chunk in resp.body_iterator:
                body_chunks.append(chunk)

            full_body = "".join(body_chunks)
            assert "Executing code in E2B cloud sandbox" in full_body
            assert "Hello stream line 1" in full_body
            assert "[Process exited with code 0]" in full_body
            assert "[DONE]" in full_body
