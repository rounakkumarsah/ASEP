import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.tools.python_sandbox import PythonSandboxTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sandbox", tags=["Sandbox"])

class SandboxRunRequest(BaseModel):
    code: str

@router.post("/python/stream")
async def stream_python_execution(request: SandboxRunRequest) -> StreamingResponse:
    """
    Execute Python code in a secure Docker sandbox and stream the stdout/stderr.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        import docker
        import tempfile
        import os
        import contextlib
        
        try:
            client = docker.from_env()
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': f'Docker daemon unreachable: {e}'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
        with os.fdopen(fd, "w") as f:
            f.write(request.code)
            
        container = None
        try:
            yield f"data: {json.dumps({'type': 'system', 'text': 'Starting secure Python sandbox container...'})}\n\n"
            
            container = client.containers.run(
                image="python:3.12-slim",
                command=["python", "-u", "/workspace/code.py"],  # -u for unbuffered output
                volumes={temp_path: {"bind": "/workspace/code.py", "mode": "ro"}},
                working_dir="/workspace",
                network_mode="none",
                nano_cpus=500000000,
                mem_limit="50m",
                detach=True,
                user="1000:1000",
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "size=10m,noexec,nosuid,nodev"},
                pids_limit=50,
            )
            
            # Stream logs
            for log_line in container.logs(stream=True, follow=True):
                # Docker logs returns bytes. We decode and send as output.
                decoded = log_line.decode("utf-8")
                yield f"data: {json.dumps({'type': 'output', 'text': decoded})}\n\n"
                await asyncio.sleep(0.01)  # tiny yield
                
            result = container.wait(timeout=5)
            returncode = result.get("StatusCode", 0)
            
            if returncode == 0:
                yield f"data: {json.dumps({'type': 'success', 'text': f'\\n[Process exited with code {returncode}]'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'text': f'\\n[Process exited with code {returncode}]'})}\n\n"
                
        except Exception as e:
            logger.exception("Sandbox streaming error")
            yield f"data: {json.dumps({'type': 'error', 'text': f'\\nSandbox Error: {str(e)}'})}\n\n"
        finally:
            if container:
                with contextlib.suppress(Exception):
                    container.kill()
                    container.remove(force=True)
            with contextlib.suppress(Exception):
                os.unlink(temp_path)
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
