"""
ASEP — Embedding Provider Health Check
"""

import logging

from src.documents.embedding_service import OpenAICompatibleEmbeddingProvider

logger = logging.getLogger(__name__)


async def embedding_health_check() -> bool:
    """Perform a query against the embedding provider to verify health.
    
    Returns:
        True if the provider successfully generates a test embedding, False otherwise.
    """
    provider = None
    try:
        provider = OpenAICompatibleEmbeddingProvider(timeout=3.0)
        await provider.embed_query("ping")
        return True
    except Exception as e:
        logger.warning(f"Embedding provider health check failed: {e}")
        return False
    finally:
        if provider:
            await provider.close()
