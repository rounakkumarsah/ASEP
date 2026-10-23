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
