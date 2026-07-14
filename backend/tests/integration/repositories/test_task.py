"""
Integration Tests for TaskRepository
"""

import uuid
import pytest
from sqlalchemy.exc import NoResultFound

from src.db.models.task import Task, TaskStatus, TaskType
from src.repositories.task import TaskRepository


@pytest.fixture
def repo(db_session):
    return TaskRepository(db_session)


@pytest.mark.asyncio
async def test_get_by_run(repo, db_session):
    run_id = uuid.uuid4()
    tasks = [
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=2, title="T2", task_type=TaskType.COMMAND, status=TaskStatus.PENDING, prompt="test"),
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=0, title="T0", task_type=TaskType.COMMAND, status=TaskStatus.PENDING, prompt="test"),
        Task(id=uuid.uuid4(), agent_run_id=run_id, position=1, title="T1", task_type=TaskType.COMMAND, status=TaskStatus.PENDING, prompt="test"),
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
    # Insert one pending and one running
    run_id = uuid.uuid4()
    t1 = Task(id=uuid.uuid4(), agent_run_id=run_id, position=0, title="T0", task_type=TaskType.COMMAND, status=TaskStatus.PENDING, prompt="test")
    t2 = Task(id=uuid.uuid4(), agent_run_id=run_id, position=1, title="T1", task_type=TaskType.COMMAND, status=TaskStatus.RUNNING, prompt="test")
    
    await repo.create(t1)
    await repo.create(t2)
    await db_session.flush()
    
    pending = await repo.get_pending_oldest_first(limit=5)
    
    # We might have other tasks in DB, but the ones we just added:
    assert t1.id in [p.id for p in pending]
    assert t2.id not in [p.id for p in pending]
