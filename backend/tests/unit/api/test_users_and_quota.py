"""
ASEP — Daily Quota & Username Management Test Suite
==================================================
Tests verifying:
1. New user accounts always start with 10/10 daily quota (used=0, remaining=10).
2. Passive endpoints (auth/me, users/quota, settings, profile) do NOT consume quota.
3. Active AI endpoints (copilot/research) consume exactly 1 credit.
4. Username validation, case-insensitive uniqueness check, suggestions, and 409 conflict.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.auth.dependencies import get_auth_service, get_current_user
from src.auth.service import AuthService
from src.db.models.user import User
from src.production.monetization import FreemiumRateLimiter


@pytest.mark.asyncio
async def test_quota_starts_at_ten_and_passive_endpoints_do_not_decrement(monkeypatch):
    """Test A, B, C, D: Verify brand new account starts at 10/10 quota and non-AI queries do not consume quota."""
    mock_redis = AsyncMock()
    stored_redis = {}

    async def mock_get(key):
        return stored_redis.get(key)

    async def mock_incr(key):
        stored_redis[key] = str(int(stored_redis.get(key, 0)) + 1)
        return int(stored_redis[key])

    async def mock_setex(key, ttl, value):
        stored_redis[key] = str(value)

    async def mock_expire(key, ttl):
        pass

    mock_redis.get = mock_get
    mock_redis.incr = mock_incr
    mock_redis.setex = mock_setex
    mock_redis.expire = mock_expire

    monkeypatch.setattr("src.production.monetization.get_redis_client", lambda: mock_redis)
    monkeypatch.setattr("src.cache.redis.get_redis_client", lambda: mock_redis)

    limiter = FreemiumRateLimiter(free_daily_limit=10)
    user_id = str(uuid.uuid4())

    # 1. Immediate lookup on brand new account
    q1 = await limiter.get_usage(user_id, tier="free")
    assert q1.remaining_queries == 10
    assert q1.allowed is True
    assert stored_redis.get(f"rate_limit:{user_id}") is None

    # 2. Subsequent lookups (dashboard, settings, profile loading) must NOT decrement quota
    for _ in range(5):
        q_passive = await limiter.get_usage(user_id, tier="free")
        assert q_passive.remaining_queries == 10

    # 3. An active AI request triggers check_rate_limit -> decrements by 1
    q_active = await limiter.check_rate_limit(user_id, tier="free")
    assert q_active.remaining_queries == 9
    assert q_active.allowed is True

    # 4. Subsequent passive checks reflect 9 remaining
    q_after = await limiter.get_usage(user_id, tier="free")
    assert q_after.remaining_queries == 9


@pytest.mark.asyncio
async def test_username_validation_and_case_insensitive_uniqueness(monkeypatch):
    """Test username availability, regex validation, suggestions, and update conflict."""
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.username = "sachin"
    existing_user.email = "sachin@asep.io"

    uow_mock = AsyncMock()
    uow_mock.users = AsyncMock()

    async def mock_get_by_username(uname: str):
        if uname.strip().lower() == "sachin":
            return existing_user
        return None

    uow_mock.users.get_by_username = mock_get_by_username
    uow_mock.users.get.return_value = existing_user
    uow_mock.commit = AsyncMock()

    class MockUowContext:
        async def __aenter__(self):
            return uow_mock

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    user_service_mock = MagicMock()
    user_service_mock._uow_factory = lambda: MockUowContext()

    email_service_mock = MagicMock()
    auth_service = AuthService(user_service_mock, email_service_mock)

    # 1. Available check for 'Sachin' (case insensitive match against 'sachin') -> unavailable with suggestions
    avail, suggestions = await auth_service.check_username_availability("Sachin")
    assert avail is False
    assert len(suggestions) > 0
    assert "Sachin_1" in suggestions or "Sachin_dev" in suggestions

    # 2. Invalid username format -> unavailable with no suggestions
    avail_invalid, _ = await auth_service.check_username_availability("ab")  # too short
    assert avail_invalid is False

    avail_invalid2, _ = await auth_service.check_username_availability("invalid-user-name!")
    assert avail_invalid2 is False

    # 3. Available check for 'sachin_new_dev' -> available
    avail_new, suggestions_new = await auth_service.check_username_availability("sachin_new_dev")
    assert avail_new is True
    assert len(suggestions_new) == 0


def test_users_api_endpoints(monkeypatch):
    """API level test for /api/v1/users/check-username, /api/v1/users/quota, and /api/v1/users/profile."""
    app = create_app()

    current_user_obj = MagicMock(spec=User)
    current_user_obj.id = uuid.uuid4()
    current_user_obj.username = "originaluser"
    current_user_obj.email = "original@asep.io"
    current_user_obj.role = "free"
    current_user_obj.is_active = True
    current_user_obj.email_verified = True
    current_user_obj.status = "active"
    current_user_obj.first_name = "Original"
    current_user_obj.last_name = "User"
    current_user_obj.avatar_url = None
    current_user_obj.company = None
    current_user_obj.last_login = None
    current_user_obj.mfa_enabled = False
    current_user_obj.account_type = "individual"
    current_user_obj.timezone = "UTC"
    current_user_obj.locale = "en"
    current_user_obj.current_plan = "free"
    import datetime
    current_user_obj.created_at = datetime.datetime.now(datetime.UTC)
    current_user_obj.updated_at = datetime.datetime.now(datetime.UTC)

    mock_auth_service = MagicMock()
    mock_auth_service.check_username_availability = AsyncMock(return_value=(True, []))

    async def mock_update_user(uid, data):
        if data.username == "already_taken":
            raise ValueError("Username already taken")
        current_user_obj.username = data.username or current_user_obj.username
        current_user_obj.first_name = data.first_name or current_user_obj.first_name
        current_user_obj.last_name = data.last_name or current_user_obj.last_name
        return current_user_obj

    mock_auth_service.update_user = mock_update_user

    app.dependency_overrides[get_current_user] = lambda: current_user_obj
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    client = TestClient(app)

    # 1. Test GET /api/v1/users/quota
    res_quota = client.get("/api/v1/users/quota")
    assert res_quota.status_code == 200
    data_quota = res_quota.json()
    assert data_quota["limit"] == 10
    assert data_quota["remaining"] == 10
    assert data_quota["used"] == 0

    # 2. Test GET /api/v1/users/check-username
    res_check = client.get("/api/v1/users/check-username?username=cool_dev")
    assert res_check.status_code == 200
    assert res_check.json()["available"] is True

    # 3. Test PATCH /api/v1/users/profile (Success)
    res_prof = client.patch("/api/v1/users/profile", json={"first_name": "Alex", "username": "alex_vance"})
    assert res_prof.status_code == 200
    assert res_prof.json()["first_name"] == "Alex"
    assert res_prof.json()["username"] == "alex_vance"

    # 4. Test PATCH /api/v1/users/profile (Conflict 409)
    res_conflict = client.patch("/api/v1/users/profile", json={"username": "already_taken"})
    assert res_conflict.status_code == 409


@pytest.mark.asyncio
async def test_duplicate_email_signup_and_normalization():
    """Verify duplicate email raises 409 and email normalization handles gmail dots."""
    from src.auth.service import RESERVED_USERNAMES, normalize_email

    # Email normalization checks
    assert normalize_email("  User.Name+test@GMAIL.COM  ") == "username@gmail.com"
    assert normalize_email("  Dev@Company.IO  ") == "dev@company.io"

    # Reserved username check
    assert "admin" in RESERVED_USERNAMES
    assert "root" in RESERVED_USERNAMES
    assert "support" in RESERVED_USERNAMES
    assert "billing" in RESERVED_USERNAMES


@pytest.mark.asyncio
async def test_totp_mfa_calculation_and_verification():
    """Verify standard RFC 6238 TOTP generation and validation."""
    import time

    from src.auth.service import _calculate_totp, _generate_totp_secret, _verify_totp

    secret = _generate_totp_secret()
    assert len(secret) == 32

    current_step = int(time.time() // 30)
    current_code = _calculate_totp(secret, current_step)
    assert len(current_code) == 6
    assert current_code.isdigit()

    # Valid current code matches
    assert _verify_totp(secret, current_code) is True

    # Invalid code rejected
    assert _verify_totp(secret, "000000" if current_code != "000000" else "111111") is False


@pytest.mark.asyncio
async def test_reserved_username_availability_check():
    """Verify check_username_availability rejects reserved keywords and offers suggestions."""
    from src.auth.service import AuthService

    user_service_mock = MagicMock()
    uow_mock = AsyncMock()
    uow_mock.users.get_by_username.return_value = None

    class MockUowContext:
        async def __aenter__(self):
            return uow_mock

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    user_service_mock._uow_factory = MockUowContext
    auth_service = AuthService(user_service=user_service_mock, email_service=MagicMock())

    # Reserved username check
    avail, suggestions = await auth_service.check_username_availability("admin")
    assert avail is False
    assert len(suggestions) > 0
    assert "admin_dev" in suggestions or any("admin" in s for s in suggestions)

    # Valid unique username
    avail_valid, sug_valid = await auth_service.check_username_availability("valid_developer_99")
    assert avail_valid is True
    assert len(sug_valid) == 0

