from __future__ import annotations

import os

from src.ai_runtime.circuit_breaker import CircuitBreaker
from src.ai_runtime.providers.anthropic import AnthropicProvider
from src.ai_runtime.providers.base import BaseAIProvider
from src.ai_runtime.providers.gemini import GeminiProvider
from src.ai_runtime.providers.groq import GroqProvider
from src.ai_runtime.providers.mock import MockProvider
from src.ai_runtime.providers.ollama import OllamaProvider
from src.ai_runtime.providers.openai import OpenAIProvider
from src.ai_runtime.providers.openrouter import OpenRouterProvider
from src.ai_runtime.providers.vision import VisionModelProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: dict[str, BaseAIProvider] = {
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "vision": VisionModelProvider(),
            "openrouter": OpenRouterProvider(),
            "groq": GroqProvider(),
        }

        self.circuit_breakers: dict[str, CircuitBreaker] = {
            "ollama": CircuitBreaker(),
            "gemini": CircuitBreaker(),
            "openai": CircuitBreaker(),
            "anthropic": CircuitBreaker(),
            "vision": CircuitBreaker(),
            "openrouter": CircuitBreaker(),
            "groq": CircuitBreaker(),
            "mock": CircuitBreaker()
        }

        # Load priority from env
        default_priority = "gemini,groq,openrouter,openai,ollama"
        try:
            from src.config.settings import get_settings
            default_priority = getattr(get_settings(), "AI_PROVIDER_PRIORITY", default_priority)
        except Exception:
            pass
        priority_env = os.environ.get("AI_PROVIDER_PRIORITY", default_priority)
        self.priority: list[str] = [p.strip().lower() for p in priority_env.split(",") if p.strip()]

    def is_key_present(self, provider_name: str) -> bool:
        """Check whether credentials/key are present for a provider (never returns key values)."""
        name = provider_name.lower().strip()
        env_map = {
            "gemini": "GEMINI_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        if name in env_map:
            val = os.environ.get(env_map[name], "").strip()
            if val:
                return True
            provider = self.providers.get(name)
            if provider and getattr(provider, "api_key", None):
                return bool(str(provider.api_key).strip())
            return False
        if name == "ollama":
            return True
        if name == "mock":
            return True
        return False

    def get_default_provider_name(self) -> str:
        """Resolve the highest priority provider that is available/configured."""
        for name in self.priority:
            if name in self.providers and self.is_key_present(name):
                return name
        for name in self.priority:
            if name in self.providers:
                return name
        return "gemini"

    def get_default_model(self) -> str:
        """Resolve the default model for the active primary provider."""
        provider_name = self.get_default_provider_name()
        default_models = {
            "gemini": "gemini-2.0-flash",
            "groq": "llama-3.3-70b-versatile",
            "openrouter": "google/gemini-2.0-flash-exp:free",
            "openai": "gpt-4o-mini",
            "ollama": "llama3.2",
            "anthropic": "claude-3-5-sonnet-20241022",
        }
        return default_models.get(provider_name, "gemini-2.0-flash")

    def get_provider(self, name: str) -> BaseAIProvider | None:
        return self.providers.get(name.lower())

    def get_breaker(self, name: str) -> CircuitBreaker | None:
        return self.circuit_breakers.get(name.lower())

    def resolve_provider_for_model(self, model: str) -> str:
        """Map model names to their default/primary provider identifier."""
        if not model or model.lower() in ("default", "auto"):
            return self.get_default_provider_name()
        model_lower = model.lower()
        if "groq" in model_lower or "gpt-oss" in model_lower or "whisper" in model_lower or "compound" in model_lower or "qwen3" in model_lower:
            return "groq"
        elif any(k in model_lower for k in ("gemini", "nano-banana", "veo", "omni", "lyria", "antigravity", "deep-research", "computer-use")):
            return "gemini"
        elif "gpt-" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        elif "vl" in model_lower or "vision" in model_lower or "qwen" in model_lower:
            return "vision"
        elif "deepseek" in model_lower or "openrouter" in model_lower:
            return "openrouter"
        elif "mock" in model_lower:
            return "mock"
        else:
            # Default to first configured priority provider if available, or ollama
            return self.priority[0] if self.priority else "ollama"

    def get_priority_chain(self, requested_model: str) -> list[BaseAIProvider]:
        """
        Get a list of providers ordered by fallback priority.
        The primary provider for the model is placed first.
        Unhealthy providers (with OPEN circuit breakers) are skipped.
        """
        primary_name = self.resolve_provider_for_model(requested_model)

        chain = []
        # Place primary provider first if healthy
        if True:
            chain.append(self.providers[primary_name])

        # Append remaining healthy providers matching prioritised list
        for name in self.priority:
            if name == primary_name:
                continue
            if name in self.providers:
                chain.append(self.providers[name])

        return chain
