import asyncio
import json
import logging
from typing import AsyncGenerator, Any

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
    Gracefully falls back to RestrictedExecutor (RestrictedPython sandbox) when
    Docker daemon is unreachable or in serverless environments.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        import contextlib
        import json
        import os
        from src.services.restricted_code_sandbox import RestrictedExecutor

        is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("SERVERLESS") == "1"
        docker_client = None

        if not is_serverless:
            try:
                import docker
                client = docker.from_env()
                client.ping()
                docker_client = client
            except Exception as e:
                logger.info(
                    "Docker daemon unreachable (%s), falling back to in-process RestrictedExecutor sandbox.",
                    e,
                )
                docker_client = None

        if docker_client is None:
            # Fallback to RestrictedExecutor
            yield f"data: {json.dumps({'type': 'system', 'text': 'Running in isolated RestrictedPython sandbox...'})}\n\n"
            try:
                res = await RestrictedExecutor.execute(request.code, timeout=30.0)
                stdout = res.stdout if hasattr(res, "stdout") else str(res.get("stdout") or "")
                error = res.stderr if hasattr(res, "stderr") else str(res.get("error") or "")
                is_success = res.success if hasattr(res, "success") else bool(res.get("success", False))

                if stdout:
                    for line in stdout.splitlines(keepends=True):
                        yield f"data: {json.dumps({'type': 'output', 'text': line})}\n\n"
                        await asyncio.sleep(0.01)

                if error:
                    yield f"data: {json.dumps({'type': 'error', 'text': error})}\n\n"

                exit_code = 0 if is_success else 1
                if exit_code == 0:
                    yield f"data: {json.dumps({'type': 'success', 'text': f'\\n[Process exited with code {exit_code}]'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'text': f'\\n[Process exited with code {exit_code}]'})}\n\n"
            except Exception as e:
                logger.exception("Restricted sandbox execution error")
                yield f"data: {json.dumps({'type': 'error', 'text': f'\\nSandbox Error: {str(e)}'})}\n\n"
                yield f"data: {json.dumps({'type': 'error', 'text': '\\n[Process exited with code 1]'})}\n\n"

            yield "data: [DONE]\n\n"
            return

        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=".py", text=True)
        with os.fdopen(fd, "w") as f:
            f.write(request.code)
            
        container = None
        try:
            yield f"data: {json.dumps({'type': 'system', 'text': 'Starting secure Python sandbox container...'})}\n\n"
            
            container = docker_client.containers.run(
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
            logger.exception("Docker sandbox error, falling back to RestrictedExecutor")
            if container is None:
                yield f"data: {json.dumps({'type': 'system', 'text': 'Docker container unavailable. Falling back to isolated RestrictedPython sandbox...'})}\n\n"
                try:
                    res = await RestrictedExecutor.execute(request.code, timeout=30.0)
                    stdout = res.stdout if hasattr(res, "stdout") else str(res.get("stdout") or "")
                    error = res.stderr if hasattr(res, "stderr") else str(res.get("error") or "")
                    is_success = res.success if hasattr(res, "success") else bool(res.get("success", False))

                    if stdout:
                        for line in stdout.splitlines(keepends=True):
                            yield f"data: {json.dumps({'type': 'output', 'text': line})}\n\n"
                            await asyncio.sleep(0.01)

                    if error:
                        yield f"data: {json.dumps({'type': 'error', 'text': error})}\n\n"

                    exit_code = 0 if is_success else 1
                    if exit_code == 0:
                        yield f"data: {json.dumps({'type': 'success', 'text': f'\\n[Process exited with code {exit_code}]'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'text': f'\\n[Process exited with code {exit_code}]'})}\n\n"
                except Exception as inner_e:
                    logger.exception("Restricted sandbox fallback error")
                    yield f"data: {json.dumps({'type': 'error', 'text': f'\\nSandbox Error: {str(inner_e)}'})}\n\n"
                    yield f"data: {json.dumps({'type': 'error', 'text': '\\n[Process exited with code 1]'})}\n\n"
            else:
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

class TerminalRequest(BaseModel):
    command: str
    cwd: str | None = None

@router.post("/terminal/execute")
async def terminal_execute(request: TerminalRequest) -> dict[str, Any]:
    """Execute a command. On serverless: uses RestrictedPython for Python,
    subprocess for simple system commands with strict timeout."""
    import os
    import shlex
    
    cmd = request.command.strip()
    is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("SERVERLESS") == "1"
    
    # Python code execution
    if cmd.startswith("python ") or cmd.startswith("python3 ") or cmd in ("python", "python3"):
        # Extract the code or filename
        parts = cmd.split(" ", 1)
        code_arg = parts[1].strip() if len(parts) > 1 else ""
        
        if code_arg.startswith("-c "):
            code = code_arg[3:].strip().strip('"').strip("'")
        elif code_arg and os.path.isfile(code_arg):
            try:
                with open(code_arg, "r", encoding="utf-8", errors="replace") as f:
                    code = f.read()
            except Exception:
                code = f"print('Would execute: {code_arg}')"
        elif code_arg and request.cwd and os.path.isfile(os.path.join(request.cwd, code_arg)):
            try:
                with open(os.path.join(request.cwd, code_arg), "r", encoding="utf-8", errors="replace") as f:
                    code = f.read()
            except Exception:
                code = f"print('Would execute: {code_arg}')"
        elif code_arg:
            if any(term in code_arg for term in ("print(", "def ", "import ", "=", "+", "-", "*", "/", "{", "}")):
                code = code_arg
            else:
                code = f"print('Executing {code_arg}...')\n"
        else:
            code = "print('Python interactive mode not supported in terminal. Usage: python <code> or python -c <code>')"
        
        try:
            from src.services.restricted_code_sandbox import RestrictedExecutor
            result = await RestrictedExecutor.execute(code, timeout=10)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": 1}
    
    # Simple system-like commands (safe subset)
    safe_commands = {
        "whoami": lambda: os.environ.get("USER", os.environ.get("USERNAME", "asep-agent")),
        "pwd": lambda: os.getcwd(),
        "date": lambda: __import__("datetime").datetime.now().isoformat(),
        "env": lambda: "\n".join(f"{k}={v}" for k, v in sorted(os.environ.items()) if k.startswith("ASEP_") or k in ("VERCEL", "NODE_ENV", "PYTHON_VERSION")),
        "uname": lambda: f"{os.name} {__import__('platform').platform()}",
    }
    
    cmd_name = cmd.split()[0].lower()
    if cmd_name in safe_commands:
        try:
            output = safe_commands[cmd_name]()
            return {"stdout": str(output), "stderr": "", "exit_code": 0}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": 1}
    
    # For other commands on serverless: cannot run arbitrary subprocesses
    if is_serverless:
        return {
            "stdout": "",
            "stderr": f"Command '{cmd_name}' is not available in the serverless environment.\nAvailable commands: python, whoami, pwd, date, env, uname\nFor Python code: python -c 'print(\"hello\")'",
            "exit_code": 127,
        }
    
    # Local development: run via subprocess with strict timeout
    import subprocess
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10,
            cwd=request.cwd,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out after 10 seconds.", "exit_code": 124}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1}

class ExecuteRequest(BaseModel):
    code: str
    timeout: int = 10

@router.post("/execute")
async def execute_code(request: ExecuteRequest) -> dict[str, Any]:
    """Execute Python code via RestrictedPython. No Docker required.
    Used by the Critic node on serverless environments."""
    try:
        from src.services.restricted_code_sandbox import RestrictedExecutor
        result = await RestrictedExecutor.execute(request.code, timeout=min(request.timeout, 30))
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "success": result.exit_code == 0,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Sandbox execution error: {str(e)}",
            "exit_code": 1,
            "success": False,
        }
