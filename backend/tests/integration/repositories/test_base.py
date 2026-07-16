"""
Integration Tests for BaseRepository
"""

import uuid
import pytest

from src.db.models.agent_run import AgentRun, RunStatus
from src.repositories.agent_run import AgentRunRepository


@pytest.fixture
def repo(db_session):
    # Using AgentRunRepository to test BaseRepository methods
    return AgentRunRepository(db_session)


@pytest.mark.asyncio
async def test_base_create(repo, db_session):
    run = AgentRun(
        id=uuid.uuid4(),
        goal="Base create",
        plan={},
        status=RunStatus.PENDING,
        session_id="test-session"
    )
    result = await repo.create(run)
    await db_session.flush()
    assert result.id == run.id


@pytest.mark.asyncio
async def test_base_update(repo, db_session):
    run = AgentRun(
        id=uuid.uuid4(),
        goal="Base update",
        plan={},
        status=RunStatus.PENDING,
        session_id="test-session"
    )
    await repo.create(run)
    await db_session.flush()
    
    updated = await repo.update(run, goal="Updated goal")
    await db_session.flush()
    
    assert updated.goal == "Updated goal"


@pytest.mark.asyncio
async def test_base_delete(repo, db_session):
    run = AgentRun(
        id=uuid.uuid4(),
        goal="Base delete",
        plan={},
        status=RunStatus.PENDING,
        session_id="test-session"
    )
    await repo.create(run)
    await db_session.flush()
    
    await repo.delete(run)
    await db_session.flush()
    
    fetched = await repo.get(run.id)
    assert fetched is None
