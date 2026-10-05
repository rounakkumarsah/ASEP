import os
import pytest
from unittest.mock import patch

from src.ai_runtime.providers.anthropic import AnthropicProvider
from src.ai_runtime.registry import ProviderRegistry
from src.ai_runtime.router import ModelRegistry
from src.config.settings import Settings


@pytest.mark.asyncio
async def test_anthropic_provider_gracefully_disabled_without_key():
    """Verify AnthropicProvider initializes cleanly without key and reports disabled status without error count."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        provider = AnthropicProvider(api_key="")

        assert provider.name == "anthropic"
        assert not provider.api_key

        health = await provider.check_health()
        assert health.is_healthy is False
        assert health.error_count == 0
        assert health.last_error is None
        assert health.active_model == "none"


@pytest.mark.asyncio
async def test_anthropic_provider_complete_raises_descriptive_error_when_disabled():
    """Verify AnthropicProvider complete call raises clean ValueError when no key is set."""
    from src.ai_runtime.contracts import CompletionRequest, Message

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        provider = AnthropicProvider(api_key="")

        request = CompletionRequest(
            messages=[Message(role="user", content="Hi")],
            model="claude-3-5-sonnet-20241022"
        )
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            await provider.complete(request)


def test_registry_key_presence_and_default_provider_without_anthropic():
    """Verify ProviderRegistry never selects Anthropic as default when ANTHROPIC_API_KEY is not set."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        assert registry.is_key_present("anthropic") is False
        default_provider = registry.get_default_provider_name()
        assert default_provider != "anthropic"


def test_registry_default_provider_ignores_anthropic_in_priority():
    """Verify that even if AI_PROVIDER_PRIORITY includes anthropic first, it is skipped when key is missing."""
    with patch.dict(os.environ, {"AI_PROVIDER_PRIORITY": "anthropic,gemini,groq"}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        assert registry.get_default_provider_name() != "anthropic"
        # Second loop fallback should also skip anthropic
        registry.priority = ["anthropic"]
        assert registry.get_default_provider_name() == "gemini"


def test_registry_resolve_provider_for_model_falls_back_when_no_anthropic_key():
    """Verify resolve_provider_for_model falls back to default provider when claude is requested without key."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        resolved = registry.resolve_provider_for_model("claude-3-5-sonnet")
        assert resolved != "anthropic"
        assert resolved == registry.get_default_provider_name()


def test_registry_resolve_provider_for_model_resolves_anthropic_when_key_present():
    """Verify resolve_provider_for_model resolves to anthropic when key is present."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}, clear=False):
        registry = ProviderRegistry()
        resolved = registry.resolve_provider_for_model("claude-3-5-sonnet")
        assert resolved == "anthropic"


def test_registry_priority_chain_excludes_anthropic_when_no_key():
    """Verify get_priority_chain never includes AnthropicProvider when ANTHROPIC_API_KEY is absent."""
    with patch.dict(os.environ, {"AI_PROVIDER_PRIORITY": "anthropic,gemini,groq"}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        chain = registry.get_priority_chain("claude-3-5-sonnet")
        provider_names = [p.name for p in chain]
        assert "anthropic" not in provider_names

        default_chain = registry.get_priority_chain("default")
        default_names = [p.name for p in default_chain]
        assert "anthropic" not in default_names


def test_auto_router_excludes_claude_when_no_anthropic_key():
    """Verify ModelRegistry / auto_router never routes to Claude when ANTHROPIC_API_KEY is absent."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        router = ModelRegistry()

        # High complexity prompt that would normally route to premium tier (claude or gpt-4o)
        complex_prompt = "class Architecture implements Kubernetes Docker function import " * 50
        decision = router.route(prompt=complex_prompt, has_tools=True, research_mode="deep")

        assert "claude" not in decision["model"].lower()


def test_settings_production_validation_succeeds_without_anthropic_key():
    """Verify Settings initializes and passes production validator without ANTHROPIC_API_KEY."""
    with patch.dict(os.environ, {"APP_ENV": "production", "DATABASE_URL": "postgresql+asyncpg://asep:secret@neon.tech/asep", "REDIS_URL": "rediss://production-redis:6379", "SECRET_KEY": "a" * 64}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://asep:secret@neon.tech/asep",
            REDIS_URL="rediss://production-redis:6379",
            SECRET_KEY="a" * 64,
            APP_ENV="production"
        )
        assert settings.ANTHROPIC_API_KEY is None


def test_anthropic_provider_explicit_empty_key_overrides_env():
    """Verify AnthropicProvider explicitly passed api_key="" disables the provider even if env has a key."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-some-key"}, clear=False):
        provider = AnthropicProvider(api_key="")
        assert provider.api_key == ""
        assert not provider.api_key


def test_registry_resolves_anthropic_prefix_to_default_without_key():
    """Verify resolve_provider_for_model handles 'anthropic' and 'anthropic/...' model names safely."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        assert registry.resolve_provider_for_model("anthropic") == registry.get_default_provider_name()
        assert registry.resolve_provider_for_model("anthropic/claude-3-5-sonnet") == registry.get_default_provider_name()


def test_free_providers_safely_translate_claude_models():
    """Verify Gemini and Groq providers safely translate Claude models rather than failing with invalid model errors."""
    from src.ai_runtime.providers.gemini import GeminiProvider
    from src.ai_runtime.providers.groq import GroqProvider

    assert GeminiProvider._resolve_model("claude-3-5-sonnet-20241022") == "gemini-3.6-flash"
    assert GeminiProvider._resolve_model("anthropic/claude-3-5-sonnet") == "gemini-3.6-flash"

    assert GroqProvider._resolve_model("claude-3-5-sonnet-20241022") == "llama-3.3-70b-versatile"
    assert GroqProvider._resolve_model("anthropic/claude-3-5-sonnet") == "llama-3.3-70b-versatile"


def test_registry_priority_chain_only_anthropic_configured_graceful_fallback():
    """Verify that when AI_PROVIDER_PRIORITY contains only 'anthropic', chain still falls back safely."""
    with patch.dict(os.environ, {"AI_PROVIDER_PRIORITY": "anthropic"}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        registry = ProviderRegistry()

        chain = registry.get_priority_chain("default")
        provider_names = [p.name for p in chain]
        assert "anthropic" not in provider_names
        assert len(chain) > 0
        assert chain[0].name == "gemini"

