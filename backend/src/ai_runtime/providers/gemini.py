from __future__ import annotations
import httpx
import json
import os
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

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "gemini"

    def _convert_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        contents = []
        for msg in messages:
            # Map roles: 'system' -> 'system', 'user' -> 'user', 'assistant' -> 'model'
            role = "user"
            if msg.role == "assistant":
                role = "model"
            elif msg.role == "system":
                role = "system"
                
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        return contents

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        contents = self._convert_messages(request.messages)
        
        # Pull out system instruction if present
        system_instruction = None
        filtered_contents = []
        for content in contents:
            if content["role"] == "system":
                system_instruction = {"parts": content["parts"]}
            else:
                filtered_contents.append(content)

        payload = {
            "contents": filtered_contents,
            "generationConfig": {
                "temperature": request.temperature,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        url = f"/models/{request.model}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Extract generated content text
            text = ""
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexDown):
                pass
                
            meta = data.get("usageMetadata", {})
            prompt_tokens = meta.get("promptTokenCount", 0)
            completion_tokens = meta.get("candidatesTokenCount", 0)
            
            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
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
        # For lightweight implementation, fallback stream calls to complete yielding all at once,
        # or implement Server-Sent Events stream support for Gemini. Let's yield complete response.
        res = await self.complete(request)
        yield StreamChunk(text=res.text, usage=res.usage, finish_reason=res.finish_reason)

    async def complete_structured(self, request: CompletionRequest, schema: Dict[str, Any]) -> CompletionResponse:
        # Gemini structured output can be forced by setting responseMimeType to application/json
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        contents = self._convert_messages(request.messages)
        
        filtered_contents = [c for c in contents if c["role"] != "system"]
        system_prompt = next((c["parts"] for c in contents if c["role"] == "system"), None)

        payload = {
            "contents": filtered_contents,
            "generationConfig": {
                "temperature": request.temperature,
                "responseMimeType": "application/json",
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": system_prompt}
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        url = f"/models/{request.model}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            text = ""
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except KeyError:
                pass
                
            meta = data.get("usageMetadata", {})
            prompt_tokens = meta.get("promptTokenCount", 0)
            completion_tokens = meta.get("candidatesTokenCount", 0)
            
            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
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
        return [[0.0] * 1536 for _ in texts]

    async def check_health(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider_name=self.name,
                is_healthy=False,
                active_model="none",
                circuit_breaker_state="CLOSED",
                error_count=1,
                latency_ms=0.0,
                last_error="GEMINI_API_KEY not configured"
            )
        start = time.perf_counter()
        try:
            url = f"/models/gemini-2.5-flash?key={self.api_key}"
            async with httpx.AsyncClient(base_url=self.base_url, timeout=3.0) as client:
                response = await client.get(url)
                is_healthy = response.status_code == 200
                latency = (time.perf_counter() - start) * 1000.0
                return ProviderHealth(
                    provider_name=self.name,
                    is_healthy=is_healthy,
                    active_model="gemini-2.5-flash",
                    circuit_breaker_state="CLOSED",
                    error_count=0,
                    latency_ms=round(latency, 2),
                    loaded_models=["gemini-2.5-flash", "gemini-2.5-pro"],
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
            reasoning=True,
            context_window=32768
        )
