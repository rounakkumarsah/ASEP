"""
Tests for AuditService
"""

import uuid
import pytest
from unittest.mock import AsyncMock

from src.db.models.audit_log import ActorType, AuditOutcome, AuditSeverity
from src.services.audit_service import AuditService


@pytest.fixture
def audit_service(uow_factory):
    return AuditService(uow_factory)


@pytest.mark.asyncio
async def test_log_event(audit_service, mock_uow):
    mock_uow.audit_logs.create.side_effect = lambda log: log
    
    result = await audit_service.log_event(
        actor_type=ActorType.SYSTEM,
        actor_id="test_system",
        action="test.event",
        resource_type="agent_run",
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.INFO
    )
    
    assert result.action == "test.event"
    assert result.actor_type == ActorType.SYSTEM
    assert result.severity == AuditSeverity.INFO
    assert result.actor_id == "test_system"
    assert result.outcome == AuditOutcome.SUCCESS
    
    mock_uow.audit_logs.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_event_validation(audit_service):
    with pytest.raises(ValueError, match="action must be"):
        await audit_service.log_event(
            actor_type=ActorType.SYSTEM,
            actor_id="test_system",
            action="   ",
            resource_type="agent_run",
            outcome=AuditOutcome.SUCCESS,
        )
        
    with pytest.raises(ValueError, match="actor_id must be"):
        await audit_service.log_event(
            actor_type=ActorType.SYSTEM,
            actor_id="",
            action="test.event",
            resource_type="agent_run",
            outcome=AuditOutcome.SUCCESS,
        )
