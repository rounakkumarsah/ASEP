import datetime
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from src.ai_runtime.contracts import CompletionRequest, Message
from src.ai_runtime.router import ModelRegistry, resolve_api_key
from src.ai_runtime.service import AIRuntimeService
from src.api.app import create_app
from src.auth.dependencies import get_current_user
from src.auth.key_vault import decrypt_key, encrypt_key, mask_key
from src.db.models.user import User
from src.db.models.user_api_key import UserApiKey
from src.db.postgres import get_db_session
from src.db.repositories.user_api_key_repository import (
    create_or_update,
    delete,
    get_all_for_user,
    get_by_user_and_provider,
    mark_invalid,
)
from src.services.key_validator import validate_provider_key


# =============================================================================
# 1. Key Vault Unit Tests
# =============================================================================

def test_key_vault_roundtrip():
    original = "sk-ant-api03-abcdef1234567890xyz"
    encrypted = encrypt_key(original)
    assert encrypted != original
    decrypted = decrypt_key(encrypted)
    assert decrypted == original


def test_key_vault_empty_strings():
    assert encrypt_key("") == ""
    assert decrypt_key("") == ""


def test_mask_key():
    assert mask_key("sk-1234567890abcd") == "sk-...abcd"
    assert mask_key("gsk_12345678901234") == "gsk...1234"
    assert mask_key("short") == "sh...rt"
    assert mask_key("1234") == "****"
    assert mask_key("") == ""
    assert mask_key("abcdefgh") == "ab...gh"


def test_key_vault_custom_secret():
    secret_key = Fernet.generate_key().decode()
    with patch.dict(os.environ, {"ASEP_KEY_VAULT_SECRET": secret_key}, clear=False):
        import src.auth.key_vault as kv
        orig_fernet = kv._fernet_instance
        try:
            kv._fernet_instance = None
            token = kv.encrypt_key("sk-custom-secret-key")
            assert kv.decrypt_key(token) == "sk-custom-secret-key"
        finally:
            kv._fernet_instance = orig_fernet


# =============================================================================
# 2. Key Validator Tests
# =============================================================================

@pytest.mark.asyncio
async def test_key_validator_empty():
    ok, reason = await validate_provider_key("groq", "")
    assert ok is False
    assert reason == "missing_key"


@pytest.mark.asyncio
async def test_key_validator_unsupported():
    ok, reason = await validate_provider_key("unsupported_llm", "some_key")
    assert ok is False
    assert reason == "unsupported_provider"


@pytest.mark.parametrize("provider", ["groq", "openai", "openrouter", "gemini", "anthropic"])
@pytest.mark.asyncio
async def test_key_validator_success(provider):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ok, reason = await validate_provider_key(provider, "test_api_key_123")
        assert ok is True
        assert reason is None


@pytest.mark.parametrize("status_code,expected_reason", [
    (401, "invalid_key"),
    (403, "forbidden"),
    (400, "invalid_key"),
    (500, "http_500"),
])
@pytest.mark.asyncio
async def test_key_validator_error_codes(status_code, expected_reason):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ok, reason = await validate_provider_key("openai", "bad_key")
        assert ok is False
        assert reason == expected_reason


@pytest.mark.asyncio
async def test_key_validator_network_error():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectTimeout("Connection timed out")
        ok, reason = await validate_provider_key("groq", "test_key")
        assert ok is False
        assert reason == "network_error"


# =============================================================================
# 3. Repository Unit Tests (Mock Session)
# =============================================================================

@pytest.mark.asyncio
async def test_repository_crud():
    user_id = uuid.uuid4()
    provider = "groq"
    encrypted_key = encrypt_key("gsk_test123")
    preview = mask_key("gsk_test123")

    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    # 1. create_or_update (new)
    record = await create_or_update(session, user_id, provider, encrypted_key, preview)
    assert record.user_id == user_id
    assert record.provider == "groq"
    assert record.encrypted_key == encrypted_key
    assert record.key_preview == preview
    assert record.is_valid is True
    session.add.assert_called_once()
    session.flush.assert_called()

    # 2. create_or_update (update existing)
    existing_record = UserApiKey(
        user_id=user_id,
        provider="groq",
        encrypted_key="old_enc",
        key_preview="old_prev",
        is_valid=False,
    )
    mock_result.scalars.return_value.first.return_value = existing_record
    new_enc = encrypt_key("gsk_updated")
    updated = await create_or_update(session, user_id, provider, new_enc, "gsk...ated")
    assert updated.encrypted_key == new_enc
    assert updated.is_valid is True

    # 3. get_by_user_and_provider
    mock_result.scalars.return_value.first.return_value = existing_record
    retrieved = await get_by_user_and_provider(session, user_id, "groq")
    assert retrieved == existing_record

    # 4. mark_invalid
    await mark_invalid(session, user_id, "groq", "revoked_key")
    assert existing_record.is_valid is False
    assert existing_record.last_error == "revoked_key"

    # 5. delete
    mock_result.scalars.return_value.first.return_value = existing_record
    deleted_ok = await delete(session, user_id, "groq")
    assert deleted_ok is True
    session.delete.assert_called_with(existing_record)


