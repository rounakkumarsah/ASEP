"""
ASEP — Checkpoint Abstraction Wrapper
"""

import logging
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level singletons for AsyncPostgresSaver connection pool
_pool: Any | None = None
_saver: BaseCheckpointSaver | None = None


class CheckpointManager:
    """Wrapper class managing thread-safe workflow checkpoint savers."""

    def __init__(self) -> None:
        pass

    def get_checkpointer(self) -> BaseCheckpointSaver:
        """Retrieve the compiled checkpoint saver instance.

        Falls back to MemorySaver if AsyncPostgresSaver is not initialized.
        """
        global _saver
        if _saver is not None:
            return _saver

        # Fallback to MemorySaver for local dev/testing
        logger.debug("AsyncPostgresSaver not initialized. Falling back to MemorySaver.")
        return MemorySaver()


async def init_postgres_checkpointer() -> None:
    """Initialize the Postgres connection pool and AsyncPostgresSaver.

    This is called during application startup within the FastAPI lifespan.
    """
    global _pool, _saver
    if _saver is not None:
        return  # Already initialized

    settings = get_settings()
    db_url = settings.DATABASE_URL

    # Standardize to psycopg3 schema (remove +asyncpg)
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif "postgres://" in db_url:
        db_url = db_url.replace("postgres://", "postgresql://")

    logger.info("Initializing Postgres checkpointer connection pool.")

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        # autocommit=True is MANDATORY for LangGraph's saver
        _pool = AsyncConnectionPool(
            conninfo=db_url, max_size=20, open=False, kwargs={"autocommit": True}
        )
        await _pool.open()

        _saver = AsyncPostgresSaver(_pool)
        # setup() is idempotent: it creates the required tables if they do not exist
        await _saver.setup()

        logger.info("Postgres checkpointer successfully initialized and tables verified.")
    except Exception as exc:
        logger.warning(
            "Failed to initialize Postgres checkpointer (%s). "
            "Falling back to in-memory checkpointer (state will not be durable).",
            str(exc),
        )
        _saver = None
        _pool = None


async def close_postgres_checkpointer() -> None:
    """Close the Postgres checkpointer connection pool on application shutdown."""
    global _pool, _saver
    if _pool is not None:
        logger.info("Closing Postgres checkpointer connection pool.")
        await _pool.close()
        _pool = None
    _saver = None
