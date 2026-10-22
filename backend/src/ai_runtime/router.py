from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from uuid import UUID
import time
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self.models = {
            "gemini-1.5-flash": {
                "id": "gemini-1.5-flash",
                "tier": "cheap",
                "cost_in": 0.075,
                "cost_out": 0.30,
                "latency": 0.8,
                "context": 1048576,
            },
            "llama3-8b": {
                "id": "llama3-8b",
                "tier": "cheap",
                "cost_in": 0.05,
                "cost_out": 0.05,
                "latency": 0.5,
                "context": 8192,
            },
            "gpt-4o-mini": {
                "id": "gpt-4o-mini",
                "tier": "balanced",
                "cost_in": 0.15,
                "cost_out": 0.60,
                "latency": 1.2,
                "context": 128000,
            },
            "claude-3-5-sonnet-20240620": {
                "id": "claude-3-5-sonnet-20240620",
                "tier": "premium",
                "cost_in": 3.0,
                "cost_out": 15.0,
                "latency": 2.5,
                "context": 200000,
            },
            "gpt-4o": {
                "id": "gpt-4o",
                "tier": "premium",
                "cost_in": 5.0,
                "cost_out": 15.0,
                "latency": 2.2,
                "context": 128000,
            },
            "groq/llama-3.3-70b-versatile": {
                "id": "groq/llama-3.3-70b-versatile",
                "tier": "balanced",
                "cost_in": 0.59,
                "cost_out": 0.79,
                "latency": 1.0,
                "context": 128000,
            },
            "gemini-1.5-pro": {
                "id": "gemini-1.5-pro",
                "tier": "premium",
                "cost_in": 3.5,
                "cost_out": 10.5,
                "latency": 1.5,
                "context": 2097152,
            },
            "openrouter/meta-llama/llama-3.3-70b-instruct": {
                "id": "openrouter/meta-llama/llama-3.3-70b-instruct",
                "tier": "balanced",
                "cost_in": 0.40,
                "cost_out": 0.40,
                "latency": 1.2,
                "context": 128000,
            },
        }

        # Model rate limit states
        self.degraded_models = {} # model_id -> expiry_timestamp
        self.failure_counts = {}  # model_id -> consecutive_failures
        self.routing_logs = []

    def score_task(self, prompt: str, has_tools: bool, research_mode: str, phase: str | None = None) -> dict:
        """Estimate complexity from prompt length, code keywords, tools, mode, and phase."""
        score = 0
        
        # 1. Prompt length
        tok_estimate = len(prompt) // 4
        if tok_estimate > 2000:
            score += 3
        elif tok_estimate > 500:
            score += 1
            
        # 2. Code keywords or coding phase
        code_keywords = ["class ", "def ", "function", "import ", "extends ", "implements ", "architecture", "kubernetes", "docker"]
        is_code = (phase in ("implement", "coding", "code_generation")) or any(kw in prompt.lower() for kw in code_keywords)
        if is_code:
            score += 2
            
        # 3. Tool usage
        if has_tools:
            score += 2
            
        # 4. Research mode
        if research_mode == "deep":
            score += 4
        elif research_mode == "balanced":
            score += 1
            
        tier = "cheap"
        if score >= 6:
            tier = "premium"
        elif score >= 3:
            tier = "balanced"
            
        return {
            "score": score,
            "tier": tier,
            "tokens": tok_estimate,
            "is_code": is_code,
        }

    def route(self, prompt: str, has_tools: bool, research_mode: str, has_anthropic: bool | None = None, phase: str | None = None) -> dict:
        task_info = self.score_task(prompt, has_tools, research_mode, phase=phase)
        tier = task_info["tier"]
        tokens = task_info["tokens"]
        is_code = task_info.get("is_code", False) or (phase in ("implement", "coding", "code_generation"))
        
        # Clean up degraded models
        now = time.time()
        self.degraded_models = {k: v for k, v in self.degraded_models.items() if v > now}

        def _is_anthropic_available() -> bool:
            if has_anthropic is not None:
                return has_anthropic
            import os
            key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not key:
                try:
                    from src.config.settings import get_settings
                    key = (getattr(get_settings(), "ANTHROPIC_API_KEY", "") or "").strip()
                except Exception:
                    pass
            return bool(key)

        can_use_anthropic = _is_anthropic_available()

        # Filter available models
        available = [
            m for m in self.models.values()
            if m["id"] not in self.degraded_models
            and (can_use_anthropic or "claude" not in m["id"].lower())
        ]
        if not available:
            # If all degraded, fallback excluding claude if no key
            fallback = [m for m in self.models.values() if can_use_anthropic or "claude" not in m["id"].lower()]
            available = fallback if fallback else list(self.models.values())
            
        # 1. Filter by context window
        capable = [m for m in available if m["context"] >= tokens + 1000]
        if not capable:
            capable = available # fallback

        # CRITICAL (FIX 1): For code generation / implement phase, never default to 8b-instant models
        # (they lack the context window for multi-file generation).
        if is_code:
            non_8b = [m for m in capable if "8b" not in m["id"].lower()]
            if non_8b:
                capable = non_8b

        # 2. Filter by tier
        tier_order = {"cheap": 1, "balanced": 2, "premium": 3}
        target_val = tier_order[tier]
        
        tier_models = [m for m in capable if tier_order[m["tier"]] >= target_val]
        if not tier_models:
            tier_models = capable
            
        # 3. For code generation / implement phase, prefer groq/llama-3.3-70b-versatile or gemini-1.5-pro
        if is_code and any(m["id"] == "groq/llama-3.3-70b-versatile" for m in tier_models):
            pref_70b = next((m for m in tier_models if m["id"] == "groq/llama-3.3-70b-versatile"), None)
            if pref_70b and tier != "premium":
                selected = pref_70b
            else:
                tier_models.sort(key=lambda x: x["cost_in"])
                selected = tier_models[0]
        else:
            tier_models.sort(key=lambda x: x["cost_in"])
            selected = tier_models[0]
        
        reason = f"chose {selected['id']}: complexity {task_info['score']} ({tier}), {tokens} tokens"
        
        try:
            from src.utils.metrics import metrics_store
            metrics_store.record_auto_router_decision(selected['id'])
        except Exception:
            pass
            
        return {
            "model": selected["id"],
            "reason": reason,
            "task_info": task_info
        }

    def get_model_for_phase(self, phase: str = "implement") -> str:
        return get_model_for_phase(phase)

    def record_failure(self, model_id: str, is_429: bool = True):
        if not is_429:
            return False
        self.failure_counts[model_id] = self.failure_counts.get(model_id, 0) + 1
        if self.failure_counts[model_id] >= 3:
            logger.warning(f"Circuit breaker tripped for {model_id}. Degraded for 5 minutes.")
            self.degraded_models[model_id] = time.time() + 300 # 5 mins
            self.failure_counts[model_id] = 0
            return True # Tripped
        return False
        
    def record_success(self, model_id: str):
        self.failure_counts[model_id] = 0