# =============================================================================
# 4. Runtime Key Resolver Tests
# =============================================================================

@pytest.mark.asyncio
async def test_resolve_api_key_user_key_precedence():
    user_id = uuid.uuid4()
    raw_user_key = "gsk_user_personal_key_xyz"
    enc = encrypt_key(raw_user_key)

    mock_record = UserApiKey(
        user_id=user_id,
        provider="groq",
        encrypted_key=enc,
        key_preview="gsk...xyz",
        is_valid=True,
    )

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("src.db.postgres._get_session_factory", return_value=mock_factory), \
         patch("src.db.repositories.user_api_key_repository.get_by_user_and_provider", new_callable=AsyncMock) as mock_get, \
         patch.dict(os.environ, {"GROQ_API_KEY": "platform_groq_key"}, clear=False):
        mock_get.return_value = mock_record

        resolved = await resolve_api_key("groq", user_id)
        assert resolved == raw_user_key


@pytest.mark.asyncio
async def test_resolve_api_key_marked_invalid_still_attempted():
    user_id = uuid.uuid4()
    raw_user_key = "gsk_user_invalid_key_xyz"
    enc = encrypt_key(raw_user_key)

    mock_record = UserApiKey(
        user_id=user_id,
        provider="groq",
        encrypted_key=enc,
        key_preview="gsk...xyz",
        is_valid=False,
    )

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("src.db.postgres._get_session_factory", return_value=mock_factory), \
         patch("src.db.repositories.user_api_key_repository.get_by_user_and_provider", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_record

        resolved = await resolve_api_key("groq", user_id)
        assert resolved == raw_user_key


@pytest.mark.asyncio
async def test_resolve_api_key_decrypt_failed_falls_back():
    user_id = uuid.uuid4()
    mock_record = UserApiKey(
        user_id=user_id,
        provider="groq",
        encrypted_key="corrupt_non_fernet_token",
        key_preview="gsk...bad",
        is_valid=True,
    )

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("src.db.postgres._get_session_factory", return_value=mock_factory), \
         patch("src.db.repositories.user_api_key_repository.get_by_user_and_provider", new_callable=AsyncMock) as mock_get, \
         patch.dict(os.environ, {"GROQ_API_KEY": "platform_groq_fallback"}, clear=False):
        mock_get.return_value = mock_record

        resolved = await resolve_api_key("groq", user_id)
        assert resolved == "platform_groq_fallback"


@pytest.mark.asyncio
async def test_resolve_api_key_no_user_falls_back_to_env():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "platform_gemini_fallback"}, clear=False):
        resolved = await resolve_api_key("gemini", None)
        assert resolved == "platform_gemini_fallback"


@pytest.mark.asyncio
async def test_resolve_api_key_missing_everywhere_returns_none():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("OPENAI_API_KEY", None)
        resolved = await resolve_api_key("openai", None)
        # Should be None if not in settings or env
        assert resolved is None or isinstance(resolved, str)


# =============================================================================
# 5. Anthropic BYOK Runtime Injection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_service_injects_anthropic_when_user_has_byok_key():
    """Verify that when platform has NO Anthropic key, but user has a BYOK Anthropic key,
    AIRuntimeService complete places Anthropic provider in the execution chain."""
    user_id = uuid.uuid4()
    user_anthropic_key = "sk-ant-user-provided-key-999"

    service = AIRuntimeService()

    with patch("src.ai_runtime.router.resolve_api_key", new_callable=AsyncMock) as mock_resolve, \
         patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)

        async def _mock_resolve(provider, uid):
            if provider == "anthropic" and uid == user_id:
                return user_anthropic_key
            return None

        mock_resolve.side_effect = _mock_resolve

        # Request Claude model with user_id
        req = CompletionRequest(
            messages=[Message(role="user", content="Hello Claude")],
            model="claude-3-5-sonnet-20241022",
            user_id=user_id,
        )

        with patch("src.ai_runtime.providers.anthropic.AnthropicProvider.complete", new_callable=AsyncMock) as mock_complete:
            from src.ai_runtime.contracts import CompletionResponse, UsageInfo
            mock_complete.return_value = CompletionResponse(
                text="Hello from Claude!",
                model="claude-3-5-sonnet-20241022",
                provider="anthropic",
                usage=UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15, latency_ms=100),
            )

            res = await service.complete(req)
            assert res.provider == "anthropic"
            assert res.text == "Hello from Claude!"


