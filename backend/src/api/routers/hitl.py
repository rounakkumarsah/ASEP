"""
ASEP — API Router for Human-in-the-Loop Approval Queue
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import get_audit_service
from src.auth.dependencies import CurrentUser
from src.db.models.audit_log import ActorType, AuditOutcome, AuditSeverity
from src.governance.hitl import (
    ApprovalAction,
    ApprovalSLA,
    ReviewerRole,
    ReviewSession,
    get_hitl_engine,
)
from src.services.audit_service import AuditService

logger = logging.getLogger("opensep.hitl.api")
router = APIRouter(prefix="/governance/hitl", tags=["Human-in-the-Loop"])


class DecisionRequest(BaseModel):
    session_id: str
    action: ApprovalAction
    reviewer: str
    role: ReviewerRole
    modified_args: dict[str, Any] | None = None
    notes: str | None = ""


@router.get("/queue", response_model=list[ReviewSession])
async def get_queue(current_user: CurrentUser) -> list[ReviewSession]:
    """Retrieve all queued and resolved HITL sessions."""
    engine = get_hitl_engine()
    return await engine.get_all_sessions()


@router.get("/statistics", response_model=ApprovalSLA)
async def get_statistics(current_user: CurrentUser) -> ApprovalSLA:
    """Retrieve average latency and escalation SLA rates."""
    engine = get_hitl_engine()
    return await engine.get_sla_stats()


@router.post("/review")
async def submit_review_decision(
    req: DecisionRequest,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    audit_service: AuditService = Depends(get_audit_service),
) -> dict[str, Any]:
    """Submit a human action review decision and resume the corresponding StateGraph run.

    Access is restricted to users with the ``admin`` or ``operator`` role.
    The matched LangGraph thread is resumed in the background via
    ``runtime.resume_run()``.  A full audit trail entry is written before
    returning.
    """
    # RBAC check: only admin and operator can resolve reviews
    if current_user.role not in ("admin", "operator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role lacks authorization to resolve review sessions.",
        )

    engine = get_hitl_engine()
    try:
        session = await engine.submit_decision(
            session_id=req.session_id,
            action=req.action,
            reviewer=req.reviewer,
            role=req.role,
            modified_args=req.modified_args,
            notes=req.notes or "",
        )

        # Trigger execution resumption via the LangGraph ↔ HITL Bridge
        from src.runtime import get_langgraph_runtime

        runtime = get_langgraph_runtime()

        async def _consume_stream(exec_id: str, decision_val: str) -> None:
            try:
                async for _event in runtime.resume_run(thread_id=exec_id, human_input=decision_val):
                    pass  # consume full stream updates
            except Exception as e:
                logger.error("Error resuming graph execution context: %s", e, exc_info=True)

        # Enqueue background task safely using FastAPI BackgroundTasks
        background_tasks.add_task(_consume_stream, session.execution_id, session.decision.value)

        # Log audit trail event
        await audit_service.log_event(
            actor_type=ActorType.USER,
            actor_id=str(current_user.id),
            action=f"governance.hitl.{req.action.value.lower()}",
            resource_type="hitl_session",
            resource_id=session.session_id,
            outcome=AuditOutcome.SUCCESS,
            severity=(
                AuditSeverity.INFO
                if req.action == ApprovalAction.APPROVE
                else AuditSeverity.WARNING
            ),
            log_details={
                "session_id": session.session_id,
                "decision": session.decision.value,
                "reviewer_role": session.reviewer_role.value if session.reviewer_role else None,
                "notes": req.notes,
            },
        )

        return {
            "status": "success",
            "session_id": session.session_id,
            "decision": session.decision,
            "audit_trail": session.audit_trail,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
