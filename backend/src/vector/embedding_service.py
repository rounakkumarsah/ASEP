"""
ASEP — Unified Vector Embedding Service
=======================================
Provides embeddings using local sentence-transformers by default,
or falls back/switches to external providers (openai, gemini) if explicitly configured.

Provider selected via env var EMBEDDING_PROVIDER, default = "local".
"""

from __future__ import annotations

import os
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

# Module-level cached models / clients
_MODEL: Any = None
_OPENAI_CLIENT: Any = None
_GEMINI_CLIENT: Any = None


def _get_configured_provider() -> str:
    """Return requested provider from environment, normalized."""
    return os.environ.get("EMBEDDING_PROVIDER", "local").strip().lower()


def get_provider() -> str:
    """
    Get active embedding provider.
    Returns 'local', 'openai', or 'gemini'.
    Falls back to 'local' if dependencies/keys for requested provider are missing.
    """
    req = _get_configured_provider()
    if req == "openai":
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        logger.warning(
            "embedding_provider_fallback",
            requested="openai",
            reason="OPENAI_API_KEY not set, falling back to local",
        )
        return "local"
    elif req == "gemini":
        if os.environ.get("GEMINI_API_KEY"):
            return "gemini"
        logger.warning(
            "embedding_provider_fallback",
            requested="gemini",
            reason="GEMINI_API_KEY not set, falling back to local",
        )
        return "local"
    return "local"


def get_dimension() -> int:
    """Return vector dimension for the active provider."""
    provider = get_provider()
    if provider == "openai":
        return 1536
    elif provider == "gemini":
        return 768
    return 384


def _get_local_model() -> Any:
    """Lazy-load and return the SentenceTransformer model."""
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
        except Exception as exc:
            logger.warning("local_embedding_load_failed", error=str(exc))
            raise RuntimeError(
                f"Failed to load local embedding model 'BAAI/bge-small-en-v1.5': {exc}"
            ) from exc
    return _MODEL


def _get_openai_client() -> Any:
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is None:
        try:
            from openai import OpenAI
            _OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except Exception as exc:
            logger.warning("embedding_provider_fallback", requested="openai", error=str(exc))
            raise RuntimeError(f"Failed to initialize OpenAI client: {exc}") from exc
    return _OPENAI_CLIENT


def _embed_local(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    if hasattr(embeddings, "tolist"):
        return embeddings.tolist()
    return [list(map(float, vec)) for vec in embeddings]


def _embed_openai(texts: list[str]) -> list[list[float]]:
    client = _get_openai_client()
    resp = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small",
    )
    return [d.embedding for d in resp.data]


def _embed_gemini(texts: list[str]) -> list[list[float]]:
    try:
        import google.generativeai as genai
    except ImportError:
        try:
            from google import genai
        except ImportError as exc:
            logger.warning("embedding_provider_fallback", requested="gemini", error=str(exc))
            raise RuntimeError("Gemini library not installed") from exc

    api_key = os.environ.get("GEMINI_API_KEY")
    if hasattr(genai, "configure"):
        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document",
        )
        if "embedding" in result:
            emb = result["embedding"]
            if emb and isinstance(emb[0], list):
                return emb
            return [emb]
        raise RuntimeError("Unexpected gemini embed_content response format")
    else:
        client = genai.Client(api_key=api_key)
        res = client.models.embed_content(
            model="text-embedding-004",
            contents=texts,
        )
        return [e.values for e in res.embeddings]


def get_embedding(text: str) -> list[float]:
    """Generate normalized embedding for a single string."""
    batch_res = get_embedding_batch([text])
    if not batch_res:
        raise RuntimeError("Embedding generation returned empty list")
    return batch_res[0]


def get_embedding_batch(texts: list[str]) -> list[list[float]]:
    """Generate normalized embeddings for a batch of strings."""
    if not texts:
        return []

    provider = get_provider()
    if provider == "openai":
        try:
            return _embed_openai(texts)
        except Exception as exc:
            logger.warning("embedding_provider_fallback", requested="openai", error=str(exc))
            return _embed_local(texts)
    elif provider == "gemini":
        try:
            return _embed_gemini(texts)
        except Exception as exc:
            logger.warning("embedding_provider_fallback", requested="gemini", error=str(exc))
            return _embed_local(texts)
    else:
        return _embed_local(texts)
