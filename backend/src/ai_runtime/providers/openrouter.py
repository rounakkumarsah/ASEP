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
        if not self.api_key:
            # Fallback 1: ~/.ori/credentials.json (managed by Ori CLI)
            try:
                import json
                from pathlib import Path
                ori_cred = Path.home() / ".ori" / "credentials.json"
                if ori_cred.exists():
                    data = json.loads(ori_cred.read_text(encoding="utf-8"))
                    self.api_key = data.get("key", "")
            except Exception:
                pass

        if not self.api_key:
            # Fallback 2: load dotenv
            try:
                from dotenv import load_dotenv
                load_dotenv()
                self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
            except Exception:
                pass

        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "openrouter"

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://asep-ai.vercel.app"),
            "X-Title": os.environ.get("OPENROUTER_APP_TITLE", "ASEP AI"),
            "X-OpenRouter-Title": os.environ.get("OPENROUTER_APP_TITLE", "ASEP AI"),
            "X-OpenRouter-Categories": "cli-agent,cloud-agent",
        }
        if os.environ.get("OPENROUTER_CACHE_ENABLED", "true").lower() in ("true", "1", "yes"):
            headers["X-OpenRouter-Cache"] = "true"
            cache_ttl = os.environ.get("OPENROUTER_CACHE_TTL", "300")
            headers["X-OpenRouter-Cache-TTL"] = str(cache_ttl)
        if os.environ.get("OPENROUTER_METADATA_ENABLED", "true").lower() in ("true", "1", "yes"):
            headers["X-OpenRouter-Metadata"] = "enabled"
        return headers

    @staticmethod
    def _serialize_message(m: Message) -> dict[str, Any]:
        d: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_calls:
            d["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.reasoning:
            d["reasoning"] = m.reasoning
        if m.reasoning_details:
            d["reasoning_details"] = m.reasoning_details
        return d

    def _build_provider_options(self, request: CompletionRequest | None = None) -> dict[str, Any]:
        opts: dict[str, Any] = {}
        if os.environ.get("OPENROUTER_ZDR", "false").lower() in ("true", "1", "yes"):
            opts["zdr"] = True
        if os.environ.get("OPENROUTER_DATA_COLLECTION", "deny").lower() == "deny":
            opts["data_collection"] = "deny"
        if request:
            if request.preferred_max_latency:
                opts["preferred_max_latency"] = request.preferred_max_latency
            if request.preferred_min_throughput:
                opts["preferred_min_throughput"] = request.preferred_min_throughput
        return opts

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = self._build_headers()

        payload: dict[str, Any] = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        provider_opts = self._build_provider_options(request)
        if provider_opts:
            payload["provider"] = provider_opts

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        # OpenRouter Reasoning / Thinking tokens
        if request.reasoning:
            payload["reasoning"] = request.reasoning
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls

        # OpenRouter Broadcast & Observability fields
        if request.user:
            payload["user"] = request.user
        if request.session_id:
            payload["session_id"] = request.session_id
            headers["x-session-id"] = request.session_id
        if request.trace:
            payload["trace"] = request.trace

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            cache_status = response.headers.get("X-OpenRouter-Cache-Status")

            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            reasoning = message_data.get("reasoning")
            reasoning_details = message_data.get("reasoning_details")
            
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
            cached_tokens = meta.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            reasoning_tokens = (
                meta.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
                or meta.get("reasoning_tokens", 0)
            )

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                cache_status=cache_status
            )

            router_metadata = data.get("openrouter_metadata")

            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls,
                router_metadata=router_metadata,
                reasoning=reasoning,
                reasoning_details=reasoning_details
            )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        headers = self._build_headers()
        payload: dict[str, Any] = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        provider_opts = self._build_provider_options(request)
        if provider_opts:
            payload["provider"] = provider_opts

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        # OpenRouter Reasoning / Thinking tokens
        if request.reasoning:
            payload["reasoning"] = request.reasoning
            
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

        # OpenRouter Broadcast & Observability fields
        if request.user:
            payload["user"] = request.user
        if request.session_id:
            payload["session_id"] = request.session_id
            headers["x-session-id"] = request.session_id
        if request.trace:
            payload["trace"] = request.trace

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
                            reasoning = delta.get("reasoning")
                            reasoning_details = delta.get("reasoning_details")
                            
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
                                    
                            chunk_metadata = data.get("openrouter_metadata")
                            yield StreamChunk(
                                text=text,
                                usage=None,
                                finish_reason=finish_reason,
                                tool_calls=tool_calls,
                                router_metadata=chunk_metadata,
                                reasoning=reasoning,
                                reasoning_details=reasoning_details
                            )
                        except Exception:
                            pass

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = self._build_headers()

        payload: dict[str, Any] = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        provider_opts = self._build_provider_options(request)
        if provider_opts:
            payload["provider"] = provider_opts
        
        await self._fetch_capabilities_if_needed(request.model)
        model_data = self._model_capabilities_cache.get(request.model, {})
        supported_params = model_data.get("supported_parameters", [])
        
        supports_format = "response_format" in supported_params if supported_params else True
        if supports_format:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "response", "schema": schema, "strict": True}}
            payload["plugins"] = [{"id": "response-healing"}]

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        # OpenRouter Reasoning / Thinking tokens
        if request.reasoning:
            payload["reasoning"] = request.reasoning
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls

        # OpenRouter Broadcast & Observability fields
        if request.user:
            payload["user"] = request.user
        if request.session_id:
            payload["session_id"] = request.session_id
            headers["x-session-id"] = request.session_id
        if request.trace:
            payload["trace"] = request.trace

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            cache_status = response.headers.get("X-OpenRouter-Cache-Status")

            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            reasoning = message_data.get("reasoning")
            reasoning_details = message_data.get("reasoning_details")
            
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
            cached_tokens = meta.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            reasoning_tokens = (
                meta.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
                or meta.get("reasoning_tokens", 0)
            )

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2),
                cache_status=cache_status
            )

            router_metadata = data.get("openrouter_metadata")

            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls,
                router_metadata=router_metadata,
                reasoning=reasoning,
                reasoning_details=reasoning_details
            )

    async def embeddings(self, texts: list[str], model: str = "openai/text-embedding-3-small") -> list[list[float]]:
        if not self.api_key:
            return [[0.0] * 1536 for _ in texts]
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/embeddings", headers=headers, json={"model": model, "input": texts})
                if resp.status_code == 200:
                    data = resp.json()
                    items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
                    return [item["embedding"] for item in items]
        except Exception:
            pass
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
