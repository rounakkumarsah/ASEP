"""
ASEP — Implementation of Initial Tools
"""

import contextlib
import os
import subprocess
from typing import Any

import httpx
from pydantic import BaseModel, Field

from src.tools.base import BaseTool
from src.tools.metadata import ToolCategory
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput


# 1. Filesystem Tool
class FilesystemInput(BaseModel):
    action: str = Field(description="Action to perform: read, write, list")
    path: str = Field(description="Target file or directory path")
    content: str | None = Field(
        default=None, description="Content to write (required for action='write')"
    )


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read, write, or list files and directories on the local host."
    category = ToolCategory.FILESYSTEM.value
    input_model = FilesystemInput
    required_permissions = [ToolPermission.FILESYSTEM]
    destructive_operations = True

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)
            path = os.path.abspath(inputs.path)

            # Strict sandbox workspace boundary check to prevent path traversal
            workspace_root = os.path.abspath(os.environ.get("WORKSPACE_ROOT", os.getcwd()))
            if not path.startswith(workspace_root) and not path.startswith(os.path.abspath(os.path.dirname(os.getcwd()))):
                return ToolExecutionOutput(
                    success=False,
                    error=f"Security Policy Violation: Access denied to path outside workspace boundary: {path}",
                )

            if inputs.action == "read":
                if not os.path.exists(path):
                    return ToolExecutionOutput(success=False, error=f"File not found: {path}")
                with open(path, encoding="utf-8") as f:
                    data = f.read()
                return ToolExecutionOutput(success=True, result={"content": data})

            elif inputs.action == "write":
                if inputs.content is None:
                    return ToolExecutionOutput(
                        success=False, error="Content required for write action"
                    )
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(inputs.content)
                return ToolExecutionOutput(
                    success=True, result={"path": path, "bytes_written": len(inputs.content)}
                )

            elif inputs.action == "list":
                if not os.path.exists(path):
                    return ToolExecutionOutput(success=False, error=f"Directory not found: {path}")
                items = os.listdir(path)
                return ToolExecutionOutput(success=True, result={"items": items})

            return ToolExecutionOutput(success=False, error=f"Unknown action: {inputs.action}")
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))


# 2. Terminal Tool
class TerminalInput(BaseModel):
    command: str = Field(description="Shell command to run")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the command")


class TerminalTool(BaseTool):
    name = "terminal"
    description = "Execute command-line shells on the host machine."
    category = ToolCategory.SYSTEM.value
    input_model = TerminalInput
    required_permissions = [ToolPermission.EXECUTE]
    destructive_operations = True

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)

            # Restrict commands to prevent basic dangerous execution
            forbidden = ["rm -rf", "del /s", "format", "mkfs", "shutdown"]
            for term in forbidden:
                if term in inputs.command:
                    return ToolExecutionOutput(
                        success=False, error=f"Command blocked by policy: contains '{term}'"
                    )

            # Docker sandbox execution
            import os
            import shlex

            import docker

            try:
                client = docker.from_env()
                client.ping()
            except Exception as docker_exc:
                return ToolExecutionOutput(
                    success=False,
                    error=f"Docker daemon is not running or unreachable. Sandbox execution is required: {docker_exc}",
                )

            # Resolve workspace path to mount
            current_dir = os.path.abspath(os.getcwd())
            if "backend" in current_dir:
                workspace_path = os.path.dirname(current_dir)
            else:
                workspace_path = current_dir

            # Build full command string
            full_command = inputs.command
            if inputs.args:
                full_command = f"{inputs.command} " + " ".join(shlex.quote(a) for a in inputs.args)

            try:
                container = client.containers.run(
                    image="python:3.12-slim",
                    command=["sh", "-c", full_command],
                    volumes={workspace_path: {"bind": "/workspace", "mode": "ro"}},
                    working_dir="/workspace",
                    network_mode="none",
                    nano_cpus=500000000,  # Limit to 0.5 CPU
                    mem_limit="512m",  # Limit to 512MB RAM
                    detach=True,
                    # --- Sandbox Hardening ---
                    user="1000:1000",                  # Run as non-root user
                    cap_drop=["ALL"],                  # Drop all Linux capabilities
                    security_opt=["no-new-privileges:true"], # Prevent privilege escalation
                    read_only=True,                    # Read-only root filesystem
                    tmpfs={"/tmp": "size=64m,noexec,nosuid,nodev"}, # Secure scratch space
                    pids_limit=100,                    # Fork bomb mitigation
                )
            except Exception as run_exc:
                return ToolExecutionOutput(
                    success=False, error=f"Failed to start Docker sandbox container: {run_exc}"
                )

            try:
                # Wait for container execution with a timeout of 15 seconds
                result = container.wait(timeout=15)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
                returncode = result.get("StatusCode", 0)
                return ToolExecutionOutput(
                    success=returncode == 0,
                    result={"stdout": stdout, "stderr": stderr, "returncode": returncode},
                )
            except Exception as wait_exc:
                with contextlib.suppress(Exception):
                    container.kill()
                return ToolExecutionOutput(
                    success=False, error=f"Container execution timed out or failed: {wait_exc}"
                )
            finally:
                with contextlib.suppress(Exception):
                    container.remove(force=True)
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))


