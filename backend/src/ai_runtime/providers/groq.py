from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx

from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    Message,
    ProviderCapabilityMatrix,
    ProviderHealth,
    StreamChunk,
    ToolCall,
    UsageInfo,
)
from src.ai_runtime.providers.base import BaseAIProvider


class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            try:
                from dotenv import load_dotenv
                backend_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
                if backend_env.exists():
                    load_dotenv(backend_env)
                else:
                    load_dotenv()
                self.api_key = os.environ.get("GROQ_API_KEY", "")
            except Exception:
                pass

        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "groq"

    @staticmethod
    def _serialize_message(m: Message) -> dict[str, Any]:
        d: dict[str, Any] = {"role": m.role, "content": m.content or ""}
        if m.tool_calls:
            d["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        return d

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Groq-Beta": "inference-metrics"
        }

    def _apply_reasoning_parameters(self, payload: dict[str, Any], model: str, reasoning: dict[str, Any] | None) -> None:
        if not reasoning:
            return

        effort = reasoning.get("effort")
        fmt = reasoning.get("format")
        model_lower = model.lower()

        if "gpt-oss" in model_lower:
            payload["include_reasoning"] = True
            if effort in ("low", "medium", "high"):
                payload["reasoning_effort"] = effort
        elif "qwen" in model_lower:
            if fmt in ("parsed", "raw", "hidden"):
                payload["reasoning_format"] = fmt
            elif not payload.get("tools") and payload.get("response_format", {}).get("type") != "json_object":
                payload["reasoning_format"] = "parsed"
            if effort in ("none", "default", "low", "medium", "high"):
                payload["reasoning_effort"] = effort
        else:
            if effort:
                payload["reasoning_effort"] = effort

    @staticmethod
    def _resolve_model(model: str) -> str:
        if model in ("groq", "groq/default"):
            return "openai/gpt-oss-20b"
        if model.startswith("groq/") and model not in ("groq/compound", "groq/compound-mini"):
            remainder = model[len("groq/"):]
            if remainder.startswith("gpt-oss"):
                return f"openai/{remainder}"
            if remainder.startswith("qwen3"):
                return f"qwen/{remainder}"
            return remainder
        return model

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = self._get_headers()

        model = self._resolve_model(request.model)

        payload: dict[str, Any] = {
            "model": model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }

        if request.max_tokens:
            payload["max_completion_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            unsupported_parallel = ("gpt-oss", "qwen3.8", "compound")
            if not any(up in model.lower() for up in unsupported_parallel):
                payload["parallel_tool_calls"] = request.parallel_tool_calls
        if request.user:
            payload["user"] = request.user
        request_meta = getattr(request, "router_metadata", None)
        if request_meta and isinstance(request_meta, dict):
            if "search_settings" in request_meta:
                payload["search_settings"] = request_meta["search_settings"]
            if "compound_custom" in request_meta:
                payload["compound_custom"] = request_meta["compound_custom"]
            if "disable_tool_validation" in request_meta:
                payload["disable_tool_validation"] = request_meta["disable_tool_validation"]
            if "documents" in request_meta:
                payload["documents"] = request_meta["documents"]
            if "citation_options" in request_meta:
                payload["citation_options"] = request_meta["citation_options"]
            if "top_p" in request_meta:
                payload["top_p"] = request_meta["top_p"]
            if "stop" in request_meta:
                payload["stop"] = request_meta["stop"]

        if "compound" in model:
            headers["Groq-Model-Version"] = "latest"

        if getattr(request, "service_tier", None):
            payload["service_tier"] = request.service_tier
        if getattr(request, "seed", None) is not None:
            payload["seed"] = request.seed

        # Apply reasoning options
        self._apply_reasoning_parameters(payload, model, request.reasoning)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                response = await client.post("/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Handle Flex tier capacity exceeded (HTTP 498) by falling back to on_demand
                if e.response.status_code == 498 and payload.get("service_tier") == "flex":
                    payload["service_tier"] = "on_demand"
                    response = await client.post("/chat/completions", headers=headers, json=payload)
                    response.raise_for_status()
                # Retry with lowered temperature if tool call generation failed (400 error)
                elif e.response.status_code == 400 and request.tools and payload.get("temperature", 0.7) > 0.3:
                    payload["temperature"] = max(payload.get("temperature", 0.7) - 0.2, 0.1)
                    response = await client.post("/chat/completions", headers=headers, json=payload)
                    response.raise_for_status()
                else:
                    raise

            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            reasoning = message_data.get("reasoning")
            reasoning_details = message_data.get("reasoning_details")

            tool_calls = None
            if "tool_calls" in message_data:
                import json
                tool_calls = []
                for tc in message_data["tool_calls"]:
                    args = tc["function"]["arguments"]
                    if not isinstance(args, str):
                        args = json.dumps(args)
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        type="function",
                        name=tc["function"]["name"],
                        arguments=args
                    ))

            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)
            total_tokens = meta.get("total_tokens", prompt_tokens + completion_tokens)
            cached_tokens = (meta.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
            reasoning_tokens = (meta.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cached_tokens=cached_tokens,
                reasoning_tokens=reasoning_tokens,
                latency_ms=round(latency_ms, 2)
            )

            # Metadata including inference metrics, executed tools, and rate limits
            router_metadata: dict[str, Any] = {}
            if "x_groq" in data:
                router_metadata["x_groq"] = data["x_groq"]
            if "executed_tools" in message_data:
                router_metadata["executed_tools"] = message_data["executed_tools"]

            resp_headers = getattr(response, "headers", None)
            if resp_headers and isinstance(resp_headers, (dict, httpx.Headers)):
                for header_name, key in [
                    ("x-ratelimit-remaining-requests", "ratelimit_remaining_requests"),
                    ("x-ratelimit-remaining-tokens", "ratelimit_remaining_tokens"),
                    ("x-ratelimit-reset-requests", "ratelimit_reset_requests"),
                    ("x-ratelimit-reset-tokens", "ratelimit_reset_tokens"),
                ]:
                    if header_name in resp_headers:
                        router_metadata[key] = resp_headers[header_name]

            for timing_key in ("queue_time", "prompt_time", "completion_time", "total_time"):
                if timing_key in meta:
                    router_metadata[timing_key] = meta[timing_key]

            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls,
                router_metadata=router_metadata if router_metadata else None,
                reasoning=reasoning,
                reasoning_details=reasoning_details
            )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = self._get_headers()

        model = self._resolve_model(request.model)

        payload: dict[str, Any] = {
            "model": model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }

        if request.max_tokens:
            payload["max_completion_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            unsupported_parallel = ("gpt-oss", "qwen3.8", "compound")
            if not any(up in model.lower() for up in unsupported_parallel):
                payload["parallel_tool_calls"] = request.parallel_tool_calls
        if request.user:
            payload["user"] = request.user
        request_meta = getattr(request, "router_metadata", None)
        if request_meta and isinstance(request_meta, dict):
            if "search_settings" in request_meta:
                payload["search_settings"] = request_meta["search_settings"]
            if "compound_custom" in request_meta:
                payload["compound_custom"] = request_meta["compound_custom"]
            if "disable_tool_validation" in request_meta:
                payload["disable_tool_validation"] = request_meta["disable_tool_validation"]
            if "documents" in request_meta:
                payload["documents"] = request_meta["documents"]
            if "citation_options" in request_meta:
                payload["citation_options"] = request_meta["citation_options"]
            if "top_p" in request_meta:
                payload["top_p"] = request_meta["top_p"]
            if "stop" in request_meta:
                payload["stop"] = request_meta["stop"]

        if "compound" in model:
            headers["Groq-Model-Version"] = "latest"

        if getattr(request, "service_tier", None):
            payload["service_tier"] = request.service_tier
        if getattr(request, "seed", None) is not None:
            payload["seed"] = request.seed

        payload["stream_options"] = {"include_usage": True}

        self._apply_reasoning_parameters(payload, model, request.reasoning)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            async with client.stream("POST", "/chat/completions", headers=headers, json=payload) as response:
                response.raise_for_status()
                import json
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: "):]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            chunk = data.get("choices", [{}])[0]
                            delta = chunk.get("delta", {})
                            text = delta.get("content", "")
                            finish_reason = chunk.get("finish_reason")
                            reasoning = delta.get("reasoning")
                            reasoning_details = delta.get("reasoning_details")

                            tool_calls = None
                            if "tool_calls" in delta:
                                tool_calls = []
                                for tc in delta["tool_calls"]:
                                    args = tc.get("function", {}).get("arguments", "")
                                    tool_calls.append(ToolCall(
                                        id=tc.get("id", ""),
                                        type="function",
                                        name=tc.get("function", {}).get("name", ""),
                                        arguments=args
                                    ))

                            usage = None
                            if "usage" in data:
                                meta = data["usage"]
                                prompt_tokens = meta.get("prompt_tokens", 0)
                                completion_tokens = meta.get("completion_tokens", 0)
                                usage = UsageInfo(
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    total_tokens=prompt_tokens + completion_tokens,
                                    latency_ms=0.0
                                )

                            chunk_router_meta = None
                            if "executed_tools" in delta or "executed_tools" in chunk:
                                chunk_router_meta = {"executed_tools": delta.get("executed_tools") or chunk.get("executed_tools")}

                            yield StreamChunk(
                                text=text,
                                usage=usage,
                                finish_reason=finish_reason,
                                tool_calls=tool_calls,
                                reasoning=reasoning,
                                reasoning_details=reasoning_details,
                                router_metadata=chunk_router_meta
                            )
                        except Exception:
                            pass

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        headers = self._get_headers()

        model = self._resolve_model(request.model)

        schema_title = schema.get("title", "structured_output")
        response_format: dict[str, Any]
        if schema.get("type") == "object" and "properties" in schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_title,
                    "schema": schema,
                    "strict": True
                }
            }
        else:
            response_format = {"type": "json_object"}

        payload: dict[str, Any] = {
            "model": model,
            "messages": [self._serialize_message(m) for m in request.messages],
            "temperature": request.temperature,
            "stream": False,
            "response_format": response_format
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            try:
                response = await client.post("/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Fallback to json_object if json_schema is not supported for this model
                if payload["response_format"].get("type") == "json_schema" and e.response.status_code in (400, 422):
                    payload["response_format"] = {"type": "json_object"}
                    response = await client.post("/chat/completions", headers=headers, json=payload)
                    response.raise_for_status()
                else:
                    raise

            data = response.json()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            text = data["choices"][0]["message"].get("content") or ""

            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=round(latency_ms, 2)
            )

            router_metadata: dict[str, Any] = {}
            if "x_groq" in data:
                router_metadata["x_groq"] = data["x_groq"]

            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                router_metadata=router_metadata if router_metadata else None
            )

    async def transcribe_audio(
        self,
        audio_bytes: bytes | None = None,
        filename: str = "audio.wav",
        url: str | None = None,
        model: str = "whisper-large-v3-turbo",
        prompt: str | None = None,
        language: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0,
        timestamp_granularities: list[str] | None = None
    ) -> dict[str, Any]:
        """Transcribe audio to text using Groq Whisper endpoints."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        data: dict[str, Any] = {
            "model": model,
            "response_format": response_format,
            "temperature": temperature
        }
        if prompt:
            data["prompt"] = prompt
        if language:
            data["language"] = language
        if timestamp_granularities:
            data["timestamp_granularities[]"] = timestamp_granularities

        files = None
        if audio_bytes:
            files = {"file": (filename, audio_bytes)}
        elif url:
            data["url"] = url
        else:
            raise ValueError("Either audio_bytes or url must be provided.")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            res = await client.post("/audio/transcriptions", headers=headers, data=data, files=files)
            res.raise_for_status()
            if response_format in ("json", "verbose_json"):
                return res.json()
            return {"text": res.text}

    async def translate_audio(
        self,
        audio_bytes: bytes | None = None,
        filename: str = "audio.wav",
        url: str | None = None,
        model: str = "whisper-large-v3",
        prompt: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0
    ) -> dict[str, Any]:
        """Translate audio into English text using Groq Whisper translation endpoint."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        data: dict[str, Any] = {
            "model": model,
            "response_format": response_format,
            "temperature": temperature
        }
        if prompt:
            data["prompt"] = prompt

        files = None
        if audio_bytes:
            files = {"file": (filename, audio_bytes)}
        elif url:
            data["url"] = url
        else:
            raise ValueError("Either audio_bytes or url must be provided.")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            res = await client.post("/audio/translations", headers=headers, data=data, files=files)
            res.raise_for_status()
            if response_format in ("json", "verbose_json"):
                return res.json()
            return {"text": res.text}

    async def generate_speech(
        self,
        text: str,
        model: str = "canopylabs/orpheus-v1-english",
        voice: str = "troy",
        response_format: str = "wav",
        sample_rate: int = 48000,
        speed: float = 1.0
    ) -> bytes:
        """Synthesize text into speech audio using Groq Orpheus/PlayAI TTS."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            "sample_rate": sample_rate,
            "speed": speed
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.post("/audio/speech", headers=headers, json=payload)
            res.raise_for_status()
            return res.content

    async def complete_response(
        self,
        input_text: str | list[Any],
        model: str = "openai/gpt-oss-120b",
        instructions: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        service_tier: str = "auto",
        metadata: dict[str, Any] | None = None,
        max_output_tokens: int | None = None
    ) -> dict[str, Any]:
        """Call Groq's Responses API Beta (/v1/responses) for unified agentic executions."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: dict[str, Any] = {
            "model": model,
            "input": input_text,
            "service_tier": service_tier
        }
        if instructions:
            payload["instructions"] = instructions
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if metadata:
            payload["metadata"] = metadata
        if max_output_tokens:
            payload["max_output_tokens"] = max_output_tokens

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            res = await client.post("/responses", headers=headers, json=payload)
            res.raise_for_status()
            return res.json()

    # --- Batches & Files APIs ---

    async def upload_file(self, file_content: bytes | str, filename: str = "batch.jsonl", purpose: str = "batch") -> dict[str, Any]:
        """Upload a file (e.g. JSONL batch requests) to Groq Files API."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        content_bytes = file_content.encode("utf-8") if isinstance(file_content, str) else file_content
        files = {"file": (filename, content_bytes)}
        data = {"purpose": purpose}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            res = await client.post("/files", headers=headers, data=data, files=files)
            res.raise_for_status()
            return res.json()

    async def retrieve_file(self, file_id: str) -> dict[str, Any]:
        """Retrieve metadata for an uploaded file."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.get(f"/files/{file_id}", headers=headers)
            res.raise_for_status()
            return res.json()

    async def download_file_content(self, file_id: str) -> str:
        """Download file content (e.g. batch results or error file)."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            res = await client.get(f"/files/{file_id}/content", headers=headers)
            res.raise_for_status()
            return res.text

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """Delete an uploaded file."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.delete(f"/files/{file_id}", headers=headers)
            res.raise_for_status()
            return res.json()

    async def create_batch(
        self,
        input_file_id: str,
        endpoint: str = "/v1/chat/completions",
        completion_window: str = "24h",
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create and queue an asynchronous Batch API job (50% cost discount)."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input_file_id": input_file_id,
            "endpoint": endpoint,
            "completion_window": completion_window
        }
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.post("/batches", headers=headers, json=payload)
            res.raise_for_status()
            return res.json()

    async def retrieve_batch(self, batch_id: str) -> dict[str, Any]:
        """Retrieve status of a batch job."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.get(f"/batches/{batch_id}", headers=headers)
            res.raise_for_status()
            return res.json()

    async def list_batches(self, limit: int = 20, cursor: str | None = None) -> dict[str, Any]:
        """List batch jobs with cursor pagination."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.get("/batches", headers=headers, params=params)
            res.raise_for_status()
            return res.json()

    async def cancel_batch(self, batch_id: str) -> dict[str, Any]:
        """Cancel an in-progress batch job."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.post(f"/batches/{batch_id}/cancel", headers=headers)
            res.raise_for_status()
            return res.json()

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
                last_error="GROQ_API_KEY not configured"
            )
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
                res = await client.get("/models", headers={"Authorization": f"Bearer {self.api_key}"})
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                is_healthy = res.status_code == 200
                models = [m["id"] for m in res.json().get("data", [])] if is_healthy else []
                return ProviderHealth(
                    provider_name=self.name,
                    is_healthy=is_healthy,
                    active_model="qwen/qwen3.8-27b",
                    circuit_breaker_state="CLOSED",
                    error_count=0 if is_healthy else 1,
                    latency_ms=round(latency_ms, 2),
                    loaded_models=models,
                    last_error=None if is_healthy else f"HTTP {res.status_code}"
                )
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ProviderHealth(
                provider_name=self.name,
                is_healthy=False,
                active_model="none",
                circuit_breaker_state="CLOSED",
                error_count=1,
                latency_ms=round(latency_ms, 2),
                last_error=str(e)
            )

    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=False,
            reasoning=True,
            context_window=131072
        )