# Preferred models by execution phase (FIX 1)
PHASE_PREFERRED_MODELS: dict[str, str] = {
    "implement": "groq/llama-3.3-70b-versatile",
    "coding": "groq/llama-3.3-70b-versatile",
    "code_generation": "groq/llama-3.3-70b-versatile",
}

PHASE_FALLBACK_MODELS: dict[str, list[str]] = {
    "implement": ["gemini-1.5-pro", "openrouter/meta-llama/llama-3.3-70b-instruct"],
    "coding": ["gemini-1.5-pro", "openrouter/meta-llama/llama-3.3-70b-instruct"],
    "code_generation": ["gemini-1.5-pro", "openrouter/meta-llama/llama-3.3-70b-instruct"],
}


def get_model_for_phase(phase: str = "implement") -> str:
    """Select preferred model for a given execution phase.

    For 'implement' or 'coding' (code generation), returns a large-context model:
    Primary: groq/llama-3.3-70b-versatile
    Fallback: gemini-1.5-pro or openrouter/meta-llama/llama-3.3-70b-instruct
    Never defaults to llama-3.1-8b-instant for code generation.
    """
    phase_clean = (phase or "").lower().strip()
    return PHASE_PREFERRED_MODELS.get(phase_clean, "groq/llama-3.3-70b-versatile")


auto_router = ModelRegistry()


