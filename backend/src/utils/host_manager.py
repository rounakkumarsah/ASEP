"""
ASEP — Host Manager
====================
After all phases pass, the Host Manager:
  1. Installs dependencies (pip / npm) using PackageResolver for smart
     error classification and compliant-alternative resolution.
  2. Writes generated code to a temporary workspace directory.
  3. Starts the dev server / runs the app in a subprocess.
  4. Runs health checks (HTTP endpoint responds, no startup errors).
  5. Auto-increments port on conflict (address already in use).
  6. Emits live SSE-ready status messages for the Terminal tab.

No Docker required — uses Python subprocess + asyncio for portability
on Windows (works without WSL or Docker Desktop).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_PORT = 3000
_MAX_PORT_TRIES = 20
_HEALTH_CHECK_TIMEOUT = 30.0   # seconds to wait for server startup
_HEALTH_POLL_INTERVAL = 0.5    # seconds between health check polls
_INSTALL_TIMEOUT = 120         # seconds for pip/npm install


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class HostedApp:
    """A successfully hosted application instance."""
    port: int
    url: str
    pid: int
    workspace_dir: str
    product_type: str
    startup_logs: list[str] = field(default_factory=list)
    health_ok: bool = False
    install_output: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "url": self.url,
            "pid": self.pid,
            "workspace_dir": self.workspace_dir,
            "product_type": self.product_type,
            "startup_logs": self.startup_logs[:20],
            "health_ok": self.health_ok,
            "install_output": self.install_output[:500],
            "error": self.error,
        }


@dataclass
class HostManagerResult:
    """Full result of the host manager run."""
    success: bool
    app: HostedApp | None = None
    error: str = ""
    install_step: str = ""
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "app": self.app.to_dict() if self.app else None,
            "error": self.error,
            "install_step": self.install_step,
            "logs": self.logs,
        }


# ---------------------------------------------------------------------------
# Port utilities
# ---------------------------------------------------------------------------
def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if the given port is not currently bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_free_port(start: int = _DEFAULT_PORT, max_tries: int = _MAX_PORT_TRIES) -> int:
    """Find the next available port starting from `start`."""
    for port in range(start, start + max_tries):
        if is_port_free(port):
            return port
    raise RuntimeError(
        f"No free port found in range {start}–{start + max_tries}. "
        "Please free some ports and try again."
    )


def check_http_health(port: int, host: str = "127.0.0.1", path: str = "/") -> bool:
    """
    Try a simple HTTP GET to http://host:port/path.
    Returns True if a response (any status code < 600) is received.
    Uses only stdlib to avoid extra dependencies.
    """
    import http.client
    try:
        conn = http.client.HTTPConnection(host, port, timeout=2)
        conn.request("GET", path)
        resp = conn.getresponse()
        conn.close()
        return resp.status < 600
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------
def _detect_entry_file(workspace: Path, code: str, product_type: str) -> tuple[str, str]:
    """
    Returns (entry_filename, language) for the generated code.
    Detects based on product_type and code content.
    """
    code_lower = code.lower()

    # FastAPI / Flask / Django (Python)
    if (
        "fastapi" in code_lower
        or "flask" in code_lower
        or "django" in code_lower
        or product_type in ("api", "fastapi", "flask")
    ):
        return ("main.py", "python")

    # React / Next.js / Vue (Node)
    if (
        "react" in code_lower
        or "next" in code_lower
        or "vue" in code_lower
        or product_type in ("react", "nextjs", "vue", "website")
    ):
        return ("index.js", "node")

    # Plain Python fallback
    if "print(" in code or "def " in code or "import " in code:
        return ("main.py", "python")

    # Default
    return ("main.py", "python")


def _build_requirements(code: str, product_type: str) -> list[str]:
    """
    Parse import statements from generated code to derive pip requirements.
    Returns a list of package names suitable for `pip install`.
    """
    # Map import names → pip package names
    import_to_pkg: dict[str, str] = {
        "fastapi": "fastapi[standard]",
        "uvicorn": "uvicorn[standard]",
        "flask": "flask",
        "django": "django",
        "pydantic": "pydantic",
        "sqlalchemy": "sqlalchemy",
        "httpx": "httpx",
        "aiohttp": "aiohttp",
        "requests": "requests",
        "starlette": "starlette",
        "databases": "databases",
        "alembic": "alembic",
        "jose": "python-jose",
        "passlib": "passlib[bcrypt]",
        "dotenv": "python-dotenv",
        "psycopg2": "psycopg2-binary",
        "asyncpg": "asyncpg",
        "redis": "redis",
        "celery": "celery",
        "boto3": "boto3",
        "jwt": "PyJWT",
        "yaml": "pyyaml",
        "toml": "tomli",
    }

    # FastAPI apps always need uvicorn
    base_pkgs: list[str] = []
    if "fastapi" in code.lower() or product_type in ("api", "fastapi"):
        base_pkgs = ["fastapi[standard]", "uvicorn[standard]"]
    elif "flask" in code.lower() or product_type == "flask":
        base_pkgs = ["flask"]

    detected: set[str] = set(base_pkgs)

    import_pattern = re.compile(r"^(?:import|from)\s+([\w]+)", re.MULTILINE)
    for match in import_pattern.finditer(code):
        pkg_name = match.group(1).lower()
        if pkg_name in import_to_pkg:
            detected.add(import_to_pkg[pkg_name])

    return sorted(detected)


def _build_server_command(
    entry_file: str,
    language: str,
    port: int,
    code: str,
    workspace: Path,
) -> list[str]:
    """
    Build the subprocess command to start the app server.
    Returns a list suitable for subprocess.Popen.
    """
    code_lower = code.lower()

    if language == "python":
        if "fastapi" in code_lower or "uvicorn" in code_lower:
            # uvicorn main:app --host 127.0.0.1 --port PORT --reload
            module = entry_file.replace(".py", "")
            # Detect the app variable name
            app_var = "app"
            app_match = re.search(r"(\w+)\s*=\s*FastAPI\(", code)
            if app_match:
                app_var = app_match.group(1)
            return [
                sys.executable, "-m", "uvicorn",
                f"{module}:{app_var}",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--reload",
            ]
        elif "flask" in code_lower:
            # FLASK_APP=main.py flask run --host 127.0.0.1 --port PORT
            return [
                sys.executable, "-m", "flask", "run",
                "--host", "127.0.0.1",
                "--port", str(port),
            ]
        else:
            # Plain Python: python main.py
            return [sys.executable, entry_file]

    elif language == "node":
        node_path = shutil.which("node") or "node"
        npm_path = shutil.which("npm") or "npm"

        # Next.js dev server
        if "next" in code_lower:
            return [npm_path, "run", "dev", "--", "-p", str(port)]
        # React (CRA)
        if "react" in code_lower:
            return [npm_path, "start"]
        return [node_path, entry_file]

    return [sys.executable, entry_file]


# ---------------------------------------------------------------------------
# HostManager
# ---------------------------------------------------------------------------
class HostManager:
    """
    Orchestrates dependency installation, app startup, health checks,
    and local URL exposure for generated applications.
    """

    def __init__(self) -> None:
        # Registry of active hosted processes: port → subprocess.Popen
        self._processes: dict[int, subprocess.Popen] = {}  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def host(
        self,
        code: str,
        product_type: str,
        run_id: str,
        preferred_port: int = _DEFAULT_PORT,
        progress_cb: Any = None,  # Optional[Callable[[str], Awaitable[None]]]
    ) -> HostManagerResult:
        """
        Full host lifecycle:
          1. Write code to temp workspace
          2. Install dependencies (pip/npm) with PackageResolver fallback
          3. Start server subprocess
          4. Health-check until responding or timeout
          5. Return HostedApp with URL
        """
        logs: list[str] = []

        def _log(msg: str) -> None:
            logs.append(msg)
            logger.info("[HostManager] %s", msg)

        # ----- Step 1: Workspace -----------------------------------------------
        workspace = Path(tempfile.mkdtemp(prefix=f"asep_app_{run_id[:8]}_"))
        _log(f"Workspace: {workspace}")

        entry_file, language = _detect_entry_file(workspace, code, product_type)
        code_path = workspace / entry_file

        try:
            code_path.write_text(code, encoding="utf-8")
            _log(f"Code written to {code_path}")
        except Exception as exc:
            return HostManagerResult(
                success=False,
                error=f"Failed to write code to workspace: {exc}",
                logs=logs,
            )

        # ----- Step 2: Install dependencies ------------------------------------
        install_output = ""
        install_step = "skipped"

        if language == "python":
            requirements = _build_requirements(code, product_type)
            if requirements:
                install_step = f"pip install {' '.join(requirements)}"
                _log(f"Installing: {install_step}")
                install_output, install_err = await self._pip_install(requirements, workspace)
                if install_err:
                    # Use PackageResolver to classify and retry with alternatives
                    _log(f"Install error detected, attempting resolution: {install_err[:200]}")
                    install_output, install_step, install_err = await self._resolve_install(
                        requirements, install_err, language, workspace, _log
                    )
                else:
                    _log(f"Dependencies installed successfully.")
            else:
                _log("No external dependencies detected.")

        elif language == "node":
            pkg_json = workspace / "package.json"
            if not pkg_json.exists():
                _log("No package.json found — skipping npm install.")
            else:
                install_step = "npm install"
                _log("Running npm install...")
                install_output, install_err = await self._npm_install(workspace)
                if install_err:
                    _log(f"npm install error: {install_err[:200]}")

        # ----- Step 3: Port selection ------------------------------------------
        try:
            port = find_free_port(preferred_port)
        except RuntimeError as exc:
            return HostManagerResult(
                success=False, error=str(exc), logs=logs, install_step=install_step,
            )
        if port != preferred_port:
            _log(f"Port {preferred_port} in use → using port {port}")

        # ----- Step 4: Start server --------------------------------------------
        cmd = _build_server_command(entry_file, language, port, code, workspace)
        _log(f"Starting server: {' '.join(cmd)}")

        env = os.environ.copy()
        env["PORT"] = str(port)
        if language == "python" and "flask" in code.lower():
            env["FLASK_APP"] = entry_file
            env["FLASK_ENV"] = "development"

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
            )
            self._processes[port] = proc
        except Exception as exc:
            return HostManagerResult(
                success=False,
                error=f"Failed to start server: {exc}",
                logs=logs,
                install_step=install_step,
            )

        _log(f"Server process started (PID={proc.pid}) on port {port}")

        # ----- Step 5: Health check --------------------------------------------
        url = f"http://localhost:{port}"
        startup_logs: list[str] = []
        health_ok = False

        _log(f"Waiting for server to become healthy at {url} ...")
        deadline = time.monotonic() + _HEALTH_CHECK_TIMEOUT

        while time.monotonic() < deadline:
            # Read any stdout from the process (non-blocking)
            if proc.stdout:
                try:
                    import select
                    # On Windows, select on a pipe is not supported, so we use
                    # proc.stdout.readline with a timeout approach
                    proc.stdout.flush()
                except Exception:
                    pass

            # Check if process died
            if proc.poll() is not None:
                raw = ""
                if proc.stdout:
                    try:
                        raw = proc.stdout.read() or ""
                    except Exception:
                        pass
                startup_logs.append(f"Process exited with code {proc.returncode}. Output: {raw[:400]}")
                _log(startup_logs[-1])
                break

            # Try HTTP health check
            if check_http_health(port):
                health_ok = True
                _log(f"Health check passed: {url} is responding.")
                break

            await asyncio.sleep(_HEALTH_POLL_INTERVAL)

        if not health_ok:
            # Collect final process output
            if proc.poll() is None:
                # Process still running but not responding — could be a plain Python script
                # that exited before we could catch it. Consider this a success if exit 0.
                await asyncio.sleep(1.0)
                if proc.poll() == 0:
                    health_ok = True
                    url = f"Exit code 0 — output at {workspace}"
                    _log("Script completed with exit code 0.")
                else:
                    _log(f"Server not responding after {_HEALTH_CHECK_TIMEOUT}s — may still be starting.")
                    # Don't kill the process — it may be slow to start.
                    # Return partial success.
                    health_ok = False

        hosted = HostedApp(
            port=port,
            url=url,
            pid=proc.pid,
            workspace_dir=str(workspace),
            product_type=product_type,
            startup_logs=startup_logs,
            health_ok=health_ok,
            install_output=install_output[:600],
            error="" if health_ok else f"Server did not respond within {_HEALTH_CHECK_TIMEOUT}s",
        )

        return HostManagerResult(
            success=health_ok or proc.poll() == 0,
            app=hosted,
            install_step=install_step,
            logs=logs,
        )

    def stop(self, port: int) -> None:
        """Terminate the process listening on the given port."""
        proc = self._processes.pop(port, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            logger.info("[HostManager] Stopped process on port %d", port)

    def stop_all(self) -> None:
        """Terminate all managed processes."""
        for port in list(self._processes.keys()):
            self.stop(port)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _pip_install(
        self, packages: list[str], workspace: Path
    ) -> tuple[str, str]:
        """
        Run `pip install <packages>` in the workspace.
        Returns (stdout_output, error_string).
        """
        cmd = [sys.executable, "-m", "pip", "install"] + packages + [
            "--quiet", "--no-input", "--disable-pip-version-check"
        ]
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(workspace),
                    timeout=_INSTALL_TIMEOUT,
                ),
                timeout=_INSTALL_TIMEOUT + 10,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "").strip()
                return result.stdout or "", err
            return result.stdout or "", ""
        except asyncio.TimeoutError:
            return "", "pip install timed out"
        except Exception as exc:
            return "", str(exc)

    async def _npm_install(self, workspace: Path) -> tuple[str, str]:
        """Run `npm install` in the workspace."""
        npm = shutil.which("npm") or "npm"
        cmd = [npm, "install", "--no-fund", "--no-audit"]
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(workspace),
                    timeout=_INSTALL_TIMEOUT,
                ),
                timeout=_INSTALL_TIMEOUT + 10,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "").strip()
                return result.stdout or "", err
            return result.stdout or "", ""
        except asyncio.TimeoutError:
            return "", "npm install timed out"
        except Exception as exc:
            return "", str(exc)

    async def _resolve_install(
        self,
        packages: list[str],
        error_str: str,
        language: str,
        workspace: Path,
        log_fn: Any,
    ) -> tuple[str, str, str]:
        """
        Use PackageResolver to classify the error and retry with compliant alternatives.
        Returns (install_output, install_step_desc, remaining_error).
        """
        try:
            from src.utils.package_resolver import PackageResolver
            resolver = PackageResolver()
            resolved_pkgs: list[str] = []
            swap_notes: list[str] = []

            for pkg in packages:
                result = resolver.resolve_failure(pkg, "pip", error_str)
                if result.compliant_alternative:
                    alt = result.compliant_alternative.replacement_package
                    resolved_pkgs.append(alt)
                    swap_notes.append(
                        f"{pkg} → {alt} ({result.compliant_alternative.rationale})"
                    )
                    log_fn(f"Package swap: {pkg} → {alt}")
                else:
                    resolved_pkgs.append(pkg)

            if swap_notes:
                log_fn(f"Applying compliant alternatives: {'; '.join(swap_notes)}")
                out, err = await self._pip_install(resolved_pkgs, workspace)
                step = f"pip install (resolved) {' '.join(resolved_pkgs)}"
                return out, step, err

        except Exception as exc:
            log_fn(f"PackageResolver failed: {exc} — retrying original install")

        # Fallback: retry original
        out, err = await self._pip_install(packages, workspace)
        return out, f"pip install {' '.join(packages)}", err


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
host_manager = HostManager()
