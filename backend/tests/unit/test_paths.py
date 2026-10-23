"""
Unit tests for dynamic workspace path helper (src/utils/paths.py).
Validates dynamic path resolution in local dev vs. serverless (Vercel, AWS Lambda) environments.
"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from src.utils.paths import get_workspaces_dir


def test_get_workspaces_dir_local(monkeypatch):
    """In local environment without VERCEL or AWS_LAMBDA_FUNCTION_NAME, uses local workspaces dir."""
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)

    ws_dir = get_workspaces_dir()
    assert isinstance(ws_dir, Path)
    assert ws_dir.name == "workspaces"
    assert ws_dir.exists()
    assert "tmp" not in str(ws_dir).lower() or os.name == "nt"  # On windows, temp is not /tmp


def test_get_workspaces_dir_vercel(monkeypatch, capsys):
    """When VERCEL=1 is set, uses /tmp/workspaces and prints 'Using /tmp/workspaces for Vercel'."""
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)

    ws_dir = get_workspaces_dir()
    assert isinstance(ws_dir, Path)
    assert str(ws_dir).replace("\\", "/").endswith("/tmp/workspaces") or ws_dir == Path("/tmp/workspaces")

    captured = capsys.readouterr()
    assert "Using /tmp/workspaces for Vercel" in captured.out


def test_get_workspaces_dir_aws_lambda(monkeypatch):
    """When AWS_LAMBDA_FUNCTION_NAME is set, uses /tmp/workspaces."""
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "asep-runtime-handler")

    ws_dir = get_workspaces_dir()
    assert isinstance(ws_dir, Path)
    assert str(ws_dir).replace("\\", "/").endswith("/tmp/workspaces") or ws_dir == Path("/tmp/workspaces")


@pytest.mark.asyncio
async def test_filesystem_tool_vercel_redirection(monkeypatch, tmp_path):
    """Verify FilesystemTool redirects relative 'workspaces/...' and '/var/task/workspaces/...' to get_workspaces_dir()."""
    from src.tools.impl import FilesystemTool

    # Force VERCEL mode and mock get_workspaces_dir to safe isolated tmp_path
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr("src.utils.paths.get_workspaces_dir", lambda: tmp_path)

    tool = FilesystemTool()

    # 1. Write using relative workspaces/project-x/demo.txt
    res_rel = await tool.execute({
        "action": "write",
        "path": "workspaces/project-x/demo.txt",
        "content": "hello world relative",
    })
    assert res_rel.success is True
    assert (tmp_path / "project-x" / "demo.txt").exists()
    assert (tmp_path / "project-x" / "demo.txt").read_text(encoding="utf-8") == "hello world relative"

    # 2. Write using absolute /var/task/workspaces/project-x/task.txt
    res_abs = await tool.execute({
        "action": "write",
        "path": "/var/task/workspaces/project-x/task.txt",
        "content": "hello world var task",
    })
    assert res_abs.success is True
    assert (tmp_path / "project-x" / "task.txt").exists()
    assert (tmp_path / "project-x" / "task.txt").read_text(encoding="utf-8") == "hello world var task"

    # 3. Read back using relative path
    res_read = await tool.execute({
        "action": "read",
        "path": "workspaces/project-x/demo.txt",
    })
    assert res_read.success is True
    assert res_read.result["content"] == "hello world relative"

    # 4. Traversal attempt blocked
    res_traversal = await tool.execute({
        "action": "read",
        "path": "workspaces/../../../../../../etc/passwd",
    })
    assert res_traversal.success is False
    assert "Security Policy Violation" in res_traversal.error