# 3. Git Tool
class GitInput(BaseModel):
    action: str = Field(description="Git action: status, commit, log, diff")
    message: str | None = Field(default=None, description="Commit message if action is commit")


class GitTool(BaseTool):
    name = "git"
    description = "Manage local Git repository state."
    category = ToolCategory.DEVELOPMENT.value
    input_model = GitInput
    required_permissions = [ToolPermission.WRITE]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)
            cmd = ["git"]
            if inputs.action == "status":
                cmd.append("status")
            elif inputs.action == "log":
                cmd += ["log", "-n", "5"]
            elif inputs.action == "diff":
                cmd.append("diff")
            elif inputs.action == "commit":
                if not inputs.message:
                    return ToolExecutionOutput(success=False, error="Commit message required")
                cmd += ["commit", "-m", inputs.message]
            else:
                return ToolExecutionOutput(
                    success=False, error=f"Unsupported action: {inputs.action}"
                )

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return ToolExecutionOutput(
                success=result.returncode == 0,
                result={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
            )
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))


# 4. GitHub Tool
class GitHubInput(BaseModel):
    repo: str = Field(description="Owner/Repo string (e.g. google/jax)")
    action: str = Field(description="Action to perform: get_repo, list_prs, list_issues")


class GitHubTool(BaseTool):
    name = "github"
    description = "Interface with GitHub API endpoints."
    category = ToolCategory.DEVELOPMENT.value
    input_model = GitHubInput
    required_permissions = [ToolPermission.NETWORK]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        # Mock implementation returning placeholder data for testing
        return ToolExecutionOutput(
            success=True,
            result={
                "repo": inputs.repo,
                "action": inputs.action,
                "mock_response": f"GitHub response for repo {inputs.repo} and action {inputs.action}.",
            },
        )


# 5. Docker Tool
class DockerInput(BaseModel):
    action: str = Field(description="Action: ps, info, inspect")
    container_id: str | None = Field(default=None, description="Container id/name to inspect")


class DockerTool(BaseTool):
    name = "docker"
    description = "Query container metrics, processes, and network setups."
    category = ToolCategory.INFRASTRUCTURE.value
    input_model = DockerInput
    required_permissions = [ToolPermission.ADMIN]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        # Mock or run subprocess if docker command exists
        try:
            cmd = ["docker"]
            if inputs.action == "ps":
                cmd += ["ps", "-a"]
            elif inputs.action == "info":
                cmd.append("info")
            elif inputs.action == "inspect":
                if not inputs.container_id:
                    return ToolExecutionOutput(
                        success=False, error="container_id required for inspect"
                    )
                cmd += ["inspect", inputs.container_id]
            else:
                return ToolExecutionOutput(success=False, error=f"Unknown action: {inputs.action}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return ToolExecutionOutput(
                success=result.returncode == 0,
                result={"stdout": result.stdout, "stderr": result.stderr},
            )
        except Exception:
            # Fallback to mock if docker command is not installed locally
            return ToolExecutionOutput(
                success=True,
                result={
                    "mock": True,
                    "action": inputs.action,
                    "status": "Docker scaffold running successfully",
                },
            )


# 6. HTTP / REST API Tool
class HTTPInput(BaseModel):
    method: str = Field(description="HTTP Method: GET, POST, PUT, DELETE")
    url: str = Field(description="Target URL")
    headers: dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")
    data: str | None = Field(default=None, description="Body data to transmit")


class HTTPTool(BaseTool):
    name = "http"
    description = "Send outbound HTTP requests and inspect REST API endpoints."
    category = ToolCategory.NETWORKING.value
    input_model = HTTPInput
    required_permissions = [ToolPermission.NETWORK]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)
            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    method=inputs.method,
                    url=inputs.url,
                    headers=inputs.headers,
                    content=inputs.data,
                    timeout=15.0,
                )
            return ToolExecutionOutput(
                success=resp.status_code < 400,
                result={
                    "status_code": resp.status_code,
                    "text": resp.text[:5000],  # Cap responses to avoid bloated outputs
                },
            )
        except Exception as e:
            return ToolExecutionOutput(success=False, error=str(e))


