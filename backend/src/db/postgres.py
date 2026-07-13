"""
ASEP — PostgreSQL Connection Manager
=======================================
Manages the SQLAlchemy 2.0 async engine and session factory.

Provides:
  - AsyncEngine with asyncpg driver
  - Dependency injection for AsyncSession
  - Health check via explicit connection ping
  - Graceful lifecycle hooks (init / close)
  - DeclarativeBase for all ORM models

Only the connection machinery lives here.
All ORM models and migrations belong in src/db/models/.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """
    Create or return the cached async SQLAlchemy engine.

    The engine uses asyncpg as the async driver and is configured
    with pool settings appropriate for production workloads.

    Returns:
        AsyncEngine: The configured async engine.

    Raises:
        RuntimeError: If database URL is invalid.
    """
    global _engine
    if _engine is not None:
        return _engine

    settings = get_settings()
    logger.info("Creating PostgreSQL async engine", extra={"database_url": settings.DATABASE_URL})

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.APP_ENV == "development",
        # Connection pool settings
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        # Pre-ping ensures stale connections are recycled
        pool_pre_ping=True,
        # Driver-specific settings for asyncpg
        connect_args={
            "timeout": 10,
            "command_timeout": 10,
            "server_settings": {
                "jit": "off",
                "random_page_cost": 1.1,
            },
        },
    )

    logger.info("PostgreSQL async engine created")
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Create or return the cached async session factory.

    The factory is bound to the async engine and configured
    for production use (no auto-expiry on commit).

    Returns:
        async_sessionmaker: The configured session factory.
    """
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    _session_factory = async_sessionmaker(
        bind=_get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _session_factory


# ---------------------------------------------------------------------------
# Declarative Base — all ORM models inherit from this
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all ASEP ORM models.

    All models should inherit from this class:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)

    TODO (Phase 0.3):
        - Add shared columns (created_at, updated_at, id) via mixin
        - Add soft-delete support
    """


# ---------------------------------------------------------------------------
# Dependency Injection — FastAPI session factory
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a scoped AsyncSession for request lifetime.

    Usage in route handlers:
        from src.db.postgres import DbSession

        @router.get("/users")
        async def list_users(db: DbSession) -> list[dict]:
            result = await db.execute(select(User))
            return result.scalars().all()

    The session is automatically:
        - Committed on success
        - Rolled back on exception

    Yields:
        AsyncSession: A scoped database session.

    Raises:
        Any exception that occurs during request processing is re-raised
        after the session is rolled back.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("Database transaction rolled back", extra={"error": str(exc)})
            raise


# Type alias for cleaner FastAPI function signatures
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Health Check — async connection ping
# ---------------------------------------------------------------------------


async def check_db_health(timeout_seconds: float = 5.0) -> tuple[bool, str, float | None]:
    """
    Check database connectivity and measure latency.

    This function:
        - Executes a simple SELECT 1 query
        - Measures latency
        - Returns status and diagnostics

    Args:
        timeout_seconds: Maximum time to wait for response (default 5s).

    Returns:
        tuple: (is_healthy, detail_string, latency_ms)
            - is_healthy: True if connection succeeds
            - detail_string: Human-readable status message
            - latency_ms: Query latency in milliseconds, or None if failed

    Examples:
        >>> is_ok, detail, latency = await check_db_health()
        >>> if is_ok:
        ...     print(f"PostgreSQL: {latency:.1f}ms")
    """
    engine = _get_engine()
    start = time.monotonic()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.monotonic() - start) * 1000
        return (True, f"Connected in {latency_ms:.1f}ms", latency_ms)
    except Exception as exc:
        latency_ms = (time.monotonic() - start) * 1000
        detail = f"Connection failed: {type(exc).__name__}: {str(exc)}"
        logger.warning("PostgreSQL health check failed", extra={"error": detail})
        return (False, detail, latency_ms)


# ---------------------------------------------------------------------------
# Lifecycle Hooks — FastAPI startup/shutdown
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """
    Initialize the database connection pool on application startup.

    This is called from the FastAPI lifespan context manager.
    It ensures the engine is created and the connection pool is ready.
    """
    engine = _get_engine()
    logger.info("Database pool initialized")

    # Verify connectivity immediately
    is_healthy, detail, _ = await check_db_health()
    if is_healthy:
        logger.info("PostgreSQL health check passed", extra={"detail": detail})
    else:
        logger.warning("PostgreSQL health check failed on startup", extra={"detail": detail})


async def close_db() -> None:
    """
    Close the database connection pool on application shutdown.

    This is called from the FastAPI lifespan context manager.
    It ensures all connections are gracefully closed.
    """
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Disposing PostgreSQL engine")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("PostgreSQL engine disposed")
