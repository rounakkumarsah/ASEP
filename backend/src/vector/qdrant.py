"""
ASEP — Qdrant Client Connection Pool
"""

import logging
from typing import AsyncGenerator

from qdrant_client import AsyncQdrantClient

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Qdrant AsyncClient instance
_qdrant_client: AsyncQdrantClient | None = None


from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
async def init_qdrant() -> None:
    """Initialise the global Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}")
        
        try:
            _qdrant_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            
            # Verify connectivity by getting cluster info or listing collections
            collections = await _qdrant_client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Found {len(collections.collections)} collections.")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            _qdrant_client = None
            raise


async def close_qdrant() -> None:
    """Close the global Qdrant client."""
    global _qdrant_client
    if _qdrant_client is not None:
        logger.info("Closing Qdrant client connection.")
        await _qdrant_client.close()
        _qdrant_client = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Get the global Qdrant client instance.
    
    Raises:
        RuntimeError: If Qdrant has not been initialized.
    """
    if _qdrant_client is None:
        raise RuntimeError("Qdrant client is not initialized. Call init_qdrant() first.")
    return _qdrant_client


async def qdrant_dependency() -> AsyncGenerator[AsyncQdrantClient, None]:
    """FastAPI dependency to inject the Qdrant client."""
    client = get_qdrant_client()
    yield client
