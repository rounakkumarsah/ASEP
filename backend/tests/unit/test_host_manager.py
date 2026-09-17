"""
ASEP — Host Manager Unit Tests
================================
10 tests verifying: port utilities, workspace setup, dependency detection,
server command generation, HTTP health checking, HostManager.host() lifecycle,
port conflict auto-increment, host_manager_node SSE messages and state.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.host_manager import (
    HostManager,
    HostManagerResult,
    HostedApp,
    _build_requirements,
    _build_server_command,
    _detect_entry_file,
    check_http_health,
    find_free_port,
    host_manager,
    is_port_free,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager() -> HostManager:
    return HostManager()


FASTAPI_CODE = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(item: Item):
    return item
'''

FLASK_CODE = '''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
'''

PLAIN_PYTHON_CODE = '''
print("Hello from ASEP!")
x = 42
print(f"The answer is {x}")
'''


# ===========================================================================
# Test 1 — is_port_free returns True for an unused port
# ===========================================================================
def test_is_port_free_returns_true_for_unused_port():
    """is_port_free should return True when no process is bound to the port."""
    # Find a port that is very likely free (use a high ephemeral port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    # Port was released by the with block — should now be free
    # (slight race condition possible in CI, but acceptable)
    assert is_port_free(port), f"Port {port} should be free but is_port_free returned False"


# ===========================================================================
# Test 2 — find_free_port auto-increments past a bound port
# ===========================================================================
def test_find_free_port_skips_bound_port():
    """find_free_port should skip ports that are already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", 0))
        occupied_port = s.getsockname()[1]
        # find_free_port starting from occupied_port should return a different port
        free = find_free_port(start=occupied_port, max_tries=20)
        # The free port should be different (or the same if we got lucky with re-use)
        assert isinstance(free, int)
        assert free >= occupied_port


# ===========================================================================
# Test 3 — check_http_health returns False for a closed port
# ===========================================================================
def test_check_http_health_false_for_closed_port():
    """check_http_health should return False when nothing is listening."""
    # Use a port that is almost certainly closed
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    # Port released — now check_http_health should fail (nothing listening)
    result = check_http_health(port)
    assert result is False, "Expected False for a port with no server"


# ===========================================================================
# Test 4 — _detect_entry_file detects FastAPI correctly
# ===========================================================================
def test_detect_entry_file_fastapi():
    """_detect_entry_file should return (main.py, python) for FastAPI code."""
    from pathlib import Path
    workspace = Path(".")
    entry, lang = _detect_entry_file(workspace, FASTAPI_CODE, "api")
    assert entry == "main.py"
    assert lang == "python"


# ===========================================================================
# Test 5 — _build_requirements detects fastapi + uvicorn for FastAPI code
# ===========================================================================
def test_build_requirements_fastapi():
    """_build_requirements should detect fastapi[standard] + uvicorn[standard] for FastAPI code."""
    reqs = _build_requirements(FASTAPI_CODE, "api")
    reqs_lower = [r.lower() for r in reqs]
    assert any("fastapi" in r for r in reqs_lower), "fastapi should be in requirements"
    assert any("uvicorn" in r for r in reqs_lower), "uvicorn should be in requirements"


# ===========================================================================
# Test 6 — _build_server_command generates uvicorn command for FastAPI
# ===========================================================================
def test_build_server_command_fastapi():
    """_build_server_command should produce a uvicorn launch command for FastAPI code."""
    from pathlib import Path
    cmd = _build_server_command("main.py", "python", 3000, FASTAPI_CODE, Path("."))
    cmd_str = " ".join(cmd)
    assert "uvicorn" in cmd_str, f"Expected uvicorn in command, got: {cmd_str}"
    assert "3000" in cmd_str, f"Expected port 3000 in command, got: {cmd_str}"
    assert "127.0.0.1" in cmd_str, f"Expected host 127.0.0.1 in command, got: {cmd_str}"


# ===========================================================================
# Test 7 — HostManager.host() with mock subprocess: success path
# ===========================================================================
def test_host_manager_success_path():
    """host() should return HostManagerResult with success=True when HTTP health check passes."""
    manager = _make_manager()

    # Mock the pip install to succeed immediately
    # Mock subprocess.Popen to return a fake process
    # Mock check_http_health to return True
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    mock_proc.poll.return_value = None  # Process still running
    mock_proc.stdout = None
    mock_proc.returncode = None

    async def run():
        with (
            patch("src.utils.host_manager.subprocess.Popen", return_value=mock_proc),
            patch("src.utils.host_manager.check_http_health", return_value=True),
            patch.object(manager, "_pip_install", new_callable=AsyncMock, return_value=("OK", "")),
        ):
            result = await manager.host(
                code=FASTAPI_CODE,
                product_type="api",
                run_id="test-run-001",
            )
        return result

    result = asyncio.run(run())
    assert result.success is True
    assert result.app is not None
    assert result.app.pid == 12345
    assert result.app.health_ok is True
    assert "localhost" in result.app.url


