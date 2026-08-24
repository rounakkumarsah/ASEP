from unittest.mock import AsyncMock, MagicMock

import pytest

from src.auth.rate_limit import check_rate_limit
from src.auth.service import normalize_email


@pytest.mark.asyncio
async def test_check_rate_limit_first_hit_sets_expiry():
    """Verify that the first hit (count=1) sets the expiry window."""
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_pipe.incr = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[1])

    mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipe
    mock_redis.pipeline.return_value.__aexit__.return_value = None
    mock_redis.get = AsyncMock(return_value="1")
    mock_redis.expire = AsyncMock()

    allowed = await check_rate_limit(mock_redis, "test:key", max_attempts=5, window_seconds=600)

    assert allowed is True
    mock_redis.expire.assert_awaited_once_with("test:key", 600)


@pytest.mark.asyncio
async def test_check_rate_limit_subsequent_hit_preserves_expiry():
    """Verify that subsequent hits (>1) do NOT re-call expire to avoid extending the window."""
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_pipe.incr = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[3])

    mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipe
    mock_redis.pipeline.return_value.__aexit__.return_value = None
    mock_redis.get = AsyncMock(return_value="3")
    mock_redis.expire = AsyncMock()

    allowed = await check_rate_limit(mock_redis, "test:key", max_attempts=5, window_seconds=600)

    assert allowed is True
    mock_redis.expire.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded():
    """Verify that requests beyond max_attempts return False."""
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_pipe.incr = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[6])

    mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipe
    mock_redis.pipeline.return_value.__aexit__.return_value = None
    mock_redis.get = AsyncMock(return_value="6")
    mock_redis.ttl = AsyncMock(return_value=120)

    allowed = await check_rate_limit(mock_redis, "test:key", max_attempts=5, window_seconds=600)

    assert allowed is False


def test_normalize_email_standard():
    assert normalize_email("  User@Example.COM  ") == "user@example.com"


def test_normalize_email_gmail_alias():
    assert normalize_email("john.doe+test@gmail.com") == "johndoe@gmail.com"
    assert normalize_email("J.O.H.N+newsletter@googlemail.com") == "john@googlemail.com"


def test_normalize_email_non_gmail_preserves_dots():
    assert normalize_email("john.doe@company.org") == "john.doe@company.org"
