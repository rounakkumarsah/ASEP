"""
ASEP — RestrictedPython Execution Sandbox Test Suite
====================================================
Tests verifying:
1. Sandbox blocks forbidden primitives: `import os`, `os.system`, `open('/etc/passwd')`, `eval`, `exec`.
2. Sandbox allows safe Python constructs: loops, functions, comprehensions, math, collections, print.
3. Timeout protection terminates long-running code without hanging main process.
4. Error handling gracefully handles syntax errors, zero division, index errors without crashing.
5. Test assertion runner detects passing and failing tests.
6. Supervisor nodes (`code_write_node` and `test_gen_node`) integrate with sandbox.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.state import AgentState
from src.agents.supervisor import code_write_node, test_gen_node
from src.ai_runtime.contracts import CompletionResponse, UsageInfo
from src.services.restricted_code_sandbox import RestrictedExecutor


# ---------------------------------------------------------------------------
# Security Blocking Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_blocks_import_statements():
    """Verify that all import mechanisms (import, from ... import) are strictly blocked."""
    prohibited_snippets = [
        "import os",
        "import sys",
        "import subprocess",
        "from os import system",
        "from pathlib import Path",
        "__import__('os').system('ls')",
    ]

    for snippet in prohibited_snippets:
        # Pre-execution validation check
        is_valid, error_msg = RestrictedExecutor.validate_syntax(snippet)
        assert is_valid is False, f"validate_syntax failed to block: {snippet}"
        assert "import" in error_msg.lower() or "prohibited" in error_msg.lower() or "forbidden" in error_msg.lower()

        # Full execution check
        result = await RestrictedExecutor.execute(snippet)
        assert result["success"] is False, f"execute() failed to block: {snippet}"
        assert result["security_violation"] is True
        assert result["error"] is not None


@pytest.mark.asyncio
async def test_sandbox_blocks_open_filesystem_access():
    """Verify that filesystem operations via open() are blocked."""
    file_snippets = [
        "f = open('/etc/passwd', 'r')",
        "with open('secret.txt', 'w') as f: f.write('hacked')",
        "data = open('C:\\\\Windows\\\\System32\\\\cmd.exe').read()",
    ]

    for snippet in file_snippets:
        is_valid, error_msg = RestrictedExecutor.validate_syntax(snippet)
        assert is_valid is False
        assert "open" in error_msg.lower() or "prohibited" in error_msg.lower()

        result = await RestrictedExecutor.execute(snippet)
        assert result["success"] is False
        assert result["security_violation"] is True


@pytest.mark.asyncio
async def test_sandbox_blocks_os_system_eval_exec_and_globals():
    """Verify that execution of system commands, eval, exec, globals are blocked."""
    dangerous_snippets = [
        "eval('2 + 2')",
        "exec('a = 10')",
        "os.system('id')",
        "globals()",
        "locals()",
        "input('Enter pass: ')",
    ]

    for snippet in dangerous_snippets:
        result = await RestrictedExecutor.execute(snippet)
        assert result["success"] is False
        assert result["security_violation"] is True


# ---------------------------------------------------------------------------
# Permitted Functionality Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_allows_loops_functions_and_comprehensions():
    """Verify that safe Python constructs execute with minimal latency (~5-10ms)."""
    valid_code = """
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [x for x in range(20) if is_prime(x)]
squares = {x: x * x for x in primes}
print("Calculated primes:", primes)
result = primes
"""
    start = time.perf_counter()
    res = await RestrictedExecutor.execute(valid_code)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert res["success"] is True
    assert res["error"] is None
    assert res["security_violation"] is False
    assert res["result"] == [2, 3, 5, 7, 11, 13, 17, 19]
    assert "Calculated primes: [2, 3, 5, 7, 11, 13, 17, 19]" in res["stdout"]

    # Latency check: execution overhead should be very lightweight (< 50ms total)
    assert res["execution_time_ms"] < 50.0, f"Overhead was {res['execution_time_ms']}ms"


@pytest.mark.asyncio
async def test_sandbox_allows_math_and_collections():
    """Verify built-in math and collection utilities work seamlessly."""
    code = """
