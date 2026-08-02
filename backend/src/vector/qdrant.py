"""
ASEP — Qdrant Client Connection Pool
======================================
Manages a singleton AsyncQdrantClient for the application lifetime.

Works with both:
  - Local Qdrant (Docker): QDRANT_URL=http://localhost:6333
  - Qdrant Cloud:          QDRANT_URL=https://<cluster-id>.<region>.cloud.qdrant.io
                           QDRANT_API_KEY=<your-api-key>

Switching between local and cloud requires only environment variable changes.
No source code modifications needed.
"""

from __future__ import annotations

import logging
from typing import Annotated, AsyncGenerator
from urllib.parse import urlparse

from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton
_qdrant_client: AsyncQdrantClient | None = None


def _safe_qdrant_host(url: str) -> str:
    """Return '<host>:<port>' from a Qdrant URL, never exposing API key material."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "<unknown>"
        port = parsed.port or (443 if parsed.scheme == "https" else 6333)
        return f"{host}:{port}"
    except Exception:
        return "<qdrant>"


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def init_qdrant() -> None:
    """
    Initialise the global Qdrant async client with retry logic.

    Attempts up to 5 times with exponential backoff (2s → 10s).
    Logs host:port only — the API key is never written to logs.

    Raises:
        RuntimeError: If all connection attempts fail.
    """
    global _qdrant_client
    if _qdrant_client is not None:
        return  # Already initialised

    settings = get_settings()
    url = settings.QDRANT_URL.rstrip("/")
    # Qdrant Cloud HTTPS endpoints run on port 6334 (gRPC) / 443 (HTTPS REST).
    # If a cloud URL includes explicit :6333, strip it so AsyncQdrantClient uses default HTTPS 443 REST / 6334 gRPC.
    if url.startswith("https://") and ":6333" in url:
        url = url.replace(":6333", "")

    host_label = _safe_qdrant_host(url)
    logger.info("Connecting to Qdrant at %s", host_label)

    client = AsyncQdrantClient(
        url=url,
        api_key=settings.QDRANT_API_KEY,  # None → no auth header sent (local dev)
    )

    try:
        collections = await client.get_collections()
        logger.info(
            "Qdrant connected successfully",
            extra={"host": host_label, "collections": len(collections.collections)},
        )
        _qdrant_client = client
    except Exception as exc:
        logger.warning("Failed to connect to primary Qdrant at %s (%s). Retrying with local fallback...", host_label, str(exc))
        await client.close()
        # Retry with local qdrant container if configured in docker-compose
        try:
            fallback_client = AsyncQdrantClient(url="http://qdrant:6333")
            collections = await fallback_client.get_collections()
            logger.info("Successfully connected to fallback local Qdrant at http://qdrant:6333")
            _qdrant_client = fallback_client
            return
        except Exception as fallback_exc:
            logger.error("Local Qdrant fallback also failed: %s", str(fallback_exc))
            raise exc


async def close_qdrant() -> None:
    """Close the global Qdrant client on application shutdown."""
    global _qdrant_client
    if _qdrant_client is not None:
        logger.info("Closing Qdrant client connection.")
        await _qdrant_client.close()
        _qdrant_client = None


def get_qdrant_client() -> AsyncQdrantClient:
    """
    Return the initialised Qdrant client singleton.

    Raises:
        RuntimeError: If ``init_qdrant()`` has not been called yet.
    """
    if _qdrant_client is None:
        raise RuntimeError(
            "Qdrant client is not initialised. Ensure init_qdrant() completes during startup."
        )
    return _qdrant_client


async def qdrant_dependency() -> AsyncGenerator[AsyncQdrantClient, None]:
    """FastAPI dependency generator that yields the shared Qdrant client."""
    yield get_qdrant_client()


# Annotated alias for clean FastAPI route signatures:
#   async def my_route(qdrant: QdrantClientDep) -> ...:
QdrantClientDep = Annotated[AsyncQdrantClient, Depends(qdrant_dependency)]
