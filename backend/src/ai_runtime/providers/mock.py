from __future__ import annotations
import time
from typing import AsyncGenerator, List, Dict, Any
from src.ai_runtime.providers.base import BaseAIProvider
from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    ProviderHealth,
    ProviderCapabilityMatrix,
    UsageInfo,
)

class MockProvider(BaseAIProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        start_time = time.perf_counter()
        text = f"Mock completion response for: '{request.messages[-1].content}'"
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        usage = UsageInfo(
            prompt_tokens=len(request.messages[-1].content) // 4 + 1,
            completion_tokens=len(text) // 4 + 1,
            total_tokens=(len(request.messages[-1].content) + len(text)) // 4 + 2,
            latency_ms=round(latency_ms, 2)
        )
        
        return CompletionResponse(
            text=text,
            usage=usage,
            provider=self.name,
            model=request.model,
            finish_reason="stop"
        )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        text = f"Mock streaming response: "
        yield StreamChunk(text=text)
        
        words = request.messages[-1].content.split()
        for word in words:
            yield StreamChunk(text=word + " ")
            
        yield StreamChunk(
            text="",
            usage=UsageInfo(
                prompt_tokens=len(request.messages[-1].content) // 4 + 1,
                completion_tokens=5,
                total_tokens=len(request.messages[-1].content) // 4 + 6,
                latency_ms=10.0
            ),
            finish_reason="stop"
        )

    async def complete_structured(self, request: CompletionRequest, schema: Dict[str, Any]) -> CompletionResponse:
        start_time = time.perf_counter()
        # Simply return dummy mock json structure matching a generic schema representation
        text = '{"status": "completed", "result": "mock_structured_value"}'
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        usage = UsageInfo(
            prompt_tokens=len(request.messages[-1].content) // 4 + 1,
            completion_tokens=len(text) // 4 + 1,
            total_tokens=(len(request.messages[-1].content) + len(text)) // 4 + 2,
            latency_ms=round(latency_ms, 2)
        )
        
        return CompletionResponse(
            text=text,
            usage=usage,
            provider=self.name,
            model=request.model,
            finish_reason="stop"
        )

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        # Return mock float vector
        return [[0.1] * 128 for _ in texts]

    async def check_health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            is_healthy=True,
            active_model="mock-default",
            circuit_breaker_state="CLOSED",
            error_count=0,
            latency_ms=1.0,
            loaded_models=["mock-default", "mock-lite"],
            last_error=None
        )

    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=False,
            tool_calling=True,
            embeddings=True,
            reasoning=True,
            context_window=8192
        )
