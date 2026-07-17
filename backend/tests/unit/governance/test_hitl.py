from __future__ import annotations
import pytest
import time
from datetime import datetime, timezone
from src.governance.hitl import (
    HITLEngine,
    RiskLevel,
    ApprovalAction,
    ReviewerRole
)

def test_hitl_risk_evaluation():
    engine = HITLEngine()
    
    # Test Terminal Tool risk matching (should be Critical)
    risk_term = engine.evaluate_risk("terminal", {"command": "echo hello"})
    assert risk_term == RiskLevel.CRITICAL
    
    # Test Filesystem write risk matching (should be Medium)
    risk_fs_write = engine.evaluate_risk("filesystem", {"action": "write"})
    assert risk_fs_write == RiskLevel.MEDIUM

def test_hitl_session_lifecycle():
    engine = HITLEngine()
    
    # Create review session
    session = engine.create_session(
        request_id="req-1",
        execution_id="exec-1",
        correlation_id="corr-1",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "rm -rf /"},
        justification="Clean workspace"
    )
    
    assert session.session_id.startswith("resume_tok_")
    assert session.risk_level == RiskLevel.CRITICAL
    assert len(session.audit_trail) == 1
    
    # Approve session
    time.sleep(0.01)
    engine.submit_decision(
        session_id=session.session_id,
        action=ApprovalAction.APPROVE,
        reviewer="admin_user",
        role=ReviewerRole.ADMINISTRATOR,
        notes="Approved for debug"
    )
    
    assert session.decision == ApprovalAction.APPROVE
    assert session.reviewer == "admin_user"
    assert len(session.audit_trail) == 2
    assert session.latency_seconds is not None
    
    # Check SLA recalculations
    assert engine.sla_stats.average_review_time > 0.0
    assert engine.sla_stats.timeout_rate == 0.0

def test_hitl_session_expiration():
    engine = HITLEngine()
    
    # Create session with expired TTL
    session = engine.create_session(
        request_id="req-exp",
        execution_id="exec-exp",
        correlation_id="corr-exp",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "dir"},
        justification="listing dir",
        ttl_seconds=-10 # expired in the past
    )
    
    # Submit decision triggers Expiration resolution
    resolved = engine.submit_decision(
        session_id=session.session_id,
        action=ApprovalAction.APPROVE,
        reviewer="ops_user",
        role=ReviewerRole.OPERATOR
    )
    
    assert resolved.decision == ApprovalAction.EXPIRE
    assert engine.sla_stats.timeout_rate == 1.0

def test_hitl_endpoints():
    from fastapi.testclient import TestClient
    from src.api.app import create_app
    from src.governance.hitl import get_hitl_engine
    
    app = create_app()
    client = TestClient(app)
    
    # Initialize some session
    engine = get_hitl_engine()
    session = engine.create_session(
        request_id="req-api",
        execution_id="exec-api",
        correlation_id="corr-api",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "whoami"},
        justification="Debug request"
    )
    
    # Get active queue
    resp_queue = client.get("/api/v1/governance/hitl/queue")
    assert resp_queue.status_code == 200
    queue_data = resp_queue.json()
    assert any(q["session_id"] == session.session_id for q in queue_data)
    
    # Get SLA statistics
    resp_sla = client.get("/api/v1/governance/hitl/statistics")
    assert resp_sla.status_code == 200
    
    # Submit review decision
    payload = {
        "session_id": session.session_id,
        "action": "Approve",
        "reviewer": "test_lead",
        "role": "Team Lead",
        "notes": "Looks safe to execute"
    }
    resp_dec = client.post("/api/v1/governance/hitl/review", json=payload)
    assert resp_dec.status_code == 200
    dec_data = resp_dec.json()
    assert dec_data["status"] == "success"
    assert dec_data["decision"] == "Approve"