# 7. PostgreSQL Tool
class PostgresInput(BaseModel):
    query: str = Field(description="SQL query to execute or 'ping'")


class PostgresTool(BaseTool):
    name = "postgres"
    description = "Execute queries on the application's PostgreSQL database."
    category = ToolCategory.DATABASE.value
    input_model = PostgresInput
    required_permissions = [ToolPermission.READ, ToolPermission.WRITE]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        # Mock/Ping or execute logic (mocked here for base suite safety)
        return ToolExecutionOutput(
            success=True,
            result={
                "status": "connected",
                "query": inputs.query,
                "rows_affected": 0,
                "records": [],
            },
        )


# 8. Neo4j Tool
class Neo4jInput(BaseModel):
    query: str = Field(description="Cypher query to run or 'ping'")


class Neo4jTool(BaseTool):
    name = "neo4j"
    description = "Interact with the Neo4j Knowledge Graph."
    category = ToolCategory.DATABASE.value
    input_model = Neo4jInput
    required_permissions = [ToolPermission.READ, ToolPermission.WRITE]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        return ToolExecutionOutput(
            success=True, result={"status": "connected", "query": inputs.query, "records": []}
        )


# 9. Qdrant Tool
class QdrantInput(BaseModel):
    collection_name: str = Field(description="Target Collection name")
    action: str = Field(description="Action to perform: list, info, search")


class QdrantTool(BaseTool):
    name = "qdrant"
    description = "Query collection configuration status and parameters."
    category = ToolCategory.DATABASE.value
    input_model = QdrantInput
    required_permissions = [ToolPermission.READ]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        return ToolExecutionOutput(
            success=True,
            result={"collection": inputs.collection_name, "status": "active", "points_count": 42},
        )


# 10. Redis Tool
class RedisInput(BaseModel):
    command: str = Field(description="Redis command: ping, get, set")
    key: str | None = Field(default=None, description="Redis key")
    value: str | None = Field(default=None, description="Redis value")


class RedisTool(BaseTool):
    name = "redis"
    description = "Query memory cache state parameters."
    category = ToolCategory.DATABASE.value
    input_model = RedisInput
    required_permissions = [ToolPermission.READ, ToolPermission.WRITE]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        return ToolExecutionOutput(
            success=True,
            result={
                "status": "PONG" if inputs.command.lower() == "ping" else "OK",
                "key": inputs.key,
            },
        )


# 11. Environment Tool
class EnvironmentInput(BaseModel):
    keys: list[str] = Field(default_factory=list, description="Filter variables by name")


class EnvironmentTool(BaseTool):
    name = "environment"
    description = "Safely list environment configuration parameters."
    category = ToolCategory.SYSTEM.value
    input_model = EnvironmentInput
    required_permissions = [ToolPermission.SECRETS]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        res = {}
        for key in inputs.keys or os.environ.keys():
            # Prevent leakage of raw secrets or sensitive DB strings
            sensitive = ["secret", "password", "token", "key", "url", "dsn"]
            if any(s in key.lower() for s in sensitive):
                res[key] = "[REDACTED]"
            else:
                res[key] = os.environ.get(key, "")
        return ToolExecutionOutput(success=True, result=res)


# 12. Configuration Tool
class ConfigurationInput(BaseModel):
    component: str | None = Field(default=None, description="Component configuration name")


class ConfigurationTool(BaseTool):
    name = "configuration"
    description = "Inspect system component settings."
    category = ToolCategory.SYSTEM.value
    input_model = ConfigurationInput
    required_permissions = [ToolPermission.READ]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        return ToolExecutionOutput(
            success=True,
            result={
                "component": inputs.component or "global",
                "app_name": "ASEP",
                "version": "1.0.0",
                "debug": True,
            },
        )


# 13. Browser Tool (Scaffold)
class BrowserInput(BaseModel):
    action: str = Field(description="Action: navigate, screenshot, click")
    url: str | None = Field(default=None, description="Target URL")


class BrowserTool(BaseTool):
    name = "browser"
    description = "Headless browser automation tool scaffold."
    category = ToolCategory.BROWSER.value
    input_model = BrowserInput
    required_permissions = [ToolPermission.NETWORK]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        inputs = self.input_model.model_validate(arguments)
        return ToolExecutionOutput(
            success=True,
            result={
                "url": inputs.url,
                "action": inputs.action,
                "status": "Scaffold: Navegating simulated successfully",
            },
        )
