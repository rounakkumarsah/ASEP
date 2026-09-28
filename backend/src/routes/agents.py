"""
ASEP — Agent Execution & Background Job Router
==============================================
Provides decoupled asynchronous agent execution endpoints, real-time WebSocket
status streaming, and webhook notifications upon job completion.
"""

from __future__ import annotations

import collections
import datetime
import logging
import uuid
from typing import Any

import httpx
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

from src.auth.jwt import decode_token
from src.services.task_queue_service import (
    ConcurrencyLimitExceededError,
    get_task_queue,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agents"])


class JobConnectionManager:
    """Manages active WebSocket connections subscribed to background job updates."""

    def __init__(self) -> None:
        self.active_connections: dict[str, set[WebSocket]] = collections.defaultdict(set)

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[job_id].add(websocket)
        logger.debug("WebSocket client connected to job %s", job_id)

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.debug("WebSocket client disconnected from job %s", job_id)

    async def broadcast_job_update(self, job_id: str, payload: dict[str, Any]) -> None:
        """Broadcast payload to all subscribed WebSocket clients and send webhook if complete."""
        # 1. Broadcast to WebSockets
        sockets = list(self.active_connections.get(job_id, []))
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception as exc:
                logger.warning("Failed to send WebSocket update for job %s: %s", job_id, exc)
                self.disconnect(job_id, ws)

        # 2. Trigger webhook notification if job is complete or failed
        job_status = payload.get("status")
        if job_status in ("completed", "failed"):
            queue = get_task_queue()
            try:
                details = await queue.get_job_details(job_id)
                if details and details.get("spec", {}).get("webhook_url"):
                    webhook_url = details["spec"]["webhook_url"]
                    await self._deliver_webhook(webhook_url, payload)
            except Exception as exc:
                logger.debug("Webhook delivery check skipped: %s", exc)

    async def _deliver_webhook(self, url: str, payload: dict[str, Any]) -> None:
        """Deliver an asynchronous HTTP webhook notification."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=payload)
                logger.info("Delivered webhook for job to %s: HTTP %s", url, res.status_code)
        except Exception as exc:
            logger.warning("Webhook delivery failed for %s: %s", url, exc)


job_connection_manager = JobConnectionManager()


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class ExecuteAgentRequest(BaseModel):
    """Payload to enqueue autonomous agent execution."""

    prompt: str = Field(..., description="Prompt / goal specification for the agent")
    workspace_id: str = Field(default="default", description="Workspace partition ID")
    model: str | None = Field(default=None, description="Preferred AI model override")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Additional agent parameters")
    webhook_url: str | None = Field(default=None, description="Optional webhook URL called on completion")


class ExecuteAgentResponse(BaseModel):
    """Immediate non-blocking response returned to client in < 500ms."""

    job_id: str
    status_url: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Detailed background job status, partial/full results, and execution telemetry."""

    job_id: str
    status: str
    workspace_id: str
    retry_count: int
    result: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


# ---------------------------------------------------------------------------
# HTTP Endpoints
# ---------------------------------------------------------------------------

def _resolve_user_id(request: Request) -> uuid.UUID:
    """Extract authenticated user ID from Authorization header or generate fallback."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            payload = decode_token(token)
            if payload:
                user_id_str = payload.get("sub") or payload.get("user_id")
                if user_id_str:
                    return uuid.UUID(str(user_id_str))
        except Exception:
            pass

    # Check state user if set by previous middleware
    if hasattr(request.state, "user_id") and request.state.user_id:
        return uuid.UUID(str(request.state.user_id))

    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post(
    "/execute-agent",
    response_model=ExecuteAgentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Agent Execution",
    description="Enqueues autonomous agent execution in background queue and returns immediately in <500ms.",
)
async def execute_agent(
    req: ExecuteAgentRequest,
    request: Request,
) -> ExecuteAgentResponse:
    """Enqueue an agent execution job asynchronously."""
    user_id = _resolve_user_id(request)
    task_queue = get_task_queue()

    spec = {
        "prompt": req.prompt,
        "model": req.model,
        "parameters": req.parameters,
        "webhook_url": req.webhook_url,
    }

    try:
        job_id = await task_queue.enqueue_agent_execution(
            user_id=user_id,
            spec=spec,
            workspace_id=req.workspace_id,
        )
    except ConcurrencyLimitExceededError as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(err),
        )

    return ExecuteAgentResponse(
        job_id=job_id,
        status_url=f"/jobs/{job_id}",
        status="pending",
        message="Agent execution enqueued successfully",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status and Results",
    description="Fetch execution status, partial or full code results, and execution metrics.",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Retrieve current status and output of a background agent job."""
    task_queue = get_task_queue()
    details = await task_queue.get_job_details(job_id)

    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return JobStatusResponse(**details)


@router.websocket("/jobs/{job_id}/ws")
async def websocket_job_updates(websocket: WebSocket, job_id: str) -> None:
    """WebSocket stream for real-time progress and completion updates for a specific job."""
    await job_connection_manager.connect(job_id, websocket)
    task_queue = get_task_queue()

    try:
        # Send initial status
        details = await task_queue.get_job_details(job_id)
        if details:
            await websocket.send_json(details)
        else:
            await websocket.send_json({"job_id": job_id, "status": "unknown"})

        # Keep connection open to listen for client disconnection or ping
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        job_connection_manager.disconnect(job_id, websocket)
    except Exception as exc:
        logger.debug("WebSocket connection error on job %s: %s", job_id, exc)
        job_connection_manager.disconnect(job_id, websocket)
