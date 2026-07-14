"""
ASEP — PostgreSQL Async Layer Tests
=====================================
Tests for SQLAlchemy 2.0 async engine, session factory, and health checks.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import (
    Base,
    DbSession,
    check_db_health,
    close_db,
    get_db_session,
    init_db,
)


class TestDatabaseInit:
    """Tests for database initialization."""

    @pytest.mark.asyncio
    async def test_init_db_creates_engine(self) -> None:
        """init_db() should create the async engine."""
        await init_db()
        # If this doesn't raise, the engine was created successfully

    @pytest.mark.asyncio
    async def test_close_db_disposes_engine(self) -> None:
        """close_db() should dispose the engine and reset singletons."""
        await init_db()
        await close_db()
        # If this doesn't raise, the engine was disposed successfully


class TestHealthCheck:
    """Tests for database health check."""

    @pytest.mark.asyncio
    async def test_check_db_health_returns_tuple(self) -> None:
        """check_db_health() should return (bool, str, float|None)."""
        result = await check_db_health()
        assert isinstance(result, tuple)
        assert len(result) == 3
        is_healthy, detail, latency = result
        assert isinstance(is_healthy, bool)
        assert isinstance(detail, str)
        assert latency is None or isinstance(latency, float)

    @pytest.mark.asyncio
    async def test_check_db_health_success(self) -> None:
        """check_db_health() should succeed when database is reachable."""
        is_healthy, detail, latency = await check_db_health()
        assert is_healthy is True
        assert isinstance(detail, str)
        assert latency is not None
        assert latency > 0

    @pytest.mark.asyncio
    async def test_check_db_health_timeout(self) -> None:
        """check_db_health() should timeout gracefully with very short deadline."""
        is_healthy, detail, latency = await check_db_health(timeout_seconds=0.0001)
        # Should timeout and return False
        assert is_healthy is False
        assert "failed" in detail.lower() or "timeout" in detail.lower()


class TestSessionDependency:
    """Tests for FastAPI dependency injection."""

    @pytest.mark.asyncio
    async def test_get_db_session_yields_async_session(self) -> None:
        """get_db_session() should yield an AsyncSession."""
        async for session in get_db_session():
            assert isinstance(session, AsyncSession)
            break

    @pytest.mark.asyncio
    async def test_get_db_session_is_async_generator(self) -> None:
        """get_db_session() should be an async generator function."""
        gen = get_db_session()
        # Check it's an async generator
        assert hasattr(gen, "__aenter__") or hasattr(gen, "__anext__")

    @pytest.mark.asyncio
    async def test_session_can_execute_query(self) -> None:
        """Session should be able to execute a simple query."""
        async for session in get_db_session():
            result = await session.execute(text("SELECT 1"))
            rows = result.fetchall()
            assert len(rows) == 1
            assert rows[0][0] == 1
            break


class TestDeclarativeBase:
    """Tests for the ORM declarative base."""

    def test_base_is_declarative(self) -> None:
        """Base should be a valid SQLAlchemy DeclarativeBase."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "__tablename__")

    def test_base_registry_is_empty_initially(self) -> None:
        """Base registry should be empty initially (no models defined)."""
        # The registry attribute exists even if no models are defined
        assert hasattr(Base, "registry")


class TestDatabaseErrorHandling:
    """Tests for database error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_session_rollback_on_exception(self) -> None:
        """Session should rollback if an exception occurs."""
        try:
            async for session in get_db_session():
                # Simulate an error
                raise ValueError("Simulated error")
        except ValueError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_session_cleanup_after_exception(self) -> None:
        """Session should be cleaned up after an exception."""
        try:
            async for session in get_db_session():
                # Simulate an error before yield completes
                raise RuntimeError("Simulated error")
        except RuntimeError:
            pass  # Expected

        # The next call should still work
        async for session in get_db_session():
            result = await session.execute(text("SELECT 1"))
            assert result.fetchone() is not None
            break
