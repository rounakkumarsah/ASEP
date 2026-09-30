import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.exc import ProgrammingError

from src.db.models.user import User
from src.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_user_repository_fallback_on_missing_column():
    """Verify UserRepository falls back and defers monthly_token_quota when column is missing."""
    session_mock = AsyncMock()

    # First execute fails with column missing ProgrammingError
    error_msg = "(sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) column users.monthly_token_quota does not exist"
    programming_error = ProgrammingError("statement", {}, Exception(error_msg))

    mock_user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
    )

    mock_fallback_result = MagicMock()
    mock_fallback_result.scalars.return_value.first.return_value = mock_user

    session_mock.execute.side_effect = [
        programming_error,
        mock_fallback_result,
    ]

    repo = UserRepository(session_mock)

    # Test get_by_email
    user = await repo.get_by_email("test@example.com")

    assert user is not None
    assert user.email == "test@example.com"
    # Ensure rollback was called
    session_mock.rollback.assert_awaited_once()
    # Ensure execute was called twice (initial + fallback)
    assert session_mock.execute.await_count == 2
    # Ensure monthly_token_quota was populated in __dict__
    assert user.monthly_token_quota == 100000


@pytest.mark.asyncio
async def test_user_repository_fallback_on_get_by_username():
    """Verify UserRepository fallback works for get_by_username."""
    session_mock = AsyncMock()

    error_msg = "column users.monthly_token_quota does not exist"
    programming_error = ProgrammingError("statement", {}, Exception(error_msg))

    mock_user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        username="testuser2",
    )

    mock_fallback_result = MagicMock()
    mock_fallback_result.scalars.return_value.first.return_value = mock_user

    session_mock.execute.side_effect = [
        programming_error,
        mock_fallback_result,
    ]

    repo = UserRepository(session_mock)

    user = await repo.get_by_username("testuser2")

    assert user is not None
    assert user.username == "testuser2"
    session_mock.rollback.assert_awaited_once()
    assert session_mock.execute.await_count == 2
    assert user.monthly_token_quota == 100000


@pytest.mark.asyncio
async def test_user_repository_fallback_on_get():
    """Verify UserRepository fallback works for get by primary key."""
    session_mock = AsyncMock()

    error_msg = "column users.monthly_token_quota does not exist"
    programming_error = ProgrammingError("statement", {}, Exception(error_msg))

    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        email="test3@example.com",
        username="testuser3",
    )

    session_mock.get.side_effect = [
        programming_error,
        mock_user,
    ]

    repo = UserRepository(session_mock)

    user = await repo.get(user_id)

    assert user is not None
    assert user.id == user_id
    session_mock.rollback.assert_awaited_once()
    assert session_mock.get.await_count == 2
    assert user.monthly_token_quota == 100000


@pytest.mark.asyncio
async def test_user_repository_reraises_other_programming_errors():
    """Verify UserRepository does NOT catch unrelated ProgrammingErrors."""
    session_mock = AsyncMock()

    programming_error = ProgrammingError("statement", {}, Exception("syntax error at or near 'WHERE'"))
    session_mock.execute.side_effect = programming_error

    repo = UserRepository(session_mock)

    with pytest.raises(ProgrammingError) as exc_info:
        await repo.get_by_email("test@example.com")

    assert "syntax error" in str(exc_info.value)
    session_mock.rollback.assert_not_awaited()

