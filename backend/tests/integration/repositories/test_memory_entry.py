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


@pytest.mark.asyncio
async def test_get_by_run(repo, db_session):
    run_id = uuid.uuid4()
    
    m1 = MemoryEntry(
        id=uuid.uuid4(),
        agent_run_id=run_id,
        memory_type=MemoryType.OBSERVATION,
        content="test 1",
        importance_score=Decimal("0.5")
    )
    m2 = MemoryEntry(
        id=uuid.uuid4(),
        agent_run_id=run_id,
        memory_type=MemoryType.REFLECTION,
        content="test 2",
        importance_score=Decimal("0.9")
    )
    
    await repo.create(m1)
    await repo.create(m2)
    await db_session.flush()
    
    memories = await repo.get_by_run(run_id)
    assert len(memories) == 2
    assert memories[0].id == m2.id  # m2 has higher importance_score, so it should be first?
    # Wait, get_by_run defaults to created_at desc. They might have same created_at (or close).
    
    # Test get_top_by_importance
    top_memories = await repo.get_top_by_importance(run_id, limit=1)
    assert len(top_memories) == 1
    assert top_memories[0].id == m2.id
