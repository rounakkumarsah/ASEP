from __future__ import annotations
import httpx
import json
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
from src.config.settings import get_settings

class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "ollama"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        start_time = time.perf_counter()
        
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
            }
        }
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            
            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2)
            )
            
            return CompletionResponse(
                text=data["message"]["content"],
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason="stop"
            )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
            "options": {
                "temperature": request.temperature,
            }
        }
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        start_time = time.perf_counter()
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    chunk_text = data.get("message", {}).get("content", "")
                    
                    if data.get("done", False):
                        latency_ms = (time.perf_counter() - start_time) * 1000.0
                        prompt_tokens = data.get("prompt_eval_count", 0)
                        completion_tokens = data.get("eval_count", 0)
                        
                        usage = UsageInfo(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens,
                            latency_ms=round(latency_ms, 2)
                        )
                        yield StreamChunk(text=chunk_text, usage=usage, finish_reason="stop")
                    else:
                        yield StreamChunk(text=chunk_text)

    async def complete_structured(self, request: CompletionRequest, schema: Dict[str, Any]) -> CompletionResponse:
        # Structured output in Ollama requires setting JSON format option or schema options
        start_time = time.perf_counter()
        
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "format": "json",  # Forces JSON output mode
            "options": {
                "temperature": request.temperature,
            }
        }
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            
            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2)
            )
            
            return CompletionResponse(
                text=data["message"]["content"],
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason="stop"
            )

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        # Scaffold implementation talking to local embeddings API
        vectors = []
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            for text in texts:
                payload = {"model": "nomic-embed-text", "prompt": text}
                response = await client.post("/api/embeddings", json=payload)
                if response.status_code == 200:
                    vectors.append(response.json().get("embedding", []))
                else:
                    vectors.append([0.0] * 768)
        return vectors

    async def check_health(self) -> ProviderHealth:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
                # Query tags endpoint to list downloaded models
                response = await client.get("/api/tags")
                is_healthy = response.status_code == 200
                loaded_models = []
                if is_healthy:
                    loaded_models = [m["name"] for m in response.json().get("models", [])]
                
                latency = (time.perf_counter() - start) * 1000.0
                return ProviderHealth(
                    provider_name=self.name,
                    is_healthy=is_healthy,
                    active_model=loaded_models[0] if loaded_models else "none",
                    circuit_breaker_state="CLOSED",
                    error_count=0,
                    latency_ms=round(latency, 2),
                    loaded_models=loaded_models,
                    last_error=None
                )
        except Exception as exc:
            return ProviderHealth(
                provider_name=self.name,
                is_healthy=False,
                active_model="none",
                circuit_breaker_state="CLOSED",
                error_count=1,
                latency_ms=0.0,
                last_error=str(exc)
            )

    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=True,
            reasoning=False,
            context_window=8192
        )
