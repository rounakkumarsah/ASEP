"""
Tests for MemoryService
"""

import uuid
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock

from src.db.models.memory_entry import MemoryEntry, MemoryType
from src.services.memory_service import MemoryService


@pytest.fixture
def memory_service(uow_factory):
    return MemoryService(uow_factory)


@pytest.mark.asyncio
async def test_add_memory(memory_service, mock_uow):
    run_id = uuid.uuid4()
    mock_uow.memory_entries.create.side_effect = lambda m: m
    
    result = await memory_service.store_memory(
        namespace="test-namespace",
        agent_run_id=run_id,
        memory_type=MemoryType.EPISODIC,
        content="Test observation",
        importance_score=0.75,
        embedding_id=uuid.uuid4(),
        embedding_model="test-model"
    )
    
    assert result.memory_type == MemoryType.EPISODIC
    assert result.content == "Test observation"
    assert result.importance_score == Decimal("0.750")
    
    mock_uow.memory_entries.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_memory_validation(memory_service):
    with pytest.raises(ValueError, match="MemoryEntry.content must be a non-empty string."):
        await memory_service.store_memory(
            namespace="test-namespace",
            agent_run_id=uuid.uuid4(),
            memory_type=MemoryType.EPISODIC,
            content="",
            importance_score=0.5
        )
        
    with pytest.raises(ValueError, match="importance_score must be in"):
        await memory_service.store_memory(
            namespace="test-namespace",
            agent_run_id=uuid.uuid4(),
            memory_type=MemoryType.EPISODIC,
            content="test",
            importance_score=1.5
        )
        
    with pytest.raises(ValueError, match="embedding_model may not be set without embedding_id"):
        await memory_service.store_memory(
            namespace="test-namespace",
            agent_run_id=uuid.uuid4(),
            memory_type=MemoryType.EPISODIC,
            content="test",
            importance_score=0.5,
            embedding_model="test-model" # Missing embedding_id
        )


@pytest.mark.asyncio
async def test_mark_accessed(memory_service, mock_uow):
    memory_id = uuid.uuid4()
    mock_entry = MemoryEntry(id=memory_id, access_count=0)
    mock_uow.memory_entries.increment_access_count.return_value = MemoryEntry(id=memory_id, access_count=1)
    
    result = await memory_service.record_access(memory_id)
    
    assert result.access_count == 1
    mock_uow.memory_entries.increment_access_count.assert_awaited_once_with(memory_id)
    mock_uow.commit.assert_awaited_once()
