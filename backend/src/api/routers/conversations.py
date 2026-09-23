"""
ASEP — Conversations Router
============================
Thin stateless proxy gateway exposing LangGraph execution threads as REST
endpoints.

Design principles:
  - Stateless: no conversation data is stored here; all persistence is owned
    by the ``AsyncPostgresSaver`` checkpointer bound to the StateGraph.
  - Auth-first: every endpoint requires a valid ``CurrentUser`` session.
  - Polling: long-running runs are started immediately and polled via
    ``GET /conversations/run/{run_id}/status`` — SSE streaming is NOT used
    because Vercel serverless buffers the entire response body, causing the
    30-second function timeout to kill the connection before agents finish.
  - HITL-aware: a paused thread (``next == ("validate",)``) surfaces its
    interrupt payload in the response so the caller knows to POST a resume.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.auth.dependencies import CurrentUser
from src.runtime import get_langgraph_runtime

logger = logging.getLogger("opensep.conversations")

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Strong references to background run tasks (prevents GC before completion)
_background_run_tasks: set = set()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    """Payload for starting a new conversation run."""

    goal: str = Field(
        ...,
        description="Natural-language goal that the agent should accomplish.",
        min_length=1,
        max_length=4096,
    )
    thread_id: str | None = Field(
        default=None,
        description=(
            "Optional LangGraph thread identifier.  If omitted a new UUID is "
            "generated so each call creates an isolated execution thread."
        ),
    )
    research_mode: str = Field(
        default="balanced",
        description="The research mode/persona to use for this execution."
    )
    environment_mode: str = Field(
        default="local",
        description="Target environment: local or deploy."
    )


class ResumeRequest(BaseModel):
    """Payload for resuming a paused (interrupted) run."""

    decision: str = Field(
        ...,
        description=(
            "Human decision value to feed back into the interrupted node. "
            "Typically 'approve' or 'reject'."
        ),
    )


class ThreadStateResponse(BaseModel):
    """Serialised snapshot of the current checkpoint state for a thread."""

    thread_id: str
    status: str | None
    next: list[str]
    run_id: str | None
    human_input: str | None
    messages: list[dict[str, Any]]
    variables: dict[str, Any]
    is_paused: bool


# ---------------------------------------------------------------------------
# SSE helpers (kept for /resume and /explore/stream endpoints)
# ---------------------------------------------------------------------------


def _sse_line(data: dict[str, Any]) -> str:
    """Format a single Server-Sent Event frame."""
    return f"data: {json.dumps(data)}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/graph",
    summary="Get React Flow visual graph structure of the LangGraph multi-agent pipeline",
    response_model=dict[str, Any],
)
async def get_visual_graph() -> dict[str, Any]:
    """Return static/runtime nodes and edges schema formatted for React Flow (@xyflow/react)."""
    from src.runtime.visualizer import parse_graph_to_react_flow
    return parse_graph_to_react_flow()


@router.post(
    "/run",
    summary="Start a new agent run — returns immediately; poll /run/{run_id}/status for updates",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_run(
    payload: RunRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Start a new LangGraph execution thread.

    Returns **immediately** with ``run_id`` and ``status: queued`` so the
    caller never blocks on the full agent execution.

    The agent runs in a background ``asyncio.Task``.  The frontend should
    poll ``GET /conversations/run/{run_id}/status`` every 1.5 seconds
    to receive batched events and the final status.

    This pattern is necessary on Vercel serverless where SSE streaming is
    fully buffered by the CDN layer, causing ``fetch()`` to throw a network
    error before the stream completes.
    """
    import asyncio
    import uuid

    thread_id = payload.thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    logger.info(
        "Initiating run run_id=%s thread_id=%s user=%s",
        run_id,
        thread_id,
        current_user.id,
    )

    org_id = current_user.org_id or current_user.id

    # Persist initial AgentRun record
    try:
        from src.api.dependencies import get_uow_factory
        from src.db.models.agent_run import AgentRun, RunStatus as DbRunStatus
        async with get_uow_factory()() as uow:
            run_record = AgentRun(
                id=uuid.UUID(run_id),
                org_id=org_id,
                goal=payload.goal,
                status=DbRunStatus.RUNNING,
            )
            await uow.agent_runs.create(run_record)
            await uow.commit()
    except Exception as e:
        logger.warning("Could not persist initial AgentRun %s: %s", run_id, e)

    runtime = get_langgraph_runtime()
    step_result = await runtime.execute_step(
        run_id=run_id,
        thread_id=thread_id,
        goal=payload.goal,
        research_mode=payload.research_mode,
        environment_mode=payload.environment_mode,
        org_id=org_id,
        is_first=True
    )
    
    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "status": step_result["status"],
        "events": step_result["events"]
    }


@router.post(
    "/run/{run_id}/step",
    summary="Execute next step of a LangGraph run",
)
async def run_step(
    run_id: str,
    payload: RunRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Execute the next node in the LangGraph workflow."""
    org_id = current_user.org_id or current_user.id
    thread_id = payload.thread_id
    
    runtime = get_langgraph_runtime()
    step_result = await runtime.execute_step(
        run_id=run_id,
        thread_id=thread_id,
        org_id=org_id,
        is_first=False
    )
    
    if step_result["status"] == "done":
        try:
            from src.api.dependencies import get_uow_factory
            from src.db.models.agent_run import RunStatus as DbRunStatus
            async with get_uow_factory()() as uow:
                await uow.agent_runs.update_status(uuid.UUID(run_id), DbRunStatus.COMPLETED)
                await uow.commit()
        except Exception:
            pass
            
    return step_result



