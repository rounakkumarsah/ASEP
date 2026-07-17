from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any
from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    ProviderHealth,
    ProviderCapabilityMatrix,
)

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the lowercase unique provider identifier string."""
        pass

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a standard unary non-streaming complete call."""
        pass

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """Execute a streaming complete call yielding text token chunks."""
        pass

    @abstractmethod
    async def complete_structured(self, request: CompletionRequest, schema: Dict[str, Any]) -> CompletionResponse:
        """Execute a complete call forcing json schemas conformance matching the output."""
        pass

    @abstractmethod
    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Scaffold interface generating float vectors from text chunks."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Query availability, uptime latency, and loaded models."""
        pass

    @abstractmethod
    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        """Return features support matrix and limits settings."""
        pass
