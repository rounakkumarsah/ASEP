from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List
from src.ai_runtime.service import AIRuntimeService

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of document texts."""
        pass

class RuntimeEmbeddingProvider(EmbeddingProvider):
    """Embedding provider wrapping the new vendor-agnostic AIRuntimeService."""

    def __init__(self, service: AIRuntimeService | None = None) -> None:
        self.service = service or AIRuntimeService()

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        if not res:
            raise ValueError("Failed to generate embedding for query.")
        return res[0]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            return await self.service.embeddings(texts)
        except Exception as e:
            logger.error(f"Error calling embedding service: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        pass

class OpenAICompatibleEmbeddingProvider(RuntimeEmbeddingProvider):
    """Subclass maintaining compatibility with the legacy provider."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
