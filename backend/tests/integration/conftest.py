"""
Integration Test Fixtures
=========================
Database connection and savepoint fixtures for integration tests.
These ensure that each test runs inside a nested transaction and is rolled back.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config.settings import get_settings


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create a single async engine for the test session."""
    settings = get_settings()
    # Ensure tests run against the dedicated test database
    test_url = settings.DATABASE_URL.replace("/asep", "/asep_test")
    engine = create_async_engine(test_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session_factory(db_engine):
    """
    Yields an async_sessionmaker bound to a connection with a nested transaction.
    This ensures that when `session.commit()` is called by the Unit of Work,
    it only commits the savepoint, and the root transaction is rolled back after the test.
    """
    async with db_engine.connect() as conn:
        # Start a root transaction
        await conn.begin()
        # Start a nested transaction (savepoint)
        await conn.begin_nested()
        
        session_factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        yield session_factory
        
        # Roll back everything after the test completes
        await conn.rollback()


@pytest_asyncio.fixture
async def db_session(db_session_factory):
    """Yields a raw AsyncSession for tests that bypass UoW (e.g., repository tests)."""
    async with db_session_factory() as session:
        yield session
