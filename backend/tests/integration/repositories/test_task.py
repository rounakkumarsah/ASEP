"""
Integration Tests for TaskRepository
"""

import uuid
import pytest
from sqlalchemy.exc import NoResultFound

from src.db.models.task import Task, TaskStatus, TaskPriority
from src.repositories.task import TaskRepository


@pytest.fixture
def repo(db_session):
    return TaskRepository(db_session)


from src.db.models.agent_run import AgentRun, RunStatus

@pytest.mark.asyncio
async def test_get_by_run(repo, db_session):
    run_id = uuid.uuid4()
    run = AgentRun(
        id=run_id,
        goal="Test Goal",
        plan=[],
        status=RunStatus.PENDING,
        session_id="test"
    )
    db_session.add(run)
    await db_session.flush()

    tasks = [
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=2, title="T2", status=TaskStatus.PENDING),
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=0, title="T0", status=TaskStatus.PENDING),
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=1, title="T1", status=TaskStatus.PENDING),
    ]
    for t in tasks:
        await repo.create(t)
    await db_session.flush()
    
    fetched = await repo.get_by_run(run_id)
    
    assert len(fetched) == 3
    # Verify order
    assert fetched[0].position == 0
    assert fetched[1].position == 1
    assert fetched[2].position == 2


@pytest.mark.asyncio
async def test_get_pending_oldest_first(repo, db_session):
    run_id = uuid.uuid4()
    run = AgentRun(
        id=run_id,
        goal="Test Goal",
        plan=[],
        status=RunStatus.PENDING,
        session_id="test"
    )
    db_session.add(run)
    await db_session.flush()

    t1 = Task(id=uuid.uuid4(), agent_run_id=run_id, position=0, title="T0", status=TaskStatus.PENDING)
    t2 = Task(id=uuid.uuid4(), agent_run_id=run_id, position=1, title="T1", status=TaskStatus.RUNNING)
    
    await repo.create(t1)
    await repo.create(t2)
    await db_session.flush()
    
    next_pending = await repo.get_next_pending(run_id)
    
    assert next_pending is not None
    assert next_pending.id == t1.id
