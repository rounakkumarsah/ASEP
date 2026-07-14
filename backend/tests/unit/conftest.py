"""
Unit Test Fixtures
==================
Mocks for Unit of Work and Repositories to isolate Service Layer testing.
"""

from unittest.mock import AsyncMock

import pytest

from src.unit_of_work.base import AbstractUnitOfWork


class MockUnitOfWork(AbstractUnitOfWork):
    """
    Mock implementation of AbstractUnitOfWork.
    All repositories and transactional methods are AsyncMocks.
    """

    def __init__(self):
        super().__init__()
        # Mock repositories
        self.agent_runs = AsyncMock()
        self.tasks = AsyncMock()
        self.memory_entries = AsyncMock()
        self.audit_logs = AsyncMock()
        self.knowledge_documents = AsyncMock()
        
        # Mock transaction methods
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()


@pytest.fixture
def mock_uow():
    """Returns a fresh MockUnitOfWork instance."""
    return MockUnitOfWork()


@pytest.fixture
def uow_factory(mock_uow):
    """Returns a factory function that yields the mock_uow."""
    return lambda: mock_uow
