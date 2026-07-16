"""
Integration Tests for MemoryEntryRepository
"""

import uuid
from decimal import Decimal
import pytest

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.repositories.memory_entry import MemoryEntryRepository


@pytest.fixture
def repo(db_session):
    return MemoryEntryRepository(db_session)


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
    
    m1 = MemoryEntry(
        id=uuid.uuid4(),
        agent_run_id=run_id,
        memory_type=MemoryType.EPISODIC,
        content="test 1",
        importance_score=Decimal("0.500")
    )
    m2 = MemoryEntry(
        id=uuid.uuid4(),
        agent_run_id=run_id,
        memory_type=MemoryType.SEMANTIC,
        content="test 2",
        importance_score=Decimal("0.900")
    )
    
    await repo.create(m1)
    await repo.create(m2)
    await db_session.flush()
    
    memories = await repo.get_by_agent_run(run_id)
    assert len(memories) == 2
    
    # Test get_top_by_importance
    top_memories = await repo.get_top_by_importance(namespace="default", memory_type=MemoryType.SEMANTIC, limit=1)
    assert len(top_memories) == 1
    assert top_memories[0].id == m2.id
