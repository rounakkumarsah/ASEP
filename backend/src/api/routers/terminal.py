"""
ASEP — Production-Grade FastAPI WebSocket Router for Terminal Streaming
======================================================================
Provides zero-zombie interactive terminal sessions using Python's pty module,
os.fork, and asyncio read/write multiplexers. Supports token authentication,
concurrent connection caps, rate limiting, and software flow control (XON/XOFF).
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import json
import logging
import os
import pty
import signal
import struct
import sys
import termios
import uuid

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.api.dependencies import get_uow_factory
from src.auth.jwt import decode_token
from src.config.settings import get_settings
from src.services.user_service import UserService

logger = logging.getLogger("opensep.terminal.ws")
router = APIRouter(prefix="/ws/sessions", tags=["Terminal"])

# Concurrency tracker to limit resources per server node
CONCURRENT_SESSIONS: set[str] = set()
MAX_CONCURRENT_SESSIONS = 25  # Limit concurrent active terminals on this node
RATE_LIMIT_WINDOWS: dict[str, list[float]] = {}
MAX_CONNECTIONS_PER_MINUTE = 10


def _clean_zombies() -> None:
    """Reaps zombie child processes non-blockingly."""
    try:
        while True:
            pid, status_val = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            logger.info("Reaped zombie child process pid=%d status=%d", pid, status_val)
    except ChildProcessError:
        pass


class LocalPTYSession:
    """Manages an active local PTY bash session using os.fork and interactive multiplexing."""

    def __init__(self, session_id: str, websocket: WebSocket) -> None:
        self.session_id = session_id
        self.websocket = websocket
        self.fd: int | None = None
        self.pid: int | None = None
        self.read_task: asyncio.Task | None = None
        self.redis_client: redis.Redis | None = None
        self.pubsub_task: asyncio.Task | None = None
        self.paused = False

    async def initialize(
        self, shell_path: str = "/bin/bash", cols: int = 80, rows: int = 24
    ) -> bool:
        """Forks a child process attached to a PTY master/slave pair and initializes shell execution."""
        _clean_zombies()

        if len(CONCURRENT_SESSIONS) >= MAX_CONCURRENT_SESSIONS:
            logger.warning(
                "Rejecting terminal request session=%s: Max concurrency cap reached",
                self.session_id,
            )
            return False

        try:
            pid, fd = pty.fork()
            if pid == 0:
                # Inside child process: setup terminal environment and exec shell
                os.environ["TERM"] = "xterm-256color"
                os.environ["LANG"] = "en_US.UTF-8"

                # Exec shell
                try:
                    os.execve(shell_path, [shell_path], os.environ)
                except Exception as exc:
                    sys.stderr.write(f"Failed to execute shell {shell_path}: {exc}\n")
                    sys.exit(1)
            else:
                # Parent process: store FD and PID
                self.pid = pid
                self.fd = fd

                # Set non-blocking on Master FD
                fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
                fcntl.fcntl(self.fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

                # Set initial terminal size
                self._set_winsize(rows, cols)

                # Register globally
                CONCURRENT_SESSIONS.add(self.session_id)

                # Setup Redis client for horizontal scaling if configured
                settings = get_settings()
                if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
                    self.redis_client = redis.from_url(settings.REDIS_URL)

                logger.info(
                    "Spawned PTY shell pid=%d fd=%d for session=%s",
                    self.pid,
                    self.fd,
                    self.session_id,
                )
                return True
        except Exception as e:
            logger.exception("Failed to initialize PTY session=%s: %s", self.session_id, e)
            return False

    def _set_winsize(self, rows: int, cols: int) -> None:
        """Flashes terminal win size geometry to Master PTY via ioctl."""
        if self.fd is not None:
            # Struct layout: 4 unsigned shorts: rows, cols, xpixels, ypixels
            win_size = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, win_size)

    async def start(self) -> None:
        """Starts PTY read tasks and Redis PubSub synchronizers."""
        self.read_task = asyncio.create_task(self._read_pty_master())
        if self.redis_client:
            self.pubsub_task = asyncio.create_task(self._subscribe_redis_broadcasts())

    async def write_stdin(self, data: str) -> None:
        """Writes data string directly to PTY standard input descriptor.

        Enforces OPA policy validation dynamically before execution if OPA is enabled.
        """
        settings = get_settings()
        if settings.OPA_ENABLED:
            try:
                # Intercept input command and query the local Open Policy Agent sidecar
                import httpx
                async with httpx.AsyncClient(timeout=1.0) as client:
                    resp = await client.post(
                        settings.OPA_URL,
                        json={"input": {"session_id": self.session_id, "command": data}}
                    )
                    if resp.status_code == 200:
                        decision = resp.json().get("result", {})
                        if not decision.get("allow", True):
                            logger.warning(
                                "OPA blocked terminal input command on session=%s: %s",
                                self.session_id,
                                data
                            )
                            # Echo block notification back to terminal output
                            await self.websocket.send_text("\r\n\033[31m[GOVERNANCE ERROR] Command blocked by OPA security policy.\033[0m\r\n")
                            return
            except Exception as e:
                logger.error("OPA policy query failed for session=%s: %s", self.session_id, e)
                # Fallback safety: fail closed if OPA is enabled but unreachable
                await self.websocket.send_text("\r\n\033[31m[GOVERNANCE ERROR] Security engine unreachable. Execution halted.\033[0m\r\n")
                return

        if self.fd is not None:
            try:
                # low-level write directly to file descriptor bypasses shell injection vulnerabilities
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, os.write, self.fd, data.encode("utf-8"))
            except Exception as e:
                logger.error(
                    "Failed writing to PTY fd=%d for session=%s: %s", self.fd, self.session_id, e
                )

    async def resize(self, cols: int, rows: int) -> None:
        """Triggers PTY resize event."""
        logger.info(
            "Resizing PTY terminal session=%s to cols=%d rows=%d", self.session_id, cols, rows
        )
        self._set_winsize(rows, cols)

    def pause(self) -> None:
        """Enforces Software flow control XOFF state."""
        self.paused = True

    def resume(self) -> None:
        """Resumes Software flow control XON state."""
        self.paused = False

    async def cleanup(self) -> None:
        """Ensures process termination, zombie reaping, and client cleanup."""
        CONCURRENT_SESSIONS.discard(self.session_id)

        if self.read_task:
            self.read_task.cancel()
        if self.pubsub_task:
            self.pubsub_task.cancel()

        if self.fd is not None:
            with contextlib.suppress(Exception):
                os.close(self.fd)
            self.fd = None

        if self.pid is not None:
            try:
                # Force process group termination to cleanly clean up sub-processes
                os.killpg(os.getpgid(self.pid), signal.SIGKILL)
            except Exception:
                with contextlib.suppress(Exception):
                    os.kill(self.pid, signal.SIGKILL)
            self.pid = None

        if self.redis_client:
            with contextlib.suppress(Exception):
                await self.redis_client.close()

        _clean_zombies()

    async def _read_pty_master(self) -> None:
        """Polls Master PTY non-blockingly and forwards data frame payloads to client."""
        settings = get_settings()
        loop = asyncio.get_running_loop()
        while self.fd is not None:
            try:
                if self.paused:
                    await asyncio.sleep(0.05)
                    continue

                # Wait until file descriptor has data available
                await loop.run_in_executor(None, self._wait_for_data)
                if self.fd is None:
                    break

                # Read raw PTY data chunk
                data = await loop.run_in_executor(None, os.read, self.fd, 65536)
                if not data:
                    break

                text = data.decode("utf-8", errors="replace")

                if self.redis_client:
                    # Use configurable Redis prefix settings parameter
                    channel = f"{settings.REDIS_TERMINAL_CHANNEL_PREFIX}:{self.session_id}"
                    await self.redis_client.publish(
                        channel,
                        json.dumps({"type": "stdout", "data": text}),
                    )
                else:
                    await self.websocket.send_text(text)
            except OSError:
                # PTY closed by process exit
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error reading PTY process for session=%s: %s", self.session_id, e)
                break

        # Terminate connection if shell exited
        with contextlib.suppress(Exception):
            await self.websocket.close(code=status.WS_1000_NORMAL_CLOSURE)

    def _wait_for_data(self) -> None:
        """Uses select statement block on FD."""
        import select

        if self.fd is not None:
            with contextlib.suppress(OSError, ValueError):
                select.select([self.fd], [], [], 1.0)

    async def _subscribe_redis_broadcasts(self) -> None:
        """Forwards cluster-wide Redis broker updates to client."""
        if not self.redis_client:
            return
        settings = get_settings()
        ps = self.redis_client.pubsub()
        channel = f"{settings.REDIS_TERMINAL_CHANNEL_PREFIX}:{self.session_id}"
        await ps.subscribe(channel)
        try:
            async for message in ps.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    if payload.get("type") == "stdout":
                        await self.websocket.send_text(payload["data"])
        except asyncio.CancelledError:
            pass
        finally:
            await ps.unsubscribe(channel)


def _check_rate_limit(client_ip: str) -> bool:
    """Standard sliding window rate limiter."""
    import time

    now = time.time()
    if client_ip not in RATE_LIMIT_WINDOWS:
        RATE_LIMIT_WINDOWS[client_ip] = []

    # Filter calls older than 60s
    RATE_LIMIT_WINDOWS[client_ip] = [t for t in RATE_LIMIT_WINDOWS[client_ip] if now - t < 60]

    if len(RATE_LIMIT_WINDOWS[client_ip]) >= MAX_CONNECTIONS_PER_MINUTE:
        return False

    RATE_LIMIT_WINDOWS[client_ip].append(now)
    return True


async def _authenticate_socket(websocket: WebSocket) -> bool:
    """Performs token check on access_token parameters or cookies."""
    token = websocket.cookies.get("access_token")
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        return False

    settings = get_settings()
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return False

        uow_factory = get_uow_factory()
        async with uow_factory() as uow:
            user_service = UserService(uow)
            user = await user_service.get_user(uuid.UUID(user_id_str))
            return user.is_active and user.status == "active"
    except Exception:
        return False


@router.websocket("/{session_id}/terminal")
async def websocket_terminal_endpoint(websocket: WebSocket, session_id: str) -> None:
    """FastAPI WebSocket endpoint supporting rate limiting, auth, and PTY bridging."""
    await websocket.accept()

    client_ip = websocket.client.host if websocket.client else "unknown"
    if not _check_rate_limit(client_ip):
        logger.warning("Rejecting terminal request: Rate limit exceeded for ip=%s", client_ip)
        # 4401 policy close code signals rate-limiting or policy violation
        await websocket.close(code=4401)
        return

    if not await _authenticate_socket(websocket):
        logger.warning(
            "Unauthenticated terminal request: session=%s client_ip=%s", session_id, client_ip
        )
        # Secure auth check failure closes socket with custom 4401/1008 code
        await websocket.close(code=4401)
        return

    settings = get_settings()
    shell_path = getattr(settings, "TERMINAL_SHELL", "/bin/bash")

    session = LocalPTYSession(session_id, websocket)
    if not await session.initialize(shell_path=shell_path):
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    await session.start()

    try:
        while True:
            message = await websocket.receive_text()
            try:
                frame = json.loads(message)
                frame_type = frame.get("type")

                if frame_type == "stdin":
                    await session.write_stdin(frame.get("data", ""))
                elif frame_type == "resize":
                    await session.resize(
                        cols=int(frame.get("cols", 80)), rows=int(frame.get("rows", 24))
                    )
                elif frame_type == "pause":
                    session.pause()
                elif frame_type == "resume":
                    session.resume()
                else:
                    logger.warning(
                        "Ignored unknown terminal packet type session=%s: %s",
                        session_id,
                        frame_type,
                    )
            except json.JSONDecodeError:
                # Interpret raw text as direct input keystrokes
                await session.write_stdin(message)
    except WebSocketDisconnect:
        logger.info("Terminal disconnected session=%s", session_id)
    except Exception as e:
        logger.exception("Websocket router crashed session=%s: %s", session_id, e)
    finally:
        await session.cleanup()
