"""
ASEP — Sandbox Service Facade
=============================
Provides a unified interface for code execution in Docker and RestrictedPython sandboxes.
Gracefully handles serverless and Docker-free environments.
"""

from __future__ import annotations

from typing import Any

from src.services.restricted_code_sandbox import (
    RestrictedExecutor,
    RestrictedSandboxResult,
)

__all__ = ["RestrictedExecutor", "RestrictedSandboxResult", "SandboxService"]


class SandboxService:
    """Service facade for executing code in sandboxed environments."""

    @classmethod
    async def execute(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = 30.0,
    ) -> RestrictedSandboxResult:
        return await RestrictedExecutor.execute(code, test_code=test_code, timeout=timeout)

    @classmethod
    def execute_sync(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = 30.0,
    ) -> RestrictedSandboxResult:
        return RestrictedExecutor.execute_sync(code, test_code=test_code, timeout=timeout)
