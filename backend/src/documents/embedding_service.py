"""
ASEP — Provider-Agnostic Embedding Service
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of document texts."""
        pass


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that communicates with any OpenAI-compatible API (e.g. Ollama, LocalAI, OpenAI)."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0
    ) -> None:
        settings = get_settings()
        self.api_url = api_url or settings.EMBEDDING_API_URL
        self.api_key = api_key or settings.EMBEDDING_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        self.client = httpx.AsyncClient(headers=headers, timeout=timeout)

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed_documents([text])
        if not results:
            raise ValueError("Failed to generate embedding for query.")
        return results[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
            
        payload = {
            "input": texts,
            "model": self.model
        }
        
        try:
            response = await self.client.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Sort by index to maintain insertion order
            embedding_data = data["data"]
            embedding_data.sort(key=lambda x: x.get("index", 0))
            
            return [item["embedding"] for item in embedding_data]
        except Exception as e:
            logger.error(f"Error calling embedding API: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()
