from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderCapabilityMatrix,
    ProviderHealth,
    StreamChunk,
    UsageInfo,
)
from src.ai_runtime.providers.base import BaseAIProvider


class OpenRouterProvider(BaseAIProvider):
    _model_capabilities_cache: dict[str, dict] = {}
    
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "openrouter"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}

        payload = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [{"role": m.role, "content": m.content, **({"tool_calls": m.tool_calls} if m.tool_calls else {}), **({"tool_call_id": m.tool_call_id} if m.tool_call_id else {})} for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            
            tool_calls = None
            if "tool_calls" in message_data:
                from src.ai_runtime.contracts import ToolCall
                tool_calls = []
                for tc in message_data["tool_calls"]:
                    import json
                    args = tc["function"]["arguments"]
                    if not isinstance(args, str):
                        args = json.dumps(args)
                    tool_calls.append(ToolCall(
                        id=tc["id"],
                        type="function",
                        name=tc["function"]["name"],
                        arguments=args
                    ))

            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)

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
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls
            )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}
        payload = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [{"role": m.role, "content": m.content, **({"tool_calls": m.tool_calls} if m.tool_calls else {}), **({"tool_call_id": m.tool_call_id} if m.tool_call_id else {})} for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls
        
        # Pass tools if any exist
        
        # Capability validation for tools
        await self._fetch_capabilities_if_needed(request.model)
        model_data = self._model_capabilities_cache.get(request.model, {})
        supported_params = model_data.get("supported_parameters", [])
        
        # Inject Server Tools
        server_tools = [
            {"type": "openrouter:web_search"},
            {"type": "openrouter:web_fetch"},
            {"type": "openrouter:datetime"}
        ]
        
        # Check if model supports tools before adding them
        supports_tools = "tools" in supported_params if supported_params else True
        if supports_tools:
            if getattr(request, "tools", None):
                payload["tools"] = request.tools + server_tools
            else:
                payload["tools"] = server_tools
                
        if supports_tools and request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if supports_tools and request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            async with client.stream("POST", "/chat/completions", headers=headers, json=payload) as response:
                response.raise_for_status()
                import json
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: "):]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            chunk = data.get("choices", [{}])[0]
                            delta = chunk.get("delta", {})
                            text = delta.get("content", "")
                            finish_reason = chunk.get("finish_reason")
                            
                            # Parse streaming tool calls
                            tool_calls = None
                            if "tool_calls" in delta:
                                from src.ai_runtime.contracts import ToolCall
                                tool_calls = []
                                for tc in delta["tool_calls"]:
                                    import json
                                    args = tc["function"]["arguments"] if "function" in tc and "arguments" in tc["function"] else ""
                                    tool_calls.append(ToolCall(
                                        id=tc.get("id", ""),
                                        type="function",
                                        name=tc.get("function", {}).get("name", ""),
                                        arguments=args
                                    ))
                                    
                            yield StreamChunk(text=text, usage=None, finish_reason=finish_reason, tool_calls=tool_calls)
                        except Exception:
                            pass

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}

        payload = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [{"role": m.role, "content": m.content, **({"tool_calls": m.tool_calls} if m.tool_calls else {}), **({"tool_call_id": m.tool_call_id} if m.tool_call_id else {})} for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        
        await self._fetch_capabilities_if_needed(request.model)
        model_data = self._model_capabilities_cache.get(request.model, {})
        supported_params = model_data.get("supported_parameters", [])
        
        supports_format = "response_format" in supported_params if supported_params else True
        if supports_format:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "response", "schema": schema, "strict": True}}

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            
            tool_calls = None
            if "tool_calls" in message_data:
                from src.ai_runtime.contracts import ToolCall
                tool_calls = []
                for tc in message_data["tool_calls"]:
                    import json
                    args = tc["function"]["arguments"]
                    if not isinstance(args, str):
                        args = json.dumps(args)
                    tool_calls.append(ToolCall(
                        id=tc["id"],
                        type="function",
                        name=tc["function"]["name"],
                        arguments=args
                    ))

            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)

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
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls
            )

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
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
                last_error="OPENROUTER_API_KEY not configured"
            )
        start = time.perf_counter()
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=3.0) as client:
                response = await client.get("/models", headers=headers)
                is_healthy = response.status_code == 200
                latency = (time.perf_counter() - start) * 1000.0
                return ProviderHealth(
                    provider_name=self.name,
                    is_healthy=is_healthy,
                    active_model="gpt-4o",
                    circuit_breaker_state="CLOSED",
                    error_count=0,
                    latency_ms=round(latency, 2),
                    loaded_models=["gpt-4o", "gpt-4-turbo"],
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

    async def _fetch_capabilities_if_needed(self, model: str):
        if not self._model_capabilities_cache:
            try:
                headers = {"HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}
                async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                    resp = await client.get("/models", headers=headers)
                    if resp.status_code == 200:
                        models = resp.json().get("data", [])
                        for m in models:
                            self._model_capabilities_cache[m["id"]] = m
            except Exception:
                pass

    def get_capability_matrix(self, model: str = "") -> ProviderCapabilityMatrix:
        import asyncio
        # We can't await in sync method easily unless we run event loop, but get_capability_matrix isn't async.
        # It's fine to return a default if not fetched.
        # Since the interface is synchronous, we will return True for now but we'll use async checks in complete.
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=True,
            reasoning=True,
            context_window=16384
        )
