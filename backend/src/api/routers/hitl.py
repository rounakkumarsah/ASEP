"""
ASEP — API Router for Human-in-the-Loop Approval Queue
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.governance.hitl import (
    get_hitl_engine,
    ReviewSession,
    ApprovalSLA,
    ApprovalAction,
    ReviewerRole
)

router = APIRouter(prefix="/governance/hitl", tags=["Human-in-the-Loop"])


class DecisionRequest(BaseModel):
    session_id: str
    action: ApprovalAction
    reviewer: str
    role: ReviewerRole
    modified_args: Optional[Dict[str, Any]] = None
    notes: Optional[str] = ""


@router.get("/queue", response_model=List[ReviewSession])
async def get_queue() -> List[ReviewSession]:
    """Retrieve all queued and resolved HITL sessions."""
    engine = get_hitl_engine()
    return list(engine.queue.values())


@router.get("/statistics", response_model=ApprovalSLA)
async def get_statistics() -> ApprovalSLA:
    """Retrieve average latency and escalation SLA rates."""
    engine = get_hitl_engine()
    return engine.sla_stats


@router.post("/review")
async def submit_review_decision(req: DecisionRequest) -> Dict[str, Any]:
    """Submit a human action review decision."""
    engine = get_hitl_engine()
    try:
        session = engine.submit_decision(
            session_id=req.session_id,
            action=req.action,
            reviewer=req.reviewer,
            role=req.role,
            modified_args=req.modified_args,
            notes=req.notes or ""
        )
        return {
            "status": "success",
            "session_id": session.session_id,
            "decision": session.decision,
            "audit_trail": session.audit_trail
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
