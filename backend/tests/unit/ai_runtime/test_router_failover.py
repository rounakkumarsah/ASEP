"""
Tests for map_failover_model in src.ai_runtime.router.

FIX 2 — Gemini failover model must never be a hallucinated / non-existent name.
FIX 1 — Groq prefix must be stripped before being passed to provider payload.
"""
import pytest
from src.ai_runtime.router import map_failover_model


# ---------------------------------------------------------------------------
# Gemini failover — allowlist enforcement
# ---------------------------------------------------------------------------

class TestMapFailoverModelGemini:
    """gemini-3.6-flash is NOT a real model; the fix must reject it."""

    def test_hallucinated_gemini_model_replaced(self):
        result = map_failover_model("gemini-3.6-flash", "gemini")
        assert result == "gemini-2.0-flash", (
            f"Hallucinated model 'gemini-3.6-flash' should map to 'gemini-2.0-flash', got '{result}'"
        )

    def test_another_hallucinated_name_replaced(self):
        result = map_failover_model("gemini-99-ultra", "gemini")
        assert result == "gemini-2.0-flash"

    def test_valid_gemini_2_0_flash_preserved(self):
        assert map_failover_model("gemini-2.0-flash", "gemini") == "gemini-2.0-flash"

    def test_valid_gemini_1_5_flash_preserved(self):
        assert map_failover_model("gemini-1.5-flash", "gemini") == "gemini-1.5-flash"

    def test_valid_gemini_1_5_pro_preserved(self):
        assert map_failover_model("gemini-1.5-pro", "gemini") == "gemini-1.5-pro"

    def test_non_gemini_model_maps_to_default(self):
        """A Groq model name passed to Gemini failover must map to gemini-2.0-flash."""
        result = map_failover_model("llama-3.1-8b-instant", "gemini")
        assert result == "gemini-2.0-flash"

    def test_groq_prefixed_model_maps_to_default(self):
        result = map_failover_model("groq/llama-3.1-8b-instant", "gemini")
        assert result == "gemini-2.0-flash"

    def test_valid_model_with_google_prefix(self):
        """'google/gemini-2.0-flash' should resolve to 'gemini-2.0-flash'."""
        result = map_failover_model("google/gemini-2.0-flash", "gemini")
        assert result == "gemini-2.0-flash"

    def test_alias_deep_research_preserved(self):
        result = map_failover_model("deep-research", "gemini")
        assert result == "deep-research"


# ---------------------------------------------------------------------------
# OpenRouter failover
# ---------------------------------------------------------------------------

class TestMapFailoverModelOpenRouter:
    def test_llama_8b_mapped(self):
        result = map_failover_model("llama-3.1-8b-instant", "openrouter")
        assert result == "meta-llama/llama-3.1-8b-instruct"

    def test_groq_llama_remapped_for_openrouter(self):
        result = map_failover_model("groq/llama-3.1-8b-instant", "openrouter")
        # groq/ prefix is excluded from slash-based pass-through
        assert result == "meta-llama/llama-3.1-8b-instruct"

    def test_deepseek_mapped(self):
        result = map_failover_model("deepseek-r1", "openrouter")
        assert result == "deepseek/deepseek-r1"

    def test_70b_mapped(self):
        result = map_failover_model("llama-3.3-70b-versatile", "openrouter")
        assert result == "meta-llama/llama-3.3-70b-instruct"


# ---------------------------------------------------------------------------
# Groq failover — prefix stripping in map_failover_model
# ---------------------------------------------------------------------------

class TestMapFailoverModelGroq:
    def test_groq_prefix_stripped(self):
        result = map_failover_model("groq/llama-3.1-8b-instant", "groq")
        assert result == "llama-3.1-8b-instant"
        assert not result.startswith("groq/"), f"groq/ prefix not stripped: {result!r}"

    def test_groq_plain_8b_resolved(self):
        result = map_failover_model("llama-3.1-8b-instant", "groq")
        assert result == "llama-3.1-8b-instant"

    def test_groq_70b_resolved(self):
        result = map_failover_model("llama-3.3-70b-versatile", "groq")
        assert result == "llama-3.3-70b-versatile"
