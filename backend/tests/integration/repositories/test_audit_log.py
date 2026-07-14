"""
Integration Tests for AuditLogRepository
"""

import uuid
import pytest

from src.db.models.audit_log import AuditLog, AuditEventCategory, AuditEventSeverity
from src.repositories.audit_log import AuditLogRepository


@pytest.fixture
def repo(db_session):
    return AuditLogRepository(db_session)


@pytest.mark.asyncio
async def test_get_by_run(repo, db_session):
    run_id = uuid.uuid4()
    
    logs = [
        AuditLog(id=uuid.uuid4(), agent_run_id=run_id, event_name="e1", category=AuditEventCategory.SYSTEM, severity=AuditEventSeverity.INFO, actor="sys"),
        AuditLog(id=uuid.uuid4(), agent_run_id=run_id, event_name="e2", category=AuditEventCategory.SYSTEM, severity=AuditEventSeverity.INFO, actor="sys"),
    ]
    
    for log in logs:
        await repo.create(log)
    await db_session.flush()
    
    fetched = await repo.get_by_run(run_id)
    assert len(fetched) == 2


@pytest.mark.asyncio
async def test_get_by_category_and_severity(repo, db_session):
    log = AuditLog(
        id=uuid.uuid4(), 
        event_name="e1", 
        category=AuditEventCategory.DATA_ACCESS, 
        severity=AuditEventSeverity.WARNING, 
        actor="sys"
    )
    await repo.create(log)
    await db_session.flush()
    
    # Query by category
    cat_logs = await repo.get_by_category(AuditEventCategory.DATA_ACCESS, limit=50)
    assert log.id in [l.id for l in cat_logs]
    
    # Query by severity
    sev_logs = await repo.get_by_severity(AuditEventSeverity.WARNING, limit=50)
    assert log.id in [l.id for l in sev_logs]