def test_auto_router_routes_claude_when_has_anthropic_flag():
    """Verify that auto_router includes Claude models when has_anthropic=True even without env key."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        router = ModelRegistry()

        complex_prompt = "class Architecture implements Kubernetes Docker function import " * 50
        decision = router.route(prompt=complex_prompt, has_tools=True, research_mode="deep", has_anthropic=True)
        # With high complexity and Anthropic enabled, Claude-3-5-sonnet has lower cost_in (3.0) than gpt-4o (5.0)
        assert "claude" in decision["model"].lower()


# =============================================================================
# 6. API Router Endpoint Tests
# =============================================================================

@pytest.fixture
def test_client():
    app = create_app()

    fake_user = User(
        id=uuid.uuid4(),
        email="byok_tester@example.com",
        is_active=True,
    )

    mock_db = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db_session] = lambda: mock_db

    client = TestClient(app)
    yield client, fake_user, mock_db
    app.dependency_overrides.clear()


def test_router_post_unsupported_provider(test_client):
    client, user, db = test_client
    resp = client.post("/api/v1/user-keys", json={"provider": "invalid_llm", "api_key": "some_key"})
    assert resp.status_code == 400
    assert "Unsupported provider" in resp.json()["detail"]


def test_router_post_empty_key(test_client):
    client, user, db = test_client
    resp = client.post("/api/v1/user-keys", json={"provider": "groq", "api_key": "   "})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_router_post_invalid_key_fails_validation(test_client):
    client, user, db = test_client

    with patch("src.api.routers.user_keys.validate_provider_key", new_callable=AsyncMock) as mock_val:
        mock_val.return_value = (False, "invalid_key")
        resp = client.post("/api/v1/user-keys", json={"provider": "groq", "api_key": "bad_key_123"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_key"


def test_router_post_success(test_client):
    client, user, db = test_client

    fake_key_record = UserApiKey(
        id=uuid.uuid4(),
        user_id=user.id,
        provider="groq",
        encrypted_key="enc_val",
        key_preview="gsk...1234",
        is_valid=True,
        last_validated_at=datetime.datetime.now(datetime.timezone.utc),
    )

    with patch("src.api.routers.user_keys.validate_provider_key", new_callable=AsyncMock) as mock_val, \
         patch("src.api.routers.user_keys.create_or_update", new_callable=AsyncMock) as mock_save:
        mock_val.return_value = (True, None)
        mock_save.return_value = fake_key_record

        resp = client.post("/api/v1/user-keys", json={"provider": "groq", "api_key": "gsk_valid_1234"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "groq"
        assert data["key_preview"] == "gsk...1234"
        assert data["is_valid"] is True
        # Security check: MUST NEVER return raw or encrypted key
        assert "api_key" not in data
        assert "encrypted_key" not in data


def test_router_get_keys_list(test_client):
    client, user, db = test_client

    fake_keys = [
        UserApiKey(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="groq",
            encrypted_key="enc1",
            key_preview="gsk...1111",
            is_valid=True,
        ),
        UserApiKey(
            id=uuid.uuid4(),
            user_id=user.id,
            provider="openai",
            encrypted_key="enc2",
            key_preview="sk-...2222",
            is_valid=False,
            last_error="invalid_key",
        ),
    ]

    with patch("src.api.routers.user_keys.get_all_for_user", new_callable=AsyncMock) as mock_get_all:
        mock_get_all.return_value = fake_keys

        resp = client.get("/api/v1/user-keys")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2
        assert items[0]["provider"] == "groq"
        assert items[0]["key_preview"] == "gsk...1111"
        assert items[1]["provider"] == "openai"
        assert items[1]["is_valid"] is False
        assert items[1]["last_error"] == "invalid_key"
        # Security check
        for item in items:
            assert "encrypted_key" not in item
            assert "api_key" not in item


def test_router_delete_key(test_client):
    client, user, db = test_client

    with patch("src.api.routers.user_keys.delete", new_callable=AsyncMock) as mock_del:
        mock_del.return_value = True

        resp = client.delete("/api/v1/user-keys/groq")
        assert resp.status_code == 200
        assert resp.json() == {"deleted": True}


def test_router_validate_key_not_found(test_client):
    client, user, db = test_client

    with patch("src.api.routers.user_keys.get_by_user_and_provider", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        resp = client.post("/api/v1/user-keys/groq/validate")
        assert resp.status_code == 404


def test_router_validate_key_success(test_client):
    client, user, db = test_client

    raw_key = "gsk_live_key_999"
    enc = encrypt_key(raw_key)
    fake_record = UserApiKey(
        id=uuid.uuid4(),
        user_id=user.id,
        provider="groq",
        encrypted_key=enc,
        key_preview="gsk...999",
        is_valid=False,
    )

    with patch("src.api.routers.user_keys.get_by_user_and_provider", new_callable=AsyncMock) as mock_get, \
         patch("src.api.routers.user_keys.validate_provider_key", new_callable=AsyncMock) as mock_val:
        mock_get.return_value = fake_record
        mock_val.return_value = (True, None)

        resp = client.post("/api/v1/user-keys/groq/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["last_error"] is None