import_free_numbers = [4.5, 2.1, 9.8, 1.3]
min_val = min(import_free_numbers)
max_val = max(import_free_numbers)
sum_val = sum(import_free_numbers)
sorted_vals = sorted(import_free_numbers)
floored = math.floor(min_val)
result = {"min": min_val, "max": max_val, "sum": sum_val, "floored": floored}
"""
    res = await RestrictedExecutor.execute(code)
    assert res["success"] is True
    assert res["result"]["min"] == 1.3
    assert res["result"]["max"] == 9.8
    assert res["result"]["floored"] == 1


# ---------------------------------------------------------------------------
# Timeout Protection Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_timeout_terminates_execution():
    """Verify that execution exceeding the configured timeout is safely terminated."""
    slow_code = """
count = 0
for i in range(10000000):
    count += i
"""
    # Execute with 0.05s timeout
    res = await RestrictedExecutor.execute(slow_code, timeout=0.05)
    assert res["success"] is False
    assert res["timed_out"] is True
    assert "timed out" in res["error"].lower()


# ---------------------------------------------------------------------------
# Error Handling & Edge Cases Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_graceful_error_handling_malformed_syntax():
    """Verify malformed code returns clean structured errors without crashing."""
    malformed_snippets = [
        ("def broken_func(: pass", "SyntaxError"),
        ("x = [1, 2, 3", "SyntaxError"),
        ("1 / 0", "ZeroDivisionError"),
        ("items = []\nx = items[5]", "IndexError"),
    ]

    for snippet, expected_err in malformed_snippets:
        res = await RestrictedExecutor.execute(snippet)
        assert res["success"] is False
        assert expected_err.lower() in res["error"].lower()
        assert res["timed_out"] is False


@pytest.mark.asyncio
async def test_sandbox_unit_test_assertion_evaluation():
    """Verify that test functions with assertions are automatically discovered and evaluated."""
    code = """
def multiply(a, b):
    return a * b
"""
    passing_tests = """
def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-1, 5) == -5
    assert multiply(0, 100) == 0
"""
    res_pass = await RestrictedExecutor.execute(code=code, test_code=passing_tests)
    assert res_pass["success"] is True
    assert res_pass["error"] is None

    failing_tests = """
def test_multiply_fail():
    assert multiply(2, 2) == 5
"""
    res_fail = await RestrictedExecutor.execute(code=code, test_code=failing_tests)
    assert res_fail["success"] is False
    assert "AssertionError" in res_fail["error"]


# ---------------------------------------------------------------------------
# Supervisor Node Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_code_write_node_validates_syntax_with_sandbox(monkeypatch):
    """Verify code_write_node rejects code that fails syntax/security validation."""
    mock_router = MagicMock()
    # Mock LLM output containing prohibited import
    mock_router.execute_task = AsyncMock(
        return_value=("import os\ndef bad(): pass", 100, "groq")
    )
    monkeypatch.setattr("src.agents.supervisor.router", mock_router)

    state: AgentState = {
        "goal": "Write bad code",
        "current_step": 0,
        "run_id": "test-run",
        "messages": [],
    }

    result = await code_write_node(state)
    assert result["error"] is not None
    assert "syntax validation failed" in result["error"].lower() or "security violation" in result["error"].lower()
    assert result.get("is_complete") is False


@pytest.mark.asyncio
async def test_test_gen_node_runs_tests_in_sandbox(monkeypatch):
    """Verify test_gen_node executes generated tests in RestrictedExecutor."""
    mock_router = MagicMock()
    # Mock LLM output with valid test code
    mock_router.execute_task = AsyncMock(
        return_value=(
            "def test_square():\n    assert square(4) == 16",
            120,
            "openrouter",
        )
    )
    monkeypatch.setattr("src.agents.supervisor.router", mock_router)

    state: AgentState = {
        "code": "def square(n):\n    return n * n",
        "goal": "Write square function",
        "current_step": 2,
        "run_id": "test-run",
        "messages": [],
    }

    result = await test_gen_node(state)
    assert result["error"] is None
    assert result["is_complete"] is True
    assert result["tests"] is not None
    assert result["test_results"]["success"] is True
    assert "passed sandbox verification" in result["final_output"].lower()