async def resolve_api_key(provider: str, user_id: UUID | str | None = None) -> str | None:
    """Resolve active API key for a provider.

    1. If user_id given, try user's own key from DB (decrypt it).
    2. If not found or decrypt fails, fall back to platform env key via existing settings lookup.
    3. If user's key exists but is marked invalid, still attempt it (user may have fixed it) but log a warning.
    4. Return None only if neither exists.
    """
    import os
    import uuid as _uuid
    import structlog

    slog = structlog.get_logger(__name__)
    p = provider.lower().strip()

    # 1. If user_id given, try user's own key from DB
    if user_id is not None:
        try:
            parsed_uid = user_id if isinstance(user_id, _uuid.UUID) else _uuid.UUID(str(user_id))
            from src.db.postgres import _get_session_factory
            from src.db.repositories.user_api_key_repository import get_by_user_and_provider
            from src.auth.key_vault import decrypt_key

            factory = _get_session_factory()
            async with factory() as session:
                key_record = await get_by_user_and_provider(session, parsed_uid, p)
                if key_record is not None and key_record.encrypted_key:
                    if not key_record.is_valid:
                        slog.warning(
                            "user_api_key_marked_invalid_attempting",
                            provider=p,
                            user_id=str(parsed_uid),
                        )
                    try:
                        decrypted = decrypt_key(key_record.encrypted_key)
                        if decrypted and decrypted.strip():
                            return decrypted.strip()
                    except Exception as exc:
                        slog.warning(
                            "user_api_key_decrypt_failed",
                            provider=p,
                            user_id=str(parsed_uid),
                            error=str(exc),
                        )
        except Exception as exc:
            slog.warning(
                "user_api_key_lookup_error",
                provider=p,
                user_id=str(user_id),
                error=str(exc),
            )

    # 2. Fall back to platform env key via existing settings lookup
    env_keys = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_var_name = env_keys.get(p)
    if env_var_name:
        val_os = os.environ.get(env_var_name, "").strip()
        if val_os:
            return val_os

        try:
            from src.config.settings import get_settings
            val = getattr(get_settings(), env_var_name, None)
            if val and str(val).strip():
                return str(val).strip()
        except Exception:
            pass

    return None


def map_failover_model(
    model: str,
    target_provider: str,
    source_provider: str | None = None,
) -> str:
    """Map model name to a valid model for the target provider during failover.

    Ensures that provider-specific model names (e.g. 'groq/llama-3.1-8b-instant'
    or 'llama-3.1-8b-instant') are not passed to fallback providers such as
    Gemini or OpenRouter, which would reject them with 404/400 errors.
    """
    target = target_provider.lower().strip()
    model_lower = (model or "").lower().strip()

    if target == "gemini":
        # Target Gemini failover models MUST be exactly one of:
        # - gemini-2.0-flash
        # - gemini-1.5-flash
        # - gemini-1.5-pro
        # Hallucinated models (such as "gemini-3.6-flash") or foreign models are never passed through.
        clean = (model.split("/")[-1] if "/" in model else model).lower().strip()
        if "1.5-pro" in clean:
            return "gemini-1.5-pro"
        if "1.5-flash" in clean:
            return "gemini-1.5-flash"
        if "2.0-flash" in clean:
            return "gemini-2.0-flash"
        # Safe default for any other model (e.g. hallucinated "gemini-3.6-flash", groq/llama, etc.)
        return "gemini-2.0-flash"

    if target == "openrouter":
        clean_model = model
        if model_lower.startswith("openrouter/"):
            clean_model = model[len("openrouter/"):]
            model_lower = clean_model.lower().strip()
        # Map to anthropic/claude-3.5-sonnet if Claude/Anthropic is requested
        if any(c in model_lower for c in ("claude", "anthropic", "sonnet")):
            return "anthropic/claude-3.5-sonnet"
        if "deepseek" in model_lower:
            return "deepseek/deepseek-r1"
        if "70b" in model_lower or "llama-3.3" in model_lower:
            return "meta-llama/llama-3.3-70b-instruct"
        # Default fallback for OpenRouter
        return "meta-llama/llama-3.1-8b-instruct"

    if target == "groq":
        if model_lower.startswith("groq/"):
            remainder = model[len("groq/"):]
            if remainder.startswith("gpt-oss"):
                return f"openai/{remainder}"
            if remainder.startswith("qwen3"):
                return f"qwen/{remainder}"
            return remainder
        if "deepseek" in model_lower:
            return "deepseek-r1-distill-llama-70b"
        if "70b" in model_lower or "llama-3.3" in model_lower:
            return "llama-3.3-70b-versatile"
        if "8b" in model_lower or "llama-3.1" in model_lower:
            return "llama-3.1-8b-instant"
        if model_lower.startswith("meta-llama/"):
            return "llama-3.3-70b-versatile"
        if any(k in model_lower for k in ("llama-", "gpt-oss", "qwen", "compound", "whisper")):
            return model
        return "llama-3.3-70b-versatile"

    if target == "openai":
        if model_lower.startswith("openai/"):
            return model[len("openai/"):]
        if model_lower.startswith("gpt-") or model_lower.startswith("o1") or model_lower.startswith("o3"):
            return model
        return "gpt-4o-mini"

    if target == "anthropic":
        if model_lower.startswith("anthropic/"):
            remainder = model[len("anthropic/"):]
            if "claude" in remainder.lower():
                return remainder
        if "claude" in model_lower:
            return model
        return "claude-3-5-sonnet-20241022"

    if target == "ollama":
        if model_lower in ("llama3.2", "llama3.1", "llama3", "mistral"):
            return model
        return "llama3.2"

    return model

