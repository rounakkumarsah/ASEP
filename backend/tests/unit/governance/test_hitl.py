from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.db.models.hitl_session import HITLSession, HITLStatus
from src.db.models.user import User
from src.governance.hitl import (
    ApprovalAction,
    HITLEngine,
    ReviewerRole,
    RiskLevel,
)


def test_hitl_risk_evaluation():
    engine = HITLEngine()

    # Test Terminal Tool risk matching (should be Critical)
    risk_term = engine.evaluate_risk("terminal", {"command": "echo hello"})
    assert risk_term == RiskLevel.CRITICAL

    # Test Filesystem write risk matching (should be Medium)
    risk_fs_write = engine.evaluate_risk("filesystem", {"action": "write"})
    assert risk_fs_write == RiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_hitl_session_lifecycle(uow_factory, mock_uow):
    engine = HITLEngine()
    engine.uow_factory = uow_factory

    # Mock uow hitl_sessions create
    mock_uow.hitl_sessions.create = AsyncMock(side_effect=lambda x: x)

    # Create review session
    session = await engine.create_session(
        request_id="req-1",
        execution_id=str(uuid.uuid4()),
        correlation_id="corr-1",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "rm -rf /"},
        justification="Clean workspace",
    )

    assert session.session_id.startswith("resume_tok_")
    assert session.risk_level == RiskLevel.CRITICAL
    assert len(session.audit_trail) == 1

    # Mock hitl_sessions get for submit_decision
    db_session_mock = HITLSession(
        session_id=session.session_id,
        execution_id=uuid.UUID(session.execution_id),
        correlation_id=session.correlation_id,
        requesting_agent=session.requesting_agent,
        requesting_tool=session.requesting_tool,
        risk_level=session.risk_level.value,
        status=HITLStatus.PENDING,
        arguments_json=session.modified_arguments,
        justification=session.justification,
        ttl_seconds=300,
    )
    db_session_mock.created_at = datetime.now(UTC)

    mock_uow.hitl_sessions.get = AsyncMock(return_value=db_session_mock)

    # Approve session
    time.sleep(0.01)
    resolved = await engine.submit_decision(
        session_id=session.session_id,
        action=ApprovalAction.APPROVE,
        reviewer="admin_user",
        role=ReviewerRole.ADMINISTRATOR,
        notes="Approved for debug",
    )

    assert resolved.decision == ApprovalAction.APPROVE
    assert resolved.reviewer == "admin_user"
    assert len(resolved.audit_trail) == 2
    assert resolved.latency_seconds is not None


@pytest.mark.asyncio
async def test_hitl_session_expiration(uow_factory, mock_uow):
    engine = HITLEngine()
    engine.uow_factory = uow_factory

    # Mock uow hitl_sessions create
    mock_uow.hitl_sessions.create = AsyncMock(side_effect=lambda x: x)

    # Create session with expired TTL
    session = await engine.create_session(
        request_id="req-exp",
        execution_id=str(uuid.uuid4()),
        correlation_id="corr-exp",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "dir"},
        justification="listing dir",
        ttl_seconds=-10,  # expired in the past
    )

    # Mock hitl_sessions get for submit_decision
    db_session_mock = HITLSession(
        session_id=session.session_id,
        execution_id=uuid.UUID(session.execution_id),
        correlation_id=session.correlation_id,
        requesting_agent=session.requesting_agent,
        requesting_tool=session.requesting_tool,
        risk_level=session.risk_level.value,
        status=HITLStatus.PENDING,
        arguments_json=session.modified_arguments,
        justification=session.justification,
        ttl_seconds=-10,
    )
    db_session_mock.created_at = datetime.now(UTC) - timedelta(
        seconds=20
    )

    mock_uow.hitl_sessions.get = AsyncMock(return_value=db_session_mock)

    # Submit decision triggers Expiration resolution
    resolved = await engine.submit_decision(
        session_id=session.session_id,
        action=ApprovalAction.APPROVE,
        reviewer="ops_user",
        role=ReviewerRole.OPERATOR,
    )

    assert resolved.decision == ApprovalAction.EXPIRE


@pytest.mark.asyncio
async def test_hitl_endpoints(uow_factory, mock_uow):
    from unittest.mock import MagicMock, patch

    from fastapi.testclient import TestClient

    from src.api.app import create_app
    from src.api.dependencies import get_audit_service
    from src.auth.dependencies import get_current_user
    from src.governance.hitl import get_hitl_engine
    from src.services.audit_service import AuditService

    # --- Mock User dependency ---
    async def mock_user():
        return User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@test.com",
            role="admin",
            status="active",
            is_active=True,
        )

    # --- Mock AuditService dependency to avoid DB calls ---
    mock_audit = MagicMock(spec=AuditService)
    mock_audit.log_event = AsyncMock(return_value=None)

    def mock_get_audit_service():
        return mock_audit

    app = create_app()
    app.dependency_overrides[get_current_user] = mock_user
    app.dependency_overrides[get_audit_service] = mock_get_audit_service
    client = TestClient(app)

    # Assign mock uow_factory on the global engine instance
    engine = get_hitl_engine()
    engine.uow_factory = uow_factory
    mock_uow.hitl_sessions.create = AsyncMock(side_effect=lambda x: x)

    # Initialize some session
    session = await engine.create_session(
        request_id="req-api",
        execution_id=str(uuid.uuid4()),
        correlation_id="corr-api",
        requesting_agent="supervisor",
        requesting_tool="terminal",
        requested_permissions=["execute"],
        arguments={"command": "whoami"},
        justification="Debug request",
    )

    # Mock hitl_sessions list and get
    db_sess_obj = HITLSession(
        session_id=session.session_id,
        execution_id=uuid.UUID(session.execution_id),
        correlation_id=session.correlation_id,
        requesting_agent=session.requesting_agent,
        requesting_tool=session.requesting_tool,
        risk_level=session.risk_level.value,
        status=HITLStatus.PENDING,
        arguments_json=session.modified_arguments,
        justification=session.justification,
        ttl_seconds=300,
    )
    db_sess_obj.created_at = datetime.now(UTC)
    mock_uow.hitl_sessions.list = AsyncMock(return_value=[db_sess_obj])
    mock_uow.hitl_sessions.get = AsyncMock(return_value=db_sess_obj)

    # Get active queue
    resp_queue = client.get("/api/v1/governance/hitl/queue")
    assert resp_queue.status_code == 200
    queue_data = resp_queue.json()
    assert any(q["session_id"] == session.session_id for q in queue_data)

    # Get SLA statistics
    resp_sla = client.get("/api/v1/governance/hitl/statistics")
    assert resp_sla.status_code == 200

    # Submit review decision — patch get_langgraph_runtime so no real runtime is invoked
    with patch("src.runtime.get_langgraph_runtime") as mock_runtime_factory:
        mock_runtime = MagicMock()
        mock_runtime.resume_run = AsyncMock(return_value=iter([]))
        mock_runtime_factory.return_value = mock_runtime

        payload = {
            "session_id": session.session_id,
            "action": "Approve",
            "reviewer": "test_lead",
            "role": "Team Lead",
            "notes": "Looks safe to execute",
        }
        resp_dec = client.post("/api/v1/governance/hitl/review", json=payload)
        assert resp_dec.status_code == 200
        dec_data = resp_dec.json()
        assert dec_data["status"] == "success"
        assert dec_data["decision"] == "Approve"

    # Clean up overrides to not affect other tests
    app.dependency_overrides.clear()
