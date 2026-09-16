"""
ASEP — Python Sandbox Tool Implementation
"""
import contextlib
import logging
import os
import shlex
from typing import Any

from pydantic import BaseModel, Field

from src.tools.base import BaseTool
from src.tools.metadata import ToolCategory
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger(__name__)

class PythonSandboxInput(BaseModel):
    code: str = Field(description="Python code to execute in the sandbox")

class PythonSandboxTool(BaseTool):
    name = "python_sandbox"
    description = "Execute arbitrary Python code in a secure, isolated Docker container (5s timeout, 50MB RAM, read-only root, no network)."
    category = ToolCategory.DEVELOPMENT.value
    input_model = PythonSandboxInput
    required_permissions = [ToolPermission.EXECUTE]
    destructive_operations = False

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)
            
            import docker
            try:
                client = docker.from_env()
                client.ping()
            except Exception as docker_exc:
                return ToolExecutionOutput(
                    success=False,
                    error=f"Docker daemon is not running or unreachable. Sandbox execution is required: {docker_exc}",
                )

            # We write the code to a temporary file in the workspace or host /tmp
            # to mount it into the container's /tmp. Wait, we can just pass the code via stdin
            # or `sh -c 'python -c ...'` but code might have quotes. 
            # Better approach: create a local temp file, mount it, run it.
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
            with os.fdopen(fd, "w") as f:
                f.write(inputs.code)
            
            try:
                # Docker sandbox execution
                # Security limits: 5s timeout, 50MB RAM, network=none, readonly, etc.
                container = client.containers.run(
                    image="python:3.12-slim",
                    command=["python", "/workspace/code.py"],
                    volumes={temp_path: {"bind": "/workspace/code.py", "mode": "ro"}},
                    working_dir="/workspace",
                    network_mode="none",
                    nano_cpus=500000000,  # 0.5 CPU
                    mem_limit="50m",  # Limit to 50MB RAM
                    detach=True,
                    user="1000:1000",                  # Run as non-root user
                    cap_drop=["ALL"],                  # Drop all Linux capabilities
                    security_opt=["no-new-privileges:true"], # Prevent privilege escalation
                    read_only=True,                    # Read-only root filesystem
                    tmpfs={"/tmp": "size=10m,noexec,nosuid,nodev"}, # Secure scratch space
                    pids_limit=50,                     # Fork bomb mitigation
                )
                
                try:
                    # Wait for container execution with a timeout of 5 seconds
                    result = container.wait(timeout=5)
                    stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
                    stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
                    returncode = result.get("StatusCode", 0)
                    
                    if returncode != 0:
                        err_msg = f"Execution failed with code {returncode}.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
                        return ToolExecutionOutput(success=False, error=err_msg)
                        
                    return ToolExecutionOutput(
                        success=True,
                        result={"stdout": stdout, "stderr": stderr, "returncode": returncode},
                    )
                except Exception as wait_exc:
                    with contextlib.suppress(Exception):
                        container.kill()
                    return ToolExecutionOutput(
                        success=False, error=f"Execution timed out after 5 seconds or failed: {wait_exc}"
                    )
                finally:
                    with contextlib.suppress(Exception):
                        container.remove(force=True)
            finally:
                # Cleanup the temp file on host
                with contextlib.suppress(Exception):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.exception("Failed to execute python_sandbox")
            return ToolExecutionOutput(success=False, error=str(e))
