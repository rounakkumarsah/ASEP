"""
ASEP — Unit Tests for Checkpoint Manager
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.settings import Settings
from src.runtime.checkpoints import (
    CheckpointManager,
    close_postgres_checkpointer,
    init_postgres_checkpointer,
)


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset the module-level globals in checkpoints.py before and after each test."""
    with (
        patch("src.runtime.checkpoints._pool", None),
        patch("src.runtime.checkpoints._saver", None),
    ):
        yield


@pytest.mark.asyncio
async def test_checkpoint_manager_default_fallback():
    """Verify CheckpointManager defaults to MemorySaver when database checkpointer is uninitialized."""
    manager = CheckpointManager()
    checkpointer = manager.get_checkpointer()

    from langgraph.checkpoint.memory import MemorySaver

    assert isinstance(checkpointer, MemorySaver)


@pytest.mark.asyncio
async def test_init_postgres_checkpointer_standardize_dsn():
    """Verify that SQLAlchemy's asyncpg connection string is standardized for psycopg3."""
    mock_settings = MagicMock(spec=Settings)
    # Simulate SQLAlchemy DSN format
    mock_settings.DATABASE_URL = "postgresql+asyncpg://asep:changeme@localhost:5432/asep"

    mock_pool_instance = AsyncMock()
    mock_pool_class = MagicMock(return_value=mock_pool_instance)

    mock_saver_instance = AsyncMock()
    mock_saver_class = MagicMock(return_value=mock_saver_instance)

    with (
        patch("src.runtime.checkpoints.get_settings", return_value=mock_settings),
        patch("psycopg_pool.AsyncConnectionPool", mock_pool_class),
        patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", mock_saver_class),
    ):

        await init_postgres_checkpointer()

        # Check standardisation occurred correctly
        mock_pool_class.assert_called_once()
        call_kwargs = mock_pool_class.call_args[1]
        assert call_kwargs["conninfo"] == "postgresql://asep:changeme@localhost:5432/asep"
        assert call_kwargs["kwargs"] == {"autocommit": True}

        # Verify pool open and saver setup are executed
        mock_pool_instance.open.assert_called_once()
        mock_saver_class.assert_called_once_with(mock_pool_instance)
        mock_saver_instance.setup.assert_called_once()


@pytest.mark.asyncio
async def test_postgres_checkpointer_graceful_fallback():
    """Verify connection failure triggers a fallback to MemorySaver instead of propagating the error."""
    mock_settings = MagicMock(spec=Settings)
    mock_settings.DATABASE_URL = "postgresql://localhost/dummy"

    # Simulate connection error
    mock_pool_class = MagicMock(side_effect=ConnectionRefusedError("Connection refused"))

    with (
        patch("src.runtime.checkpoints.get_settings", return_value=mock_settings),
        patch("psycopg_pool.AsyncConnectionPool", mock_pool_class),
    ):

        await init_postgres_checkpointer()

        # Manager should fall back to MemorySaver cleanly
        manager = CheckpointManager()
        checkpointer = manager.get_checkpointer()
        from langgraph.checkpoint.memory import MemorySaver

        assert isinstance(checkpointer, MemorySaver)


@pytest.mark.asyncio
async def test_close_postgres_checkpointer():
    """Verify close_postgres_checkpointer disposes of the connection pool cleanly."""
    mock_pool = AsyncMock()

    with (
        patch("src.runtime.checkpoints._pool", mock_pool),
        patch("src.runtime.checkpoints._saver", MagicMock()),
    ):

        await close_postgres_checkpointer()

        mock_pool.close.assert_called_once()

        # Verify global references are cleared
        import src.runtime.checkpoints as cp

        assert cp._pool is None
        assert cp._saver is None
