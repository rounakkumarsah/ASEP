"""
Integration Tests for AgentRunRepository
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.exc import NoResultFound

from src.db.models.agent_run import AgentRun, RunStatus
from src.repositories.agent_run import AgentRunRepository


@pytest.fixture
def repo(db_session):
    return AgentRunRepository(db_session)


@pytest.mark.asyncio
async def test_create_and_get(repo, db_session):
    run_id = uuid.uuid4()
    run = AgentRun(
        id=run_id,
        goal="Test DB goal",
        plan=[],
        status=RunStatus.PENDING,
        session_id="test_sys"
    )
    
    # Create
    created_run = await repo.create(run)
    await db_session.flush()
    assert created_run.id == run_id
    
    # Get
    fetched_run = await repo.get_or_raise(run_id)
    assert fetched_run.id == run_id
    assert fetched_run.goal == "Test DB goal"


@pytest.mark.asyncio
async def test_get_or_raise_not_found(repo):
    with pytest.raises(NoResultFound):
        await repo.get_or_raise(uuid.uuid4())


@pytest.mark.asyncio
async def test_get_active_runs(repo, db_session):
    # Insert multiple states
    runs = [
        AgentRun(id=uuid.uuid4(), goal="Active", plan=[], status=RunStatus.RUNNING, session_id="sys"),
        AgentRun(id=uuid.uuid4(), goal="Pending", plan=[], status=RunStatus.PENDING, session_id="sys"),
        AgentRun(id=uuid.uuid4(), goal="Done", plan=[], status=RunStatus.COMPLETED, session_id="sys"),
    ]
    for r in runs:
        await repo.create(r)
    await db_session.flush()
    
    running_runs = await repo.get_running()
    pending_runs = await repo.get_pending_oldest_first()
    
    # Assert
    assert len(running_runs) >= 1
    assert len(pending_runs) >= 1
    for r in running_runs:
        assert r.status == RunStatus.RUNNING
    for r in pending_runs:
        assert r.status == RunStatus.PENDING
