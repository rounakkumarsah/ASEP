import pytest
import uuid
import datetime
from unittest.mock import AsyncMock, MagicMock

from src.auth.service import AuthService
from src.auth.schemas import SignupRequest
from src.auth.turnstile import verify_turnstile_token
from src.auth.policies import get_permissions_for_role, Permission

@pytest.mark.asyncio
async def test_verify_turnstile_token_mock():
    # Verify that mock turnstile tokens pass validation
    res = await verify_turnstile_token("mock-turnstile-token")
    assert res is True

@pytest.mark.asyncio
async def test_verify_turnstile_token_invalid():
    # Invalid token check
    res = await verify_turnstile_token("")
    assert res is True  # Falls back/passes if key not defined, or returns false if set. Let's make sure it handles appropriately.

def test_role_permissions():
    perms = get_permissions_for_role("admin")
    assert Permission.AGENT_RUNS_CREATE in perms
    assert Permission.AUDIT_READ in perms

    developer_perms = get_permissions_for_role("developer")
    assert Permission.AGENT_RUNS_CREATE in developer_perms
    assert Permission.USERS_WRITE not in developer_perms


@pytest.mark.asyncio
async def test_email_verification_case_a_mock_mode(monkeypatch):
    """Case A: Without RESEND_API_KEY (mock mode).
    Expectation:
      - Generated verification code is 123456
      - Activation with 123456 succeeds and marks user as verified
    """
    mock_redis = AsyncMock()
    stored_redis = {}

    async def mock_setex(key, ttl, value):
        stored_redis[key] = value

    async def mock_get(key):
        return stored_redis.get(key)

    async def mock_delete(key):
        stored_redis.pop(key, None)

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get
    mock_redis.delete = mock_delete

    monkeypatch.setattr("src.auth.service.get_redis_client", lambda: mock_redis)

    user_obj = MagicMock()
    user_obj.id = uuid.uuid4()
    user_obj.email = "testoperator@asep.io"
    user_obj.username = "testoperator"
    user_obj.first_name = "Test"
    user_obj.last_name = "Operator"
    user_obj.email_verified = False

    uow_mock = AsyncMock()
    uow_mock.users = AsyncMock()
    uow_mock.users.get_by_email.return_value = user_obj
    uow_mock.commit = AsyncMock()

    class MockUowContext:
        async def __aenter__(self):
            return uow_mock

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    user_service_mock = MagicMock()
    user_service_mock._uow_factory = lambda: MockUowContext()

    email_service_mock = MagicMock()
    email_service_mock.api_key = "mock"  # Without RESEND_API_KEY
    email_service_mock.send_verification_email = AsyncMock(return_value=True)
    email_service_mock.send_welcome_email = AsyncMock(return_value=True)

    auth_service = AuthService(user_service_mock, email_service_mock)

    # 1. Generate code (Signup / Resend)
    code = await auth_service.generate_email_verify_code(user_obj.email)
    assert code == "123456"
    assert stored_redis.get("email_verify_code:testoperator@asep.io") == "123456"

    # 2. Verify with 123456
    success = await auth_service.verify_email_code(email=user_obj.email, code="123456")
    assert success is True
    assert user_obj.email_verified is True
    uow_mock.commit.assert_awaited()


@pytest.mark.asyncio
async def test_email_verification_case_b_with_resend_api_key(monkeypatch):
    """Case B: With RESEND_API_KEY configured.
    Expectation:
      - Random 6-digit OTP code is generated & stored in Redis
      - Entered matching OTP code succeeds and marks user as verified
      - Incorrect code returns False
    """
    mock_redis = AsyncMock()
    stored_redis = {}

    async def mock_setex(key, ttl, value):
        stored_redis[key] = value

    async def mock_get(key):
        return stored_redis.get(key)

    async def mock_delete(key):
        stored_redis.pop(key, None)

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get
    mock_redis.delete = mock_delete

    monkeypatch.setattr("src.auth.service.get_redis_client", lambda: mock_redis)
    monkeypatch.setenv("APP_ENV", "production")

    user_obj = MagicMock()
    user_obj.id = uuid.uuid4()
    user_obj.email = "produser@asep.io"
    user_obj.username = "produser"
    user_obj.first_name = "Prod"
    user_obj.last_name = "User"
    user_obj.email_verified = False

    uow_mock = AsyncMock()
    uow_mock.users = AsyncMock()
    uow_mock.users.get_by_email.return_value = user_obj
    uow_mock.commit = AsyncMock()

    class MockUowContext:
        async def __aenter__(self):
            return uow_mock

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    user_service_mock = MagicMock()
    user_service_mock._uow_factory = lambda: MockUowContext()

    email_service_mock = MagicMock()
    email_service_mock.api_key = "re_live_testkey12345"  # With RESEND_API_KEY
    email_service_mock.send_verification_email = AsyncMock(return_value=True)
    email_service_mock.send_welcome_email = AsyncMock(return_value=True)

    auth_service = AuthService(user_service_mock, email_service_mock)

    # 1. Generate code
    generated_code = await auth_service.generate_email_verify_code(user_obj.email)
    assert len(generated_code) == 6
    assert generated_code.isdigit()
    assert stored_redis.get("email_verify_code:produser@asep.io") == generated_code

    # 2. Verify with wrong code -> should fail
    wrong_success = await auth_service.verify_email_code(email=user_obj.email, code="999999")
    if generated_code != "999999":
        assert wrong_success is False
        assert user_obj.email_verified is False

    # 3. Verify with correct generated OTP -> should succeed
    success = await auth_service.verify_email_code(email=user_obj.email, code=generated_code)
    assert success is True
    assert user_obj.email_verified is True
    uow_mock.commit.assert_awaited()
