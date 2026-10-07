"""
ASEP — Sandbox Service Facade
=============================
Provides a unified interface for code execution in E2B, Docker, and RestrictedPython sandboxes.
Gracefully handles serverless, Docker-free, and cloud sandbox environments.
"""

from __future__ import annotations

from typing import Any, Callable

from src.services.e2b_sandbox import (
    SandboxExecutionResult,
    execute_code_with_fallback,
    execute_e2b_sync,
    get_e2b_api_key,
    is_e2b_configured,
)
from src.services.restricted_code_sandbox import (
    RestrictedExecutor,
    RestrictedSandboxResult,
)

__all__ = [
    "RestrictedExecutor",
    "RestrictedSandboxResult",
    "SandboxExecutionResult",
    "SandboxService",
    "execute_code_with_fallback",
    "execute_e2b_sync",
    "get_e2b_api_key",
    "is_e2b_configured",
]


class SandboxService:
    """Service facade for executing code in sandboxed environments."""

    @classmethod
    async def execute(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = 30.0,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> SandboxExecutionResult | RestrictedSandboxResult:
        if test_code:
            return await RestrictedExecutor.execute(code, test_code=test_code, timeout=timeout)
        return await execute_code_with_fallback(code, timeout=timeout, on_stdout=on_stdout, on_stderr=on_stderr)

    @classmethod
    def execute_sync(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = 30.0,
    ) -> RestrictedSandboxResult:
        return RestrictedExecutor.execute_sync(code, test_code=test_code, timeout=timeout)
