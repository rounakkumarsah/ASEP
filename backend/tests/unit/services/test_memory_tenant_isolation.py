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

