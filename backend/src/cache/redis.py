"""
ASEP — Redis Client & Connection Pool
"""

import asyncio
import logging
from typing import AsyncGenerator
from urllib.parse import urlparse

from redis.asyncio import Redis, from_url

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Redis instance
_redis_client: Redis | None = None


def _safe_redis_host(url: str) -> str:
    """Return '<host>:<port>' from a Redis URL, never exposing credentials."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "<unknown>"
        port = parsed.port or 6379
        return f"{host}:{port}"
    except Exception:
        return "<redis>"


async def init_redis() -> None:
    """Initialise the global Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        logger.info("Connecting to Redis at %s", _safe_redis_host(settings.REDIS_URL))
        
        # 'decode_responses=True' parses strings directly instead of returning bytes.
        # This is generally more convenient for standard caching.
        kwargs = {
            "encoding": "utf-8",
            "decode_responses": True,
            "health_check_interval": 30,
            "socket_timeout": 2.0,
            "socket_connect_timeout": 2.0,
        }
        if settings.REDIS_URL.startswith("rediss://"):
            import ssl
            kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

        _redis_client = from_url(settings.REDIS_URL, **kwargs)
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            # Fallback for plain redis connection if TLS fails on cloud proxy
            if settings.REDIS_URL.startswith("rediss://"):
                plain_url = settings.REDIS_URL.replace("rediss://", "redis://", 1)
                logger.warning("Retrying Redis connection over plain TCP: %s", _safe_redis_host(plain_url))
                try:
                    _redis_client = from_url(plain_url, encoding="utf-8", decode_responses=True, health_check_interval=30)
                    await _redis_client.ping()
                    logger.info("Successfully connected to Redis over plain TCP.")
                    return
                except Exception as inner_e:
                    logger.error("Failed to connect to Redis over plain TCP: %s", inner_e)

            # Try local Docker compose redis container as final fallback
            try:
                logger.warning("Connecting to fallback local container Redis at redis://redis:6379...")
                _redis_client = from_url("redis://redis:6379", encoding="utf-8", decode_responses=True, health_check_interval=30)
                await _redis_client.ping()
                logger.info("Successfully connected to local container Redis.")
                return
            except Exception as local_e:
                logger.warning(
                    "Redis is unavailable at startup. "
                    "The application will start in degraded mode — rate-limiting, "
                    "blacklisting, and session tokens will fail until Redis becomes reachable."
                )
                _redis_client = None


async def close_redis() -> None:
    """Close the global Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        logger.info("Closing Redis connection pool.")
        await _redis_client.close()
        _redis_client = None


def get_redis_client() -> Redis:
    """Get the global Redis client instance.
    
    Raises:
        RuntimeError: If Redis has not been initialized.
    """
    if _redis_client is None:
        raise RuntimeError("Redis client is not initialized. Call init_redis() first.")
    return _redis_client


async def redis_dependency() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency to inject the Redis client."""
    client = get_redis_client()
    yield client
