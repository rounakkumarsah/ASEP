"""
ASEP — Neo4j Driver Connection Pool
===================================
Manages a singleton Async Driver instance for the application lifetime.

Supports both:
  - Local Neo4j (Docker/bolt): NEO4J_URI=bolt://localhost:7687
  - Neo4j Aura (Cloud/neo4j+s): NEO4J_URI=neo4j+s://<db-id>.databases.neo4j.io
                                NEO4J_USER=<username>
                                NEO4J_PASSWORD=<password>

Credentials and URLs are read exclusively from settings/environment.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated, Any
from urllib.parse import urlparse

from fastapi import Depends
from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    pass

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton (typed as Any to avoid eager neo4j import)
_neo4j_driver: Any = None


def _safe_neo4j_host(url: str) -> str:
    """Return '<scheme>://<host>:<port>' from a Neo4j URI, hiding any user credentials."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "<unknown>"
        port = parsed.port or (7687 if "bolt" in parsed.scheme else 443)
        return f"{parsed.scheme}://{host}:{port}"
    except Exception:
        return "<neo4j>"


import os


@retry(
    stop=stop_after_attempt(1 if (os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV")) else 2),
    wait=wait_exponential(multiplier=1, min=1, max=2),
    reraise=True,
)
async def init_neo4j() -> None:
    """
    Initialise the global Neo4j driver connection pool with retry logic.

    Attempts up to 5 times with exponential backoff (2s → 10s).
    Logs masked host/scheme details only.
    """
    global _neo4j_driver
    if _neo4j_driver is not None:
        return  # Already initialised

    settings = get_settings()
    host_label = _safe_neo4j_host(settings.NEO4J_URI)
    logger.info("Connecting to Neo4j at %s", host_label)

    try:
        # Lazy import — neo4j is an optional heavy dependency
        from neo4j import AsyncGraphDatabase  # noqa: PLC0415

        # AsyncGraphDatabase.driver is thread-safe and acts as a connection pool
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        await driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j at %s", host_label)
        _neo4j_driver = driver
    except Exception as exc:
        logger.error("Failed to connect to Neo4j at %s: %s", host_label, str(exc))
        raise


async def close_neo4j() -> None:
    """Close the global Neo4j driver pool on application shutdown."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        logger.info("Closing Neo4j connection pool.")
        await _neo4j_driver.close()
        _neo4j_driver = None


def get_neo4j_driver() -> Any:
    """
    Return the active Neo4j driver singleton.

    Raises:
        RuntimeError: If ``init_neo4j()`` has not been called or failed.
    """
    if _neo4j_driver is None:
        raise RuntimeError(
            "Neo4j driver is not initialised. Ensure init_neo4j() completes during startup."
        )
    return _neo4j_driver


async def neo4j_driver_dependency() -> AsyncGenerator[Any, None]:
    """FastAPI dependency to inject the Neo4j driver."""
    yield get_neo4j_driver()


# Annotated alias for clean FastAPI dependency injection:
#   async def my_route(driver: Neo4jDriverDep) -> ...:
Neo4jDriverDep = Annotated[Any, Depends(neo4j_driver_dependency)]
