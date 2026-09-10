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


def test_set_auth_cookies_remember_me_enabled():
    """Verify that remember_me=True sets 30-day max_age and samesite=lax."""
    from fastapi import Response
    from src.api.routers.auth import _set_auth_cookies
    from src.auth.schemas import RefreshTokenResponse

    tokens = RefreshTokenResponse(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
    )
    res = Response()
    _set_auth_cookies(res, tokens, app_env="production", remember_me=True)

    raw_cookies = res.headers.getlist("set-cookie")
    cookie_str = "; ".join(raw_cookies)

    assert "access_token=test_access_token" in cookie_str
    assert "Max-Age=2592000" in cookie_str
    assert "SameSite=lax" in cookie_str or "samesite=lax" in cookie_str
    assert "refresh_token=test_refresh_token" in cookie_str


def test_set_auth_cookies_remember_me_disabled():
    """Verify that remember_me=False creates a session-only access token cookie."""
    from fastapi import Response
    from src.api.routers.auth import _set_auth_cookies
    from src.auth.schemas import RefreshTokenResponse

    tokens = RefreshTokenResponse(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
    )
    res = Response()
    _set_auth_cookies(res, tokens, app_env="production", remember_me=False)

    raw_cookies = res.headers.getlist("set-cookie")
    access_cookie = [c for c in raw_cookies if c.startswith("access_token=")][0]
    refresh_cookie = [c for c in raw_cookies if c.startswith("refresh_token=")][0]

    # Session cookie has no Max-Age
    assert "Max-Age" not in access_cookie
    # Refresh cookie has default 7-day Max-Age (604800)
    assert "Max-Age=604800" in refresh_cookie


def test_schemas_remember_me_aliasing():
    """Verify that both camelCase and snake_case remember_me are accepted."""
    from src.auth.schemas import LoginRequest, RefreshTokenRequest

    # LoginRequest accepting snake_case
    l1 = LoginRequest(email="test@asep.dev", password="password123456", remember_me=True)
    assert l1.rememberMe is True

    # LoginRequest accepting camelCase
    l2 = LoginRequest(email="test@asep.dev", password="password123456", rememberMe=True)
    assert l2.rememberMe is True

    # RefreshTokenRequest accepting snake_case
    r1 = RefreshTokenRequest(remember_me=True)
    assert r1.remember_me is True

    # RefreshTokenRequest accepting camelCase
    r2 = RefreshTokenRequest(rememberMe=False)
    assert r2.remember_me is False