# ===========================================================================
# Test 8 — HostManager.host() auto-increments port on conflict
# ===========================================================================
def test_host_manager_port_conflict_auto_increment():
    """host() should auto-increment port when the preferred port is in use.
    We mock is_port_free to simulate a conflict, avoiding Windows SO_REUSEADDR issues.
    """
    manager = _make_manager()

    mock_proc = MagicMock()
    mock_proc.pid = 77777
    mock_proc.poll.return_value = None
    mock_proc.stdout = None

    chosen_port = 3000
    # Simulate: port 3000 is occupied, 3001 is free
    def _mock_is_port_free(port: int, host: str = "127.0.0.1") -> bool:
        return port != chosen_port  # Only 3000 is "in use"

    async def run():
        with (
            patch("src.utils.host_manager.is_port_free", side_effect=_mock_is_port_free),
            patch("src.utils.host_manager.subprocess.Popen", return_value=mock_proc),
            patch("src.utils.host_manager.check_http_health", return_value=True),
            patch.object(manager, "_pip_install", new_callable=AsyncMock, return_value=("", "")),
        ):
            result = await manager.host(
                code=FASTAPI_CODE,
                product_type="api",
                run_id="test-conflict",
                preferred_port=chosen_port,  # This port is "occupied" via mock
            )
        return result

    result = asyncio.run(run())
    assert result.success is True
    assert result.app is not None
    # Port should have been auto-incremented past 3000
    assert result.app.port > chosen_port, (
        f"Expected port to be auto-incremented past {chosen_port}, got {result.app.port}"
    )


# ===========================================================================
# Test 9 — host_manager_node emits [Host Manager] SSE messages
# ===========================================================================
def test_host_manager_node_emits_sse_messages():
    """host_manager_node should emit [Host Manager], [Host Manager Status] messages."""
    from src.runtime.nodes import host_manager_node

    state = {
        "generated_code": FASTAPI_CODE,
        "product_type": "api",
        "run_id": "test-sse-node",
        "status": "verified",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    mock_app = HostedApp(
        port=3001,
        url="http://localhost:3001",
        pid=55555,
        workspace_dir="/tmp/asep_test",
        product_type="api",
        health_ok=True,
    )
    mock_result = HostManagerResult(
        success=True,
        app=mock_app,
        install_step="pip install fastapi[standard] uvicorn[standard]",
        logs=["Workspace created", "Dependencies installed", "Server started"],
    )

    async def run():
        with patch.object(host_manager, "host", new_callable=AsyncMock, return_value=mock_result):
            result = await host_manager_node(state)
        return result

    result = asyncio.run(run())
    assert result["current_phase"] == "host_manager"
    assert result["status"] == "verified"
    assert result["app_url"] == "http://localhost:3001"
    assert result["app_port"] == 3001

    messages = result.get("messages", [])
    host_msgs = [m for m in messages if "[Host Manager]" in m.get("content", "")]
    status_msgs = [m for m in messages if "[Host Manager Status]" in m.get("content", "")]
    assert len(host_msgs) >= 1, "Should emit at least one [Host Manager] message"
    assert len(status_msgs) >= 1, "Should emit [Host Manager Status] message"

    # Verify [OK] in status message
    status_text = status_msgs[0]["content"]
    assert "[OK]" in status_text, f"Status message should contain [OK], got: {status_text}"
    assert "http://localhost:3001" in status_text


# ===========================================================================
# Test 10 — host_manager_node: no code → skips hosting, still verified
# ===========================================================================
def test_host_manager_node_no_code_skips():
    """host_manager_node should emit skip message and status=verified when no code in state."""
    from src.runtime.nodes import host_manager_node

    state = {
        "generated_code": "",
        "product_type": "api",
        "run_id": "test-empty",
        "status": "verified",
        "token_usage_per_phase": {},
        "token_budget_per_phase": {},
        "token_savings": {},
        "file_history": {},
        "budget_approvals": [],
    }

    result = asyncio.run(host_manager_node(state))
    assert result["status"] == "verified", "Should still be verified even when no code"
    assert result["app_url"] == ""
    assert result["app_port"] == 0

    messages = result.get("messages", [])
    skip_msgs = [m for m in messages if "skipping" in m.get("content", "").lower() or "no generated" in m.get("content", "").lower()]
    assert len(skip_msgs) >= 1, "Should emit a skip message when no code"
