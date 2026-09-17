"""
ASEP — Host Manager HTTP Router
================================
Provides endpoints to manage, monitor, and forcefully stop running hosted applications:
  - POST /api/v1/host/stop: Stops hosted process(es) by port, session_id, or PID
  - GET  /api/v1/host/status: Lists all currently running hosted applications
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from src.utils.host_manager import host_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/host", tags=["Host Manager"])


class StopAppRequest(BaseModel):
    """Payload to stop a hosted application."""
    port: int | None = Field(default=None, description="Port of the running application to stop")
    session_id: str | None = Field(default=None, description="Session ID whose running apps should be stopped")
    pid: int | None = Field(default=None, description="Process ID of the application to stop")


class StopAppResponse(BaseModel):
    """Result of stopping hosted application(s)."""
    success: bool
    stopped_ports: list[int]
    message: str


@router.post(
    "/stop",
    response_model=StopAppResponse,
    status_code=status.HTTP_200_OK,
    summary="Stop a running hosted application",
)
async def stop_hosted_app(request: StopAppRequest = StopAppRequest()) -> StopAppResponse:
    """
    Explicitly stop a running hosted application.
    Supports stopping by port, session_id, PID, or stopping all if unspecified.
    """
    stopped_ports: list[int] = []

    if request.port is not None:
        if host_manager.stop(request.port):
            stopped_ports.append(request.port)
            msg = f"Stopped application running on port {request.port}"
        else:
            msg = f"No active process found on port {request.port}"

    elif request.session_id:
        stopped_ports = host_manager.stop_session(request.session_id)
        msg = f"Stopped {len(stopped_ports)} application(s) for session '{request.session_id}'"

    elif request.pid is not None:
        if host_manager.stop_pid(request.pid):
            stopped_ports.append(request.pid)
            msg = f"Stopped process PID {request.pid}"
        else:
            msg = f"Could not stop process PID {request.pid}"

    else:
        stopped_ports = host_manager.stop_all()
        msg = f"Stopped all {len(stopped_ports)} active hosted application(s)"

    logger.info("[Host Router] %s (stopped_ports=%s)", msg, stopped_ports)
    return StopAppResponse(
        success=True,
        stopped_ports=stopped_ports,
        message=msg,
    )


@router.get(
    "/status",
    summary="List active hosted applications",
)
async def get_hosted_apps_status(session_id: str | None = None) -> dict[str, Any]:
    """Return all currently active hosted applications, optionally filtered by session_id."""
    apps = host_manager.get_running_apps(session_id)
    return {
        "apps": apps,
        "count": len(apps),
    }
