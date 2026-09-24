import uuid
import pytest
from datetime import datetime, timedelta, UTC

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_tenant_isolation(uow_factory, mock_uow):
    service = MemoryService(uow_factory)
    
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()
    
    # Store memory for Org A
    entry_a = MemoryEntry(
        id=uuid.uuid4(),
        org_id=org_a,
        content="Org A secret",
        namespace="default",
        memory_type=MemoryType.EPISODIC,
        importance_score=0.5
    )
    
    # Store memory for Org B
    entry_b = MemoryEntry(
        id=uuid.uuid4(),
        org_id=org_b,
        content="Org B secret",
        namespace="default",
        memory_type=MemoryType.EPISODIC,
        importance_score=0.5
    )
    
    # Setup mock to simulate isolation query logic
    async def mock_get_by_namespace(namespace, org_id, limit=50, offset=0):
        all_memories = [entry_a, entry_b]
        return [m for m in all_memories if m.org_id == org_id]
        
    mock_uow.memory_entries.get_by_namespace.side_effect = mock_get_by_namespace
    
    # User A reads memories
    memories_a = await service.get_by_namespace("default", org_id=org_a)
    assert len(memories_a) == 1
    assert memories_a[0].content == "Org A secret"
    assert memories_a[0].org_id == org_a
    
    # User B reads memories
    memories_b = await service.get_by_namespace("default", org_id=org_b)
    assert len(memories_b) == 1
    assert memories_b[0].content == "Org B secret"
    assert memories_b[0].org_id == org_b

@pytest.mark.asyncio
async def test_ttl_expiry(uow_factory, mock_uow):
    service = MemoryService(uow_factory)
    org_a = uuid.uuid4()
    
    # Expired memory
    entry_expired = MemoryEntry(
        id=uuid.uuid4(),
        org_id=org_a,
        content="Expired",
        namespace="default",
        memory_type=MemoryType.WORKING,
        importance_score=0.5,
        expires_at=datetime.now(UTC) - timedelta(hours=1)
    )
    
    # Valid memory
    entry_valid = MemoryEntry(
        id=uuid.uuid4(),
        org_id=org_a,
        content="Valid",
        namespace="default",
        memory_type=MemoryType.WORKING,
        importance_score=0.5,
        expires_at=datetime.now(UTC) + timedelta(hours=1)
    )
    
    async def mock_get_by_namespace(namespace, org_id, limit=50, offset=0):
        all_memories = [entry_expired, entry_valid]
        return [m for m in all_memories if m.org_id == org_id and (m.expires_at is None or m.expires_at > datetime.now(UTC))]
        
    mock_uow.memory_entries.get_by_namespace.side_effect = mock_get_by_namespace
    
    memories = await service.get_by_namespace("default", org_id=org_a)
    assert len(memories) == 1
    assert memories[0].content == "Valid"


@pytest.mark.asyncio
async def test_get_top_memories_cross_tenant_isolation(uow_factory, mock_uow):
    """Verify that entries created with Org A are NOT returned when querying with Org B."""
    service = MemoryService(uow_factory)

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    entry_a = MemoryEntry(
        id=uuid.uuid4(),
        org_id=org_a,
        content="Secret belonging only to Org A",
        namespace="default",
        memory_type=MemoryType.SEMANTIC,
        importance_score=0.9,
    )

    async def mock_get_top_by_importance(namespace, memory_type, org_id, limit=50):
        all_memories = [entry_a]
        return [
            m for m in all_memories
            if m.namespace == namespace and m.memory_type == memory_type and m.org_id == org_id
        ]

    mock_uow.memory_entries.get_top_by_importance.side_effect = mock_get_top_by_importance

    # Querying with Org B MUST return ZERO entries
    memories_b = await service.get_top_memories(
        namespace="default",
        memory_type=MemoryType.SEMANTIC,
        org_id=org_b,
        limit=10,
    )
    assert len(memories_b) == 0, "Security failure: Org B retrieved memories belonging to Org A!"

    # Querying with Org A MUST return Org A's entry
    memories_a = await service.get_top_memories(
        namespace="default",
        memory_type=MemoryType.SEMANTIC,
        org_id=org_a,
        limit=10,
    )
    assert len(memories_a) == 1
    assert memories_a[0].content == "Secret belonging only to Org A"
    assert memories_a[0].org_id == org_a


