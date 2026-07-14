"""
Integration Tests for AuditLogRepository
"""

import uuid
import pytest

from src.db.models.audit_log import AuditLog, ActorType, AuditOutcome, AuditSeverity
from src.repositories.audit_log import AuditLogRepository


@pytest.fixture
def repo(db_session):
    return AuditLogRepository(db_session)


@pytest.mark.asyncio
async def test_get_by_actor(repo, db_session):
    actor_id = "test_actor_sys"
    
    logs = [
        AuditLog(id=uuid.uuid4(), actor_type=ActorType.SYSTEM, actor_id=actor_id, action="a1", resource_type="r", outcome=AuditOutcome.SUCCESS, severity=AuditSeverity.INFO),
        AuditLog(id=uuid.uuid4(), actor_type=ActorType.SYSTEM, actor_id=actor_id, action="a2", resource_type="r", outcome=AuditOutcome.SUCCESS, severity=AuditSeverity.INFO),
    ]
    
    for log in logs:
        await repo.create(log)
    await db_session.flush()
    
    fetched = await repo.get_by_actor(ActorType.SYSTEM, actor_id, limit=50)
    assert len(fetched) >= 2


@pytest.mark.asyncio
async def test_get_by_resource(repo, db_session):
    res_id = str(uuid.uuid4())
    log = AuditLog(
        id=uuid.uuid4(), 
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        action="r.updated",
        resource_type="agent_run",
        resource_id=res_id,
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.WARNING
    )
    await repo.create(log)
    await db_session.flush()
    
    # Query by resource
    res_logs = await repo.get_by_resource("agent_run", res_id, limit=50)
    assert log.id in [l.id for l in res_logs]
