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



class StepRequest(BaseModel):
    thread_id: str = Field(..., description="The LangGraph thread ID associated with the run")
    goal: str | None = Field(default=None, description="Optional goal description fallback")

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
        parsed_org_uuid = None
        if org_id:
            try:
                parsed_org_uuid = uuid.UUID(str(org_id))
            except (ValueError, TypeError):
                pass
        async with get_uow_factory()() as uow:
            run_record = AgentRun(
                id=uuid.UUID(run_id),
                org_id=parsed_org_uuid,
                goal=payload.goal,
                status=DbRunStatus.RUNNING,
            )
            await uow.agent_runs.create(run_record)
            await uow.commit()
    except Exception as e:
        logger.warning("Could not persist initial AgentRun %s: %s", run_id, e)

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "status": "running",
        "events": [],
    }


@router.post(
    "/run/{run_id}/step",
    summary="Execute next step of a LangGraph run",
)
async def run_step(
    run_id: str,
    payload: StepRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Execute the next node in the LangGraph workflow."""
    import inspect
    from langchain_core.runnables.config import RunnableConfig

    org_id = current_user.org_id or current_user.id
    thread_id = payload.thread_id

    runtime = get_langgraph_runtime()
    config = RunnableConfig(configurable={"thread_id": thread_id})

    is_initial = False
    try:
        state = None
        if hasattr(runtime, "graph") and hasattr(runtime.graph, "aget_state"):
            state_call = runtime.graph.aget_state(config)
            if inspect.isawaitable(state_call):
                state = await state_call
        if state is None or not getattr(state, "values", None):
            is_initial = True
    except Exception as e:
        logger.warning("Could not inspect graph state for thread %s: %s", thread_id, e)
        is_initial = True

    goal = payload.goal or ""
    if not goal:
        try:
            from src.api.dependencies import get_uow_factory
            async with get_uow_factory()() as uow:
                run_record = await uow.agent_runs.get(uuid.UUID(run_id))
                if run_record and run_record.goal:
                    goal = run_record.goal
        except Exception as e:
            logger.warning("Could not load AgentRun %s: %s", run_id, e)

    step_result = await runtime.execute_step(
        run_id=run_id,
        thread_id=thread_id,
        goal=goal,
        research_mode="balanced",
        environment_mode="local",
        org_id=org_id,
        is_first=is_initial,
    )

    if step_result.get("status") == "done":
        try:
            from src.api.dependencies import get_uow_factory
            from src.db.models.agent_run import RunStatus as DbRunStatus
            async with get_uow_factory()() as uow:
                await uow.agent_runs.update_status(uuid.UUID(run_id), DbRunStatus.COMPLETED)
                await uow.commit()
        except Exception:
            pass

    return step_result


@router.get(
    "/{thread_id}/explore",
    summary="Get exploration events and summary for a conversation thread",
)
async def get_exploration_data(
    thread_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Retrieve all structured exploration events and latest summary for a thread."""
    from src.runtime.explore_manager import get_explore_manager

    explore_mgr = get_explore_manager()
    events = explore_mgr.get_events(thread_id)
    summary = explore_mgr.get_summary(thread_id)

    return {
        "thread_id": thread_id,
        "events": events,
        "summary": summary,
        "count": len(events),
    }


@router.get(
    "/{thread_id}/explore/stream",
    summary="Stream live exploration events via SSE",
    response_class=StreamingResponse,
)
async def stream_exploration_events(
    thread_id: str,
    current_user: CurrentUser,
) -> StreamingResponse:
    """Stream real-time exploration events via SSE."""
    from collections.abc import AsyncGenerator
    import asyncio
    from src.runtime.explore_manager import get_explore_manager

    explore_mgr = get_explore_manager()

    async def _sse_generator() -> AsyncGenerator[str, None]:
        sent_ids = set()
        # Stream existing events first
        for ev in explore_mgr.get_events(thread_id):
            ev_id = ev.get("id")
            if ev_id not in sent_ids:
                sent_ids.add(ev_id)
                yield _sse_line({"event": ev})

        # Poll for new events
        for _ in range(60):
            await asyncio.sleep(0.5)
            new_events = [ev for ev in explore_mgr.get_events(thread_id) if ev.get("id") not in sent_ids]
            for ev in new_events:
                sent_ids.add(ev["id"])
                yield _sse_line({"event": ev})
            summary = explore_mgr.get_summary(thread_id)
            if summary:
                yield _sse_line({"summary": summary})
                break
        yield _sse_done()

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Thread-Id": thread_id,
        },
    )




