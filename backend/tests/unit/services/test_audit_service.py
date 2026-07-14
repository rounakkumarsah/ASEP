"""
Tests for AuditService
"""

import uuid
import pytest
from unittest.mock import AsyncMock

from src.db.models.audit_log import AuditEventCategory, AuditEventSeverity
from src.services.audit_service import AuditService


@pytest.fixture
def audit_service(uow_factory):
    return AuditService(uow_factory)


@pytest.mark.asyncio
async def test_log_event(audit_service, mock_uow):
    mock_uow.audit_logs.create.side_effect = lambda log: log
    
    result = await audit_service.log_event(
        category=AuditEventCategory.SYSTEM,
        event_name="test_event",
        severity=AuditEventSeverity.INFO,
        actor="test_system",
        description="A test event occurred"
    )
    
    assert result.event_name == "test_event"
    assert result.category == AuditEventCategory.SYSTEM
    assert result.severity == AuditEventSeverity.INFO
    assert result.actor == "test_system"
    
    mock_uow.audit_logs.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_event_validation(audit_service):
    with pytest.raises(ValueError, match="event_name must be non-empty"):
        await audit_service.log_event(
            category=AuditEventCategory.SYSTEM,
            event_name="   ",
            severity=AuditEventSeverity.INFO,
            actor="test"
        )
        
    with pytest.raises(ValueError, match="actor must be non-empty"):
        await audit_service.log_event(
            category=AuditEventCategory.SYSTEM,
            event_name="test",
            severity=AuditEventSeverity.INFO,
            actor=""
        )


@pytest.mark.asyncio
async def test_get_events_by_run(audit_service, mock_uow):
    run_id = uuid.uuid4()
    mock_uow.audit_logs.get_by_run.return_value = []
    
    result = await audit_service.get_events_by_run(run_id)
    
    assert result == []
    mock_uow.audit_logs.get_by_run.assert_awaited_once_with(run_id, limit=50, offset=0)
    # Read-only operation shouldn't commit
    mock_uow.commit.assert_not_called()
