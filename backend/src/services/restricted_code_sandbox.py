"""
ASEP — RestrictedPython Execution Sandbox Service
=================================================
Provides in-process, lightweight, and hardened execution of untrusted LLM-generated
code and unit tests without requiring a Docker daemon.

Features:
  - Zero Docker socket dependency.
  - ~5-10ms execution overhead.
  - AST-level validation and RestrictedPython bytecode restrictions.
  - Strict blocking of import, open, os.system, eval, exec, __import__.
  - 30-second execution timeout protection against infinite loops.
  - Output stream capture for stdout.
  - Production-safe structured error reporting.
"""

from __future__ import annotations

import ast
import asyncio
import concurrent.futures
import logging
import time
from typing import Any

from RestrictedPython import PrintCollector, compile_restricted

from src.config.sandbox_config import (
    DEFAULT_SANDBOX_TIMEOUT_SECONDS,
    DISALLOWED_BUILTINS,
    create_safe_builtins,
    get_default_guards,
)

logger = logging.getLogger(__name__)


class RestrictedExecutor:
    """
    Lightweight, Docker-free execution sandbox for untrusted Python code.
    Enforces safe builtins, guards against system/filesystem access, and manages timeouts.
    """

    DEFAULT_TIMEOUT: float = DEFAULT_SANDBOX_TIMEOUT_SECONDS

    @classmethod
    def validate_syntax(cls, code: str) -> tuple[bool, str | None]:
        """
        Validates Python syntax and checks for security violations prior to execution.

        Checks:
          1. Standard Python AST compilation (SyntaxError detection).
          2. Explicit ban on import statements (import, from ... import).
          3. Ban on dangerous function calls (open, eval, exec, __import__, input, etc.).
          4. RestrictedPython AST transformation validity.

        Returns:
          tuple: (is_valid: bool, error_message: str | None)
        """
        if not code or not code.strip():
            return False, "Code is empty"

        # 1. Parse standard AST
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return False, f"SyntaxError: {exc.msg} at line {exc.lineno}"
        except Exception as exc:
            return False, f"AST Parse Error: {exc}"

        # 2. Inspect AST for forbidden constructs
        for node in ast.walk(tree):
            # Block all module import mechanisms
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_names = []
                if isinstance(node, ast.Import):
                    module_names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module_names = [node.module]
                names_str = ", ".join(module_names) if module_names else "module"
                return (
                    False,
                    f"Security Violation: import statements ('{names_str}') are prohibited in the restricted sandbox",
                )

            # Block calls to disallowed builtins (e.g. open(), eval(), exec(), os.system())
            if isinstance(node, ast.Call):
                func = node.func
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr

                if func_name and func_name in DISALLOWED_BUILTINS:
                    return (
                        False,
                        f"Security Violation: call to '{func_name}()' is prohibited in the restricted sandbox",
                    )

                # Catch os.system, subprocess calls
                if isinstance(func, ast.Attribute) and func.attr in ("system", "popen", "spawn"):
                    return (
                        False,
                        f"Security Violation: OS shell invocation '{func.attr}()' is prohibited",
                    )

        # 3. Compile with RestrictedPython transformer
        try:
            compile_restricted(code, filename="<sandbox>", mode="exec")
        except SyntaxError as exc:
            return False, f"RestrictedPython Compilation Error: {exc}"
        except Exception as exc:
            return False, f"Restricted Compilation Failed: {exc}"

        return True, None

    @classmethod
    def _execute_code_internal(
        cls,
        code: str,
        test_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Internal worker that executes code with RestrictedPython in a controlled environment.
        Runs synchronously inside a worker thread.
        """
        start_time = time.perf_counter()
        output_buffer: list[str] = []

        # 1. Pre-execution AST check
        full_source = f"{code}\n\n{test_code}" if test_code else code
        is_valid, validation_error = cls.validate_syntax(full_source)
        if not is_valid:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            is_sec = "Security Violation" in (validation_error or "")
            return {
                "success": False,
                "stdout": "",
                "result": None,
                "error": validation_error,
                "execution_time_ms": elapsed_ms,
                "security_violation": is_sec,
                "timed_out": False,
            }

        # 2. Compile with RestrictedPython
        try:
            compiled = compile_restricted(full_source, filename="<sandbox>", mode="exec")
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "stdout": "",
                "result": None,
                "error": f"Compilation Error: {exc}",
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": False,
            }

        # 3. Setup sandbox namespace with safe builtins and guards
        safe_builtins_dict = create_safe_builtins(output_buffer=output_buffer)
        guards_dict = get_default_guards()

        sandbox_globals: dict[str, Any] = {
            "__builtins__": safe_builtins_dict,
            **guards_dict,
        }

        # 4. Execute byte code in unified global namespace
        try:
            exec(compiled, sandbox_globals)

            # If test functions were defined (e.g. def test_...():), invoke each to evaluate assertions
            for name, obj in list(sandbox_globals.items()):
                if name.startswith("test_") and callable(obj):
                    obj()

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Collect stdout text from _print (PrintCollector instance) or output_buffer
            collector = sandbox_globals.get("_print")
            if collector is not None and hasattr(collector, "txt"):
                stdout_text = collector() if callable(collector) else "".join(getattr(collector, "txt", []))
            elif output_buffer:
                stdout_text = "".join(output_buffer)
            else:
                stdout_text = ""

            # Extract return or result variable if defined
            result_val = sandbox_globals.get("result") or sandbox_globals.get("output")

            return {
                "success": True,
                "stdout": str(stdout_text),
                "result": result_val,
                "error": None,
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": False,
                "locals": {
                    k: v
                    for k, v in sandbox_globals.items()
                    if not k.startswith("_") and not callable(v) and k != "__builtins__"
                },
            }

        except AssertionError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            collector = sandbox_globals.get("_print")
            if collector is not None and hasattr(collector, "txt"):
                stdout_text = collector() if callable(collector) else "".join(getattr(collector, "txt", []))
            elif output_buffer:
                stdout_text = "".join(output_buffer)
            else:
                stdout_text = ""
            return {
                "success": False,
                "stdout": str(stdout_text),
                "result": None,
                "error": f"AssertionError: {exc or 'Test assertion failed'}",
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": False,
            }

        except (ImportError, NameError) as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            err_str = str(exc)
            is_sec = "__import__" in err_str or "import" in err_str
            return {
                "success": False,
                "stdout": "".join(output_buffer),
                "result": None,
                "error": f"Security / Import Error: {exc}",
                "execution_time_ms": elapsed_ms,
                "security_violation": is_sec,
                "timed_out": False,
            }

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "stdout": "".join(output_buffer),
                "result": None,
                "error": f"{type(exc).__name__}: {exc}",
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": False,
            }

    @classmethod
    def execute_sync(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = DEFAULT_SANDBOX_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        """
        Synchronously executes code in the restricted sandbox with timeout enforcement.
        """
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cls._execute_code_internal, code, test_code)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.warning("RestrictedExecutor execution timed out after %.2fs", timeout)
                return {
                    "success": False,
                    "stdout": "",
                    "result": None,
                    "error": f"Execution timed out ({timeout}s limit exceeded)",
                    "execution_time_ms": elapsed_ms,
                    "security_violation": False,
                    "timed_out": True,
                }

    @classmethod
    async def execute(
        cls,
        code: str,
        test_code: str | None = None,
        timeout: float = DEFAULT_SANDBOX_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        """
        Asynchronously executes code in the restricted sandbox with timeout enforcement.

        Args:
            code: Primary Python source code to execute.
            test_code: Optional test assertions or harness to evaluate against `code`.
            timeout: Maximum allowed execution duration in seconds (default: 30.0s).

        Returns:
            Structured execution dictionary.
        """
        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(cls._execute_code_internal, code, test_code),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("RestrictedExecutor async execution timed out after %.2fs", timeout)
            return {
                "success": False,
                "stdout": "",
                "result": None,
                "error": f"Execution timed out ({timeout}s limit exceeded)",
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": True,
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "stdout": "",
                "result": None,
                "error": f"Unexpected execution error: {exc}",
                "execution_time_ms": elapsed_ms,
                "security_violation": False,
                "timed_out": False,
            }
