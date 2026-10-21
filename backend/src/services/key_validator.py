"""
ASEP — Provider Key Validation Service (BYOK)
==============================================
Validates LLM provider credentials against their lightweight auth verification endpoints.
"""

from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger(__name__)


async def validate_provider_key(provider: str, raw_key: str) -> tuple[bool, str | None]:
    """Validate a raw LLM API key against the provider's auth endpoint.

    Args:
        provider: Provider identifier ('groq', 'openai', 'openrouter', 'gemini', 'anthropic').
        raw_key: Plaintext API key to verify.

    Returns:
        tuple[bool, str | None]: (True, None) if key is valid; (False, reason) otherwise.
    """
    p = provider.lower().strip()
    k = raw_key.strip() if raw_key else ""

    if not k:
        logger.info("key_validation", provider=p, ok=False, reason="missing_key")
        return False, "missing_key"

    url: str
    headers: dict[str, str] = {}
    params: dict[str, str] = {}

    if p == "groq":
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {k}"}
    elif p == "openai":
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {k}"}
    elif p == "openrouter":
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {k}"}
    elif p == "gemini":
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        params = {"key": k}
    elif p == "anthropic":
        url = "https://api.anthropic.com/v1/models"
        headers = {
            "x-api-key": k,
            "anthropic-version": "2023-06-01",
        }
    else:
        logger.info("key_validation", provider=p, ok=False, reason="unsupported_provider")
        return False, "unsupported_provider"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)

        if 200 <= resp.status_code < 300:
            logger.info("key_validation", provider=p, ok=True, reason=None)
            return True, None
        elif resp.status_code == 401:
            logger.info("key_validation", provider=p, ok=False, reason="invalid_key")
            return False, "invalid_key"
        elif resp.status_code == 403:
            logger.info("key_validation", provider=p, ok=False, reason="forbidden")
            return False, "forbidden"
        else:
            reason = "invalid_key" if resp.status_code == 400 else f"http_{resp.status_code}"
            logger.info("key_validation", provider=p, ok=False, reason=reason)
            return False, reason

    except (httpx.TimeoutException, httpx.RequestError) as exc:
        logger.warning("key_validation", provider=p, ok=False, reason="network_error", error=str(exc))
        return False, "network_error"
    except Exception as exc:
        logger.error("key_validation", provider=p, ok=False, reason="network_error", error=str(exc))
        return False, "network_error"
