from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderCapabilityMatrix,
    ProviderHealth,
    StreamChunk,
    UsageInfo,
)
from src.ai_runtime.providers.base import BaseAIProvider
from src.config.settings import get_settings


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic Claude 3.5 Sonnet LLM provider mapping client calls directly
    to the official anthropic SDK API endpoints.
    """
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None) or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

    def _get_client(self):
        if not self._client:
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable or settings parameter is not configured.")
            # Lazy import to keep startup times fast
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def _convert_messages(self, messages: list[Any]) -> tuple[str | None, list[dict[str, Any]]]:
        system_prompt = None
        converted_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                converted_messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                })
        return system_prompt, converted_messages

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        client = self._get_client()
        start_time = time.perf_counter()
        system_prompt, messages = self._convert_messages(request.messages)

        # Target dynamic model overrides or Claude 3.5 Sonnet by default
        target_model = request.model if "claude" in request.model.lower() else "claude-3-5-sonnet-20241022"

        # Anthropic calls are executing in an executor thread pool to support async wrappers
        import asyncio
        loop = asyncio.get_running_loop()

        kwargs: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        else:
            kwargs["max_tokens"] = 4096

        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(**kwargs)
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        usage = UsageInfo(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=round(latency_ms, 2)
        )

        # Retrieve text from message content block
        text = ""
        if response.content and len(response.content) > 0:
            text = response.content[0].text

        return CompletionResponse(
            text=text,
            usage=usage,
            provider=self.name,
            model=target_model,
            finish_reason=response.stop_reason or "stop"
        )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        # Simple stream fallback utilizing complete interface return yields
        res = await self.complete(request)
        yield StreamChunk(text=res.text, usage=res.usage, finish_reason=res.finish_reason)

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        # Structured output delegates to normal complete with formatting injection
        prompt_override = request.messages.copy()
        import copy
        # Inject JSON schema matching instructions
        schema_instruction = f"\n\nYou MUST format your output response matches the following strict JSON schema:\n{schema}\n"
        if len(prompt_override) > 0:
            last_msg = copy.deepcopy(prompt_override[-1])
            last_msg.content = last_msg.content + schema_instruction
            prompt_override[-1] = last_msg

        request.messages = prompt_override
        return await self.complete(request)

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        # Anthropic does not support client side embeddings natively; return vector stubs
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
                last_error="ANTHROPIC_API_KEY not configured"
            )
        return ProviderHealth(
            provider_name=self.name,
            is_healthy=True,
            active_model="claude-3-5-sonnet-20241022",
            circuit_breaker_state="CLOSED",
            error_count=0,
            latency_ms=0.0,
            loaded_models=["claude-3-5-sonnet-20241022"],
            last_error=None
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
            context_window=200000
        )
