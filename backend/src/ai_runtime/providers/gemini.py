from __future__ import annotations

import base64
import contextlib
import datetime
import hashlib
import hmac
import json
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
    ToolCall,
    UsageInfo,
)
from src.ai_runtime.providers.base import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None) -> None:
        raw_key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        if raw_key.startswith("AQ.AQ."):
            raw_key = raw_key[3:]
        self.api_key = raw_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = 30.0

    @property
    def name(self) -> str:
        return "gemini"

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        contents = []
        for msg in messages:
            role = "user"
            if msg.role == "assistant":
                role = "model"
            elif msg.role == "system":
                role = "system"

            parts = []
            if isinstance(msg.content, str):
                parts.append({"text": msg.content})
            elif isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, str):
                        parts.append({"text": item})
                    elif isinstance(item, dict):
                        if item.get("type") == "text":
                            parts.append({"text": item.get("text", "")})
                        elif item.get("type") == "image_url":
                            url_val = item.get("image_url", {}).get("url", "")
                            if url_val.startswith("data:"):
                                header, b64_data = url_val.split(",", 1)
                                mime_type = header.split(";")[0].replace("data:", "")
                                parts.append({"inlineData": {"mimeType": mime_type, "data": b64_data}})
                            else:
                                parts.append({"fileData": {"fileUri": url_val}})

            contents.append({
                "role": role,
                "parts": parts or [{"text": ""}]
            })
        return contents

    @staticmethod
    def _resolve_model(model: str) -> str:
        model_clean = model.strip()
        if model_clean.startswith("gemini/"):
            model_clean = model_clean[len("gemini/"):]

        # Gemini 3 Core Text & Reasoning
        if model_clean in ("gemini", "gemini-default", "gemini-flash", "gemini-3.8", "gemini-3.8-flash", "antigravity-default"):
            return "gemini-3.8-flash"
        if model_clean in ("gemini-3.7", "gemini-3.7-flash"):
            return "gemini-3.7-flash"
        if model_clean in ("gemini-3.6", "gemini-3.6-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"):
            return "gemini-3.6-flash"
        if model_clean in ("gemini-pro", "gemini-1.5-pro", "gemini-2.5-pro", "gemini-3.1-pro"):
            return "gemini-3.1-pro"
        if model_clean in ("gemini-lite", "gemini-flash-lite", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite"):
            return "gemini-3.5-flash-lite"
        if model_clean == "gemini-3.1-flash-lite":
            return "gemini-3.1-flash-lite"

        # Nano Banana Image Family
        if model_clean in ("gemini-image", "nano-banana", "nano-banana-2", "gemini-3.1-flash-image"):
            return "gemini-3.1-flash-image"
        if model_clean in ("nano-banana-pro", "gemini-3-pro-image"):
            return "gemini-3-pro-image"
        if model_clean in ("nano-banana-2-lite", "gemini-3.1-flash-lite-image"):
            return "gemini-3.1-flash-lite-image"

        # Veo & Omni Video Generation
        if model_clean in ("veo", "veo-3.1", "veo-3.1-generate-preview"):
            return "veo-3.1-generate-preview"
        if model_clean in ("veo-fast", "veo-3.1-fast-generate-preview"):
            return "veo-3.1-fast-generate-preview"
        if model_clean in ("veo-lite", "veo-3.1-lite-generate-preview"):
            return "veo-3.1-lite-generate-preview"
        if model_clean in ("omni", "gemini-omni", "gemini-omni-1.1-flash"):
            return "gemini-omni-1.1-flash"

        # Music & Audio
        if model_clean in ("lyria-clip", "lyria-3.5-clip-preview"):
            return "lyria-3.5-clip-preview"
        if model_clean in ("lyria-pro", "lyria-3.5-pro-preview"):
            return "lyria-3.5-pro-preview"
        if model_clean in ("lyria-realtime", "models/lyria-realtime-exp"):
            return "models/lyria-realtime-exp"
        if model_clean in ("gemini-transcribe", "gemini-3.5-transcribe"):
            return "gemini-3.5-transcribe"
        if model_clean in ("gemini-tts", "gemini-3.1-flash-tts-preview"):
            return "gemini-3.1-flash-tts-preview"
        if model_clean in ("gemini-translate", "gemini-3.5-live-translate-preview"):
            return "gemini-3.5-live-translate-preview"

        # Embeddings & Agents
        if model_clean in ("gemini-embedding", "gemini-embedding-2"):
            return "gemini-embedding-2"
        if model_clean in ("deep-research", "deep-research-preview-04-2026"):
            return "deep-research-preview-04-2026"
        if model_clean in ("antigravity-agent", "antigravity-preview-05-2026"):
            return "antigravity-preview-05-2026"
        if model_clean in ("computer-use", "gemini-2.5-computer-use-preview-10-2025"):
            return "gemini-2.5-computer-use-preview-10-2025"

        return model_clean

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

        model_name = self._resolve_model(request.model)
        meta = request.router_metadata or {}
        gen_config: dict[str, Any] = {}

        if model_name.startswith("gemini-3."):
            # Gemini 3.x models require temperature to remain at default (1.0)
            # to avoid degraded mathematical reasoning, performance loss, and repetitive loops.
            thinking_lvl = str(meta.get("thinking_level", "MEDIUM")).upper()
            if thinking_lvl == "MINIMAL" and model_name == "gemini-3.8-flash":
                thinking_lvl = "LOW"
            gen_config["thinkingConfig"] = {"thinkingLevel": thinking_lvl}
            if request.temperature is not None and request.temperature >= 1.0:
                gen_config["temperature"] = request.temperature
        else:
            if request.temperature is not None:
                gen_config["temperature"] = request.temperature
            if "thinking_budget" in meta:
                gen_config["thinkingConfig"] = {"thinkingBudget": meta["thinking_budget"]}

        if request.max_tokens:
            gen_config["maxOutputTokens"] = request.max_tokens

        payload: dict[str, Any] = {
            "contents": filtered_contents,
            "generationConfig": gen_config
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        service_tier = request.service_tier or meta.get("service_tier")
        if service_tier:
            payload["service_tier"] = service_tier

        timeout = max(self.timeout, 600.0) if service_tier == "flex" else self.timeout

        url = f"/models/{model_name}:generateContent"
        headers = {"X-goog-api-key": self.api_key}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract generated content text
            text = ""
            candidate = {}
            with contextlib.suppress(KeyError, IndexError):
                candidate = data["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]

            usage_dict = data.get("usageMetadata", {})
            prompt_tokens = usage_dict.get("promptTokenCount", 0)
            completion_tokens = usage_dict.get("candidatesTokenCount", 0)
            cached_tokens = usage_dict.get("cachedContentTokenCount", 0)
            total_tokens = usage_dict.get("totalTokenCount", prompt_tokens + completion_tokens)
            tier_header = response.headers.get("x-gemini-service-tier", service_tier or "standard")
            cache_status = f"{'hit' if cached_tokens > 0 else 'miss'}:{tier_header}"

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                total_tokens=total_tokens,
                latency_ms=round(latency_ms, 2),
                cache_status=cache_status
            )

            resp_meta: dict[str, Any] = {"service_tier": tier_header}
            if "groundingMetadata" in candidate:
                gm = candidate["groundingMetadata"]
                resp_meta["grounding_metadata"] = gm
                resp_meta["web_search_queries"] = gm.get("webSearchQueries", [])
                resp_meta["grounding_chunks"] = gm.get("groundingChunks", [])

            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason="stop",
                router_metadata=resp_meta
            )

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        meta = request.router_metadata or {}
        if meta.get("use_interactions_api") or meta.get("stream_interactions"):
            try:
                async for evt in self.stream_interaction(request):
                    evt_type = evt.get("event")
                    data = evt.get("data")
                    if isinstance(data, dict):
                        delta = data.get("delta", {})
                        if evt_type == "step.delta" and delta.get("type") == "text":
                            yield StreamChunk(text=delta.get("text", ""))
                        elif evt_type == "interaction.completed":
                            usage_dict = data.get("interaction", {}).get("usage", {})
                            usage = UsageInfo(
                                prompt_tokens=usage_dict.get("total_input_tokens", 0),
                                completion_tokens=usage_dict.get("total_output_tokens", 0),
                                total_tokens=usage_dict.get("total_tokens", 0),
                                cached_tokens=usage_dict.get("total_cached_tokens", 0),
                                thought_tokens=usage_dict.get("total_thought_tokens", 0),
                                tool_use_tokens=usage_dict.get("total_tool_use_tokens", 0),
                                latency_ms=0.0
                            )
                            yield StreamChunk(text="", usage=usage, finish_reason="stop")
                return
            except Exception:
                # Resilient fallback to complete()
                pass

        # Resilient fallback stream calls to complete yielding all at once,
        # ensuring zero interruptions across both free and paid tier keys.
        res = await self.complete(request)
        yield StreamChunk(text=res.text, usage=res.usage, finish_reason=res.finish_reason)

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        # Gemini structured output can be forced by setting responseMimeType to application/json
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        contents = self._convert_messages(request.messages)

        filtered_contents = [c for c in contents if c["role"] != "system"]
        system_prompt = next((c["parts"] for c in contents if c["role"] == "system"), None)

        model_name = self._resolve_model(request.model)
        gen_config: dict[str, Any] = {
            "responseMimeType": "application/json",
            "responseSchema": schema,
        }
        if model_name != "gemini-3.8-flash" and request.temperature is not None:
            gen_config["temperature"] = request.temperature
        if request.max_tokens:
            gen_config["maxOutputTokens"] = request.max_tokens

        payload = {
            "contents": filtered_contents,
            "generationConfig": gen_config
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": system_prompt}

        url = f"/models/{model_name}:generateContent"
        headers = {"X-goog-api-key": self.api_key}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            text = ""
            with contextlib.suppress(KeyError):
                text = data["candidates"][0]["content"]["parts"][0]["text"]

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

    async def embeddings(self, texts: list[str], model: str = "gemini-embedding-2", output_dim: int = 1536) -> list[list[float]]:
        if not self.api_key:
            return [[0.0] * output_dim for _ in texts]

        url = f"/models/{model}:batchEmbedContents"
        headers = {"X-goog-api-key": self.api_key}
        requests_payload = [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": t}]},
                "outputDimensionality": output_dim
            }
            for t in texts
        ]
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                res = await client.post(url, headers=headers, json={"requests": requests_payload})
                if res.status_code == 200:
                    data = res.json()
                    return [item.get("values", [0.0] * output_dim) for item in data.get("embeddings", [])]
        except Exception:
            pass
        return [[0.0] * output_dim for _ in texts]

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
            url = "/models"
            headers = {"X-goog-api-key": self.api_key}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                is_healthy = response.status_code == 200
                latency = (time.perf_counter() - start) * 1000.0
                error_msg = None
                models = []
                if is_healthy:
                    data = response.json()
                    models = [m.get("name", "").replace("models/", "") for m in data.get("models", []) if "gemini" in m.get("name", "")]
                else:
                    try:
                        error_msg = response.json().get("error", {}).get("message", f"HTTP {response.status_code}")
                    except Exception:
                        error_msg = f"HTTP {response.status_code}"

                return ProviderHealth(
                    provider_name=self.name,
                    is_healthy=is_healthy,
                    active_model="gemini-3.6-flash",
                    circuit_breaker_state="CLOSED",
                    error_count=0 if is_healthy else 1,
                    latency_ms=round(latency, 2),
                    loaded_models=models,
                    last_error=error_msg
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

    def _build_interaction_payload(self, request: CompletionRequest) -> tuple[dict[str, Any], dict[str, str], float]:
        meta = request.router_metadata or {}
        system_instruction = meta.get("system_instruction")
        input_content = []

        for msg in request.messages:
            if msg.role == "system":
                if not system_instruction:
                    system_instruction = msg.content
                continue

            role = "user_input" if msg.role == "user" else "model_output"
            content_parts = []
            if isinstance(msg.content, str):
                content_parts.append({"type": "text", "text": msg.content})
            elif isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, str):
                        content_parts.append({"type": "text", "text": item})
                    elif isinstance(item, dict):
                        item_type = item.get("type", "text")
                        if item_type == "text":
                            content_parts.append({"type": "text", "text": item.get("text", "")})
                        elif item_type in ("image", "image_url"):
                            url_val = item.get("image_url", {}).get("url", "") if item_type == "image_url" else item.get("uri", "")
                            part_dict: dict[str, Any] = {"type": "image"}
                            res = item.get("media_resolution") or meta.get("media_resolution")
                            if res:
                                part_dict["media_resolution"] = res
                            if url_val.startswith("data:"):
                                header, b64_data = url_val.split(",", 1)
                                mime_type = header.split(";")[0].replace("data:", "")
                                part_dict.update({"mime_type": mime_type, "data": b64_data})
                            elif url_val:
                                part_dict.update({"uri": url_val, "mime_type": item.get("mime_type", "image/jpeg")})
                            content_parts.append(part_dict)
                        elif item_type in ("video", "audio", "document"):
                            part_dict = {"type": item_type}
                            res = item.get("media_resolution") or meta.get("media_resolution")
                            if res:
                                part_dict["media_resolution"] = res
                            if "uri" in item:
                                part_dict["uri"] = item["uri"]
                            if "data" in item:
                                part_dict["data"] = item["data"]
                            if "mime_type" in item:
                                part_dict["mime_type"] = item["mime_type"]
                            content_parts.append(part_dict)

            input_content.append({
                "type": role,
                "content": content_parts or [{"type": "text", "text": ""}]
            })

        if "multimodal_parts" in meta:
            for item in meta["multimodal_parts"]:
                if isinstance(item, dict):
                    item_type = item.get("type", "text")
                    if item_type == "text":
                        part_dict = {"type": "text", "text": item.get("text", "")}
                    elif item_type in ("image", "image_url"):
                        url_val = item.get("image_url", {}).get("url", "") if item_type == "image_url" else item.get("uri", "")
                        part_dict = {"type": "image"}
                        res = item.get("media_resolution") or meta.get("media_resolution")
                        if res:
                            part_dict["media_resolution"] = res
                        if url_val.startswith("data:"):
                            header, b64_data = url_val.split(",", 1)
                            mime_type = header.split(";")[0].replace("data:", "")
                            part_dict.update({"mime_type": mime_type, "data": b64_data})
                        elif url_val:
                            part_dict.update({"uri": url_val, "mime_type": item.get("mime_type", "image/jpeg")})
                    elif item_type in ("video", "audio", "document"):
                        part_dict = {"type": item_type}
                        res = item.get("media_resolution") or meta.get("media_resolution")
                        if res:
                            part_dict["media_resolution"] = res
                        if "uri" in item:
                            part_dict["uri"] = item["uri"]
                        if "data" in item:
                            part_dict["data"] = item["data"]
                        if "mime_type" in item:
                            part_dict["mime_type"] = item["mime_type"]
                    else:
                        part_dict = item

                    if input_content and input_content[-1]["type"] == "user_input":
                        input_content[-1]["content"].append(part_dict)
                    else:
                        input_content.append({"type": "user_input", "content": [part_dict]})

        model_name = self._resolve_model(request.model)
        payload: dict[str, Any] = {
            "model": model_name,
            "input": input_content,
            "store": meta.get("store", True)
        }
        if system_instruction:
            payload["system_instruction"] = system_instruction
        if "previous_interaction_id" in meta:
            payload["previous_interaction_id"] = meta["previous_interaction_id"]
        if "background" in meta:
            payload["background"] = meta["background"]
        if "agent" in meta:
            payload["agent"] = meta["agent"]
        if "agent_config" in meta:
            payload["agent_config"] = meta["agent_config"]
        if "environment" in meta:
            payload["environment"] = meta["environment"]
        if request.tools:
            tools_list = []
            for t in request.tools:
                if isinstance(t, dict):
                    if t.get("type") in ("function", "mcp_server", "google_search", "url_context", "code_execution"):
                        tools_list.append(t)
                    elif "function" in t:
                        fn = t["function"]
                        tools_list.append({
                            "type": "function",
                            "name": fn.get("name"),
                            "description": fn.get("description", ""),
                            "parameters": fn.get("parameters", {})
                        })
                    else:
                        tools_list.append(t)
            if tools_list:
                payload["tools"] = tools_list
        elif "tools" in meta:
            payload["tools"] = meta["tools"]

        if "response_format" in meta:
            payload["response_format"] = meta["response_format"]
        elif request.response_format:
            payload["response_format"] = request.response_format

        # Generation Config for Interactions
        gen_config: dict[str, Any] = {}
        if "thinking_level" in meta:
            thinking_lvl = str(meta["thinking_level"]).lower()
            if thinking_lvl == "minimal" and model_name == "gemini-3.8-flash":
                thinking_lvl = "low"
            gen_config["thinking_level"] = thinking_lvl
        elif model_name.startswith("gemini-3."):
            gen_config["thinking_level"] = "medium"

        if request.temperature is not None and not model_name.startswith("gemini-3."):
            gen_config["temperature"] = request.temperature

        if gen_config:
            payload["generation_config"] = gen_config

        service_tier = request.service_tier or meta.get("service_tier")
        if service_tier:
            payload["service_tier"] = service_tier
        if "webhook_config" in meta:
            payload["webhook_config"] = meta["webhook_config"]

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
            "Api-Revision": "2026-05-20"
        }

        timeout = max(self.timeout, 600.0) if service_tier == "flex" else self.timeout
        return payload, headers, timeout

    async def interact(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a stateful or stateless turn using Gemini Interactions API (/v1beta/interactions).
        
        Falls back seamlessly to complete() if the endpoint returns an error or is unauthenticated.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        start_time = time.perf_counter()
        meta = request.router_metadata or {}
        payload, headers, timeout = self._build_interaction_payload(request)
        model_name = payload["model"]
        service_tier = request.service_tier or meta.get("service_tier")
        url = f"{self.base_url}/interactions"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0
                    
                    text = ""
                    tool_calls: list[ToolCall] = []
                    thought_summary = []
                    thought_signatures = []
                    search_queries = []
                    search_suggestions = []
                    code_executions = []
                    code_results = []
                    url_context_results = []
                    citations = []
                    safety_decisions = []

                    for step in data.get("steps", []):
                        step_type = step.get("type")
                        if step_type == "model_output":
                            for c in step.get("content", []):
                                if c.get("type") == "text":
                                    text += c.get("text", "")
                                if "annotations" in c:
                                    citations.extend(c.get("annotations", []))
                        elif step_type == "function_call":
                            call_id = step.get("id") or f"call_{len(tool_calls)}"
                            fn_name = step.get("name", "")
                            fn_args = step.get("arguments", {})
                            if isinstance(fn_args, dict) and "safety_decision" in fn_args:
                                safety_decisions.append(fn_args["safety_decision"])
                            arg_str = json.dumps(fn_args) if isinstance(fn_args, dict) else str(fn_args)
                            tool_calls.append(ToolCall(
                                id=call_id,
                                type="function",
                                name=fn_name,
                                arguments=arg_str
                            ))
                        elif step_type == "thought":
                            if step.get("signature"):
                                thought_signatures.append(step["signature"])
                            if step.get("summary"):
                                thought_summary.extend(step.get("summary"))
                        elif step_type == "google_search_call":
                            args = step.get("arguments", {})
                            search_queries.extend(args.get("queries", []))
                        elif step_type == "google_search_result":
                            for res in step.get("result", []):
                                if "search_suggestions" in res:
                                    search_suggestions.append(res["search_suggestions"])
                        elif step_type == "code_execution_call":
                            args = step.get("arguments", {})
                            if "code" in args:
                                code_executions.append(args["code"])
                        elif step_type == "code_execution_result":
                            if "result" in step:
                                code_results.append(step["result"])
                        elif step_type == "url_context_result":
                            url_context_results.append(step)
                        elif step_type == "safety_decision":
                            safety_decisions.append(step)
                    
                    usage_dict = data.get("usage", {})
                    prompt_tokens = usage_dict.get("total_input_tokens", 0)
                    completion_tokens = usage_dict.get("total_output_tokens", 0)
                    cached_tokens = usage_dict.get("total_cached_tokens", 0)
                    thought_tokens = usage_dict.get("total_thought_tokens", 0)
                    tool_use_tokens = usage_dict.get("total_tool_use_tokens", 0)
                    total_tokens = usage_dict.get("total_tokens", prompt_tokens + completion_tokens)
                    tier_header = response.headers.get("x-gemini-service-tier", service_tier or "standard")
                    cache_status = f"{'hit' if cached_tokens > 0 else 'miss'}:{tier_header}"

                    usage = UsageInfo(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cached_tokens=cached_tokens,
                        thought_tokens=thought_tokens,
                        tool_use_tokens=tool_use_tokens,
                        total_tokens=total_tokens,
                        latency_ms=round(latency_ms, 2),
                        cache_status=cache_status
                    )
                    
                    resp_meta = {
                        "interaction_id": data.get("id"),
                        "environment_id": data.get("environment_id"),
                        "service_tier": tier_header,
                        "status": data.get("status"),
                        "steps": data.get("steps", []),
                        "thought_summary": thought_summary,
                        "thought_signatures": thought_signatures,
                        "search_queries": search_queries,
                        "search_suggestions": search_suggestions,
                        "code_executions": code_executions,
                        "code_results": code_results,
                        "url_context_results": url_context_results,
                        "citations": citations,
                        "safety_decisions": safety_decisions
                    }
                    finish_reason = "tool_calls" if tool_calls else "stop"
                    return CompletionResponse(
                        text=text,
                        usage=usage,
                        provider=self.name,
                        model=model_name,
                        finish_reason=finish_reason,
                        tool_calls=tool_calls or None,
                        router_metadata=resp_meta
                    )
        except Exception:
            pass

        return await self.complete(request)

    async def get_interaction(self, interaction_id: str) -> dict[str, Any]:
        """Retrieve interaction state or background execution result."""
        url = f"{self.base_url}/interactions/{interaction_id}"
        headers = {
            "x-goog-api-key": self.api_key,
            "Api-Revision": "2026-05-20"
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def cancel_interaction(self, interaction_id: str) -> dict[str, Any]:
        """Cancel an in-progress background interaction."""
        url = f"{self.base_url}/interactions/{interaction_id}:cancel"
        headers = {
            "x-goog-api-key": self.api_key,
            "Api-Revision": "2026-05-20"
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    # Environments API (Managed Linux Sandboxes)
    async def list_environments(self, page_size: int = 10, page_token: str | None = None) -> dict[str, Any]:
        """List active sandboxed environments for the current project."""
        url = f"{self.base_url}/environments"
        params: dict[str, Any] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_environment(self, environment_id: str) -> dict[str, Any]:
        """Get configuration and status of a sandboxed environment."""
        url = f"{self.base_url}/environments/{environment_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_environment(self, environment_id: str) -> bool:
        """Explicitly terminate and delete an environment sandbox."""
        url = f"{self.base_url}/environments/{environment_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    async def download_environment_snapshot(self, environment_id: str) -> bytes:
        """Download an environment snapshot as a tar archive."""
        url = f"{self.base_url}/files/environment-{environment_id}:download"
        headers = {"x-goog-api-key": self.api_key}
        params = {"alt": "media"}
        async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
            resp = await client.get(url, headers=headers, params=params, follow_redirects=True)
            resp.raise_for_status()
            return resp.content

    # Managed Agents API (/v1beta/agents)
    async def create_agent(
        self,
        agent_id: str,
        base_agent: str = "antigravity-preview-05-2026",
        agent_config: dict[str, Any] | None = None,
        system_instruction: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        base_environment: Any = None
    ) -> dict[str, Any]:
        """Create and save a reusable managed agent definition."""
        url = f"{self.base_url}/agents"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload: dict[str, Any] = {
            "id": agent_id,
            "base_agent": base_agent
        }
        if agent_config:
            payload["agent_config"] = agent_config
        if system_instruction:
            payload["system_instruction"] = system_instruction
        if tools:
            payload["tools"] = tools
        if base_environment:
            payload["base_environment"] = base_environment

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_agents(self) -> list[dict[str, Any]]:
        """List all saved managed agents."""
        url = f"{self.base_url}/agents"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("agents", [])

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Retrieve a saved managed agent configuration."""
        url = f"{self.base_url}/agents/{agent_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete a saved managed agent configuration."""
        url = f"{self.base_url}/agents/{agent_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    # Triggers API (/v1beta/triggers)
    async def create_trigger(
        self,
        schedule: str,
        time_zone: str,
        interaction: dict[str, Any],
        display_name: str | None = None,
        max_consecutive_failures: int = 5,
        execution_timeout_seconds: int = 600
    ) -> dict[str, Any]:
        """Create a scheduled cron trigger for an autonomous agent."""
        url = f"{self.base_url}/triggers"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload: dict[str, Any] = {
            "schedule": schedule,
            "time_zone": time_zone,
            "interaction": interaction,
            "max_consecutive_failures": max_consecutive_failures,
            "execution_timeout_seconds": execution_timeout_seconds
        }
        if display_name:
            payload["display_name"] = display_name

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_triggers(self) -> list[dict[str, Any]]:
        """List all project triggers."""
        url = f"{self.base_url}/triggers"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("triggers", [])

    async def get_trigger(self, trigger_id: str) -> dict[str, Any]:
        """Fetch status and configuration for a trigger."""
        url = f"{self.base_url}/triggers/{trigger_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def update_trigger(self, trigger_id: str, status: str) -> dict[str, Any]:
        """Pause or resume a trigger (status: 'active' or 'paused')."""
        url = f"{self.base_url}/triggers/{trigger_id}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.patch(url, headers=headers, json={"status": status})
            resp.raise_for_status()
            return resp.json()

    async def delete_trigger(self, trigger_id: str) -> bool:
        """Permanently delete a trigger."""
        url = f"{self.base_url}/triggers/{trigger_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    async def run_trigger(self, trigger_id: str) -> dict[str, Any]:
        """Trigger an immediate execution of a scheduled agent on demand."""
        url = f"{self.base_url}/triggers/{trigger_id}/executions"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def list_trigger_executions(self, trigger_id: str) -> list[dict[str, Any]]:
        """Retrieve execution history for a trigger."""
        url = f"{self.base_url}/triggers/{trigger_id}/executions"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("trigger_executions", [])

    @staticmethod
    def generate_hooks_config(
        command_deny_patterns: list[str] | None = None,
        http_telemetry_url: str | None = None
    ) -> dict[str, Any]:
        """Generate a valid RE2-compliant .agents/hooks.json structure."""
        hooks_config: dict[str, Any] = {}
        
        if command_deny_patterns:
            hooks_config["security-gate"] = {
                "enabled": True,
                "pre_tool_execution": [
                    {
                        "matcher": "code_execution",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 /.agents/hooks-scripts/gate.py",
                                "timeout": 10
                            }
                        ]
                    }
                ]
            }
            
        if http_telemetry_url:
            hooks_config["audit-telemetry"] = {
                "enabled": True,
                "post_tool_execution": [
                    {
                        "matcher": ".*_file|code_execution",
                        "hooks": [
                            {
                                "type": "http",
                                "url": http_telemetry_url,
                                "timeout": 10
                            }
                        ]
                    }
                ]
            }

        return hooks_config

    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=True,
            reasoning=True,
            context_window=1048576
        )

    @staticmethod
    def parse_bounding_boxes(boxes: list[dict[str, Any]], image_width: int, image_height: int) -> list[dict[str, Any]]:
        """Convert normalized [0, 1000] bounding boxes from Gemini 3 vision into pixel coordinates."""
        results = []
        for b in boxes:
            box_2d = b.get("box_2d", [])
            if len(box_2d) == 4:
                ymin, xmin, ymax, xmax = box_2d
                results.append({
                    "label": b.get("label", ""),
                    "box_pixel": [
                        round((ymin / 1000.0) * image_height),
                        round((xmin / 1000.0) * image_width),
                        round((ymax / 1000.0) * image_height),
                        round((xmax / 1000.0) * image_width)
                    ]
                })
        return results

    @staticmethod
    def parse_segmentation_masks(masks: list[dict[str, Any]], image_width: int, image_height: int) -> list[dict[str, Any]]:
        """Convert normalized [0, 1000] polygon segmentation masks from Gemini 3 into pixel coordinates."""
        results = []
        for m in masks:
            raw_mask = m.get("mask", [])
            scaled_polygon = [
                [round((pt[0] / 1000.0) * image_width), round((pt[1] / 1000.0) * image_height)]
                for pt in raw_mask if len(pt) >= 2
            ]
            results.append({
                "label": m.get("label", ""),
                "mask_polygon": scaled_polygon
            })
        return results

    @staticmethod
    def denormalize_coordinates(x: int, y: int, screen_width: int, screen_height: int) -> tuple[int, int]:
        """Convert normalized (0-1000) Computer Use coordinates to actual screen pixels."""
        pixel_x = int(round((x / 1000.0) * screen_width))
        pixel_y = int(round((y / 1000.0) * screen_height))
        return pixel_x, pixel_y

    @staticmethod
    def normalize_coordinates(actual_x: int, actual_y: int, screen_width: int, screen_height: int) -> tuple[int, int]:
        """Convert screen pixels to normalized (0-1000) Computer Use coordinates."""
        norm_x = int(round((actual_x / float(screen_width)) * 1000.0))
        norm_y = int(round((actual_y / float(screen_height)) * 1000.0))
        return norm_x, norm_y

    # FileSearchStores API (Managed Multimodal RAG)
    async def create_file_search_store(
        self,
        display_name: str,
        embedding_model: str = "models/gemini-embedding-2"
    ) -> dict[str, Any]:
        """Create a persistent File Search store for document embeddings."""
        url = f"{self.base_url}/fileSearchStores"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload = {
            "displayName": display_name,
            "embeddingModel": embedding_model
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_file_search_stores(self) -> list[dict[str, Any]]:
        """List all project File Search stores."""
        url = f"{self.base_url}/fileSearchStores"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("fileSearchStores", [])

    async def get_file_search_store(self, store_name: str) -> dict[str, Any]:
        """Get details for a specific File Search store."""
        url = f"{self.base_url}/fileSearchStores/{store_name}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_file_search_store(self, store_name: str, force: bool = True) -> bool:
        """Delete a File Search store and its indexed embeddings."""
        url = f"{self.base_url}/fileSearchStores/{store_name}"
        headers = {"x-goog-api-key": self.api_key}
        params = {"force": str(force).lower()}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers, params=params)
            return resp.status_code in (200, 204)

    async def download_media(self, media_id: str) -> bytes:
        """Download an image or media chunk cited in File Search annotations."""
        url = f"{self.base_url}/{media_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.content

    # Live API & Real-time WebSockets
    async def create_ephemeral_token(
        self,
        ttl_seconds: int = 1800,
        model: str = "gemini-3.1-flash-live-preview",
        config: dict[str, Any] | None = None,
        uses: int = 1
    ) -> dict[str, Any]:
        """Mint a short-lived scoped ephemeral token for client-to-server WebSockets."""
        url = f"{self.base_url}/auth_tokens"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        expire_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=ttl_seconds)).isoformat()
        resolved_model = self._resolve_model(model)
        live_constraints: dict[str, Any] = {"model": f"models/{resolved_model}"}
        if config:
            live_constraints["config"] = config

        payload = {
            "uses": uses,
            "expireTime": expire_time,
            "liveConnectConstraints": live_constraints
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    def get_live_websocket_url(self, api_key_or_token: str | None = None, is_ephemeral: bool = False) -> str:
        """Construct the Gemini Live WebSocket endpoint URL."""
        auth_val = api_key_or_token or self.api_key
        if is_ephemeral:
            return f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained?access_token={auth_val}"
        return f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={auth_val}"

    def build_live_setup_message(
        self,
        model: str = "gemini-3.1-flash-live-preview",
        voice_name: str = "Puck",
        response_modalities: list[str] | None = None,
        thinking_level: str = "medium",
        system_instruction: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        context_compression_trigger: int | None = None,
        session_resumption_handle: str | None = None
    ) -> dict[str, Any]:
        """Construct a validated BidiGenerateContentSetup message for the Live API."""
        resolved_model = self._resolve_model(model)
        setup: dict[str, Any] = {
            "model": f"models/{resolved_model}",
            "generationConfig": {
                "responseModalities": response_modalities or ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                },
                "thinkingConfig": {"thinkingLevel": thinking_level}
            }
        }
        if system_instruction:
            setup["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if tools:
            setup["tools"] = tools
        if context_compression_trigger:
            setup["contextWindowCompression"] = {
                "triggerTokens": context_compression_trigger,
                "targetTokens": int(context_compression_trigger / 2)
            }
        if session_resumption_handle:
            setup["sessionResumption"] = {"handle": session_resumption_handle}

        return {"setup": setup}

    @staticmethod
    def format_realtime_audio_chunk(pcm_bytes: bytes, rate: int = 16000) -> dict[str, Any]:
        """Encode 16-bit PCM little-endian audio into a BidiGenerateContentRealtimeInput frame."""
        encoded = base64.b64encode(pcm_bytes).decode("utf-8")
        return {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": f"audio/pcm;rate={rate}",
                        "data": encoded
                    }
                ]
            }
        }

    @staticmethod
    def format_realtime_video_frame(frame_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
        """Encode a JPEG/PNG video frame into a BidiGenerateContentRealtimeInput frame."""
        encoded = base64.b64encode(frame_bytes).decode("utf-8")
        return {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": mime_type,
                        "data": encoded
                    }
                ]
            }
        }

    @staticmethod
    def format_realtime_stream_end() -> dict[str, Any]:
        """Format an audioStreamEnd signal for Hybrid Voice Activity Detection."""
        return {
            "realtimeInput": {
                "audioStreamEnd": True
            }
        }

    @staticmethod
    def format_live_tool_response(
        call_id: str,
        name: str,
        result: Any,
        scheduling: str | None = None
    ) -> dict[str, Any]:
        """Format a FunctionResponse frame for the Live API with optional scheduling (INTERRUPT/WHEN_IDLE/SILENT)."""
        resp_payload: dict[str, Any] = {"result": result}
        if scheduling:
            resp_payload["scheduling"] = scheduling
        return {
            "toolResponse": {
                "functionResponses": [
                    {
                        "id": call_id,
                        "name": name,
                        "response": resp_payload
                    }
                ]
            }
        }

    # Asynchronous Batch API (/v1beta/batches)
    async def create_batch_job(
        self,
        model: str,
        dataset_file_uri: str | None = None,
        inline_requests: list[dict[str, Any]] | None = None,
        display_name: str | None = None
    ) -> dict[str, Any]:
        """Submit a 50% discounted asynchronous batch job (inline <20MB or File API <=2GB)."""
        url = f"{self.base_url}/batches"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        resolved_model = self._resolve_model(model)
        payload: dict[str, Any] = {"model": f"models/{resolved_model}"}
        if display_name:
            payload["displayName"] = display_name
        if dataset_file_uri:
            payload["dataset"] = {"fileUri": dataset_file_uri}
        elif inline_requests:
            payload["dataset"] = {"requests": inline_requests}
        else:
            raise ValueError("Either dataset_file_uri or inline_requests must be provided.")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_batch_job(self, batch_name: str) -> dict[str, Any]:
        """Fetch status and metadata for a batch job (states: PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED, EXPIRED)."""
        clean_name = batch_name.lstrip("/")
        url = f"{self.base_url}/{clean_name}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def list_batch_jobs(self, page_size: int = 10, page_token: str | None = None) -> list[dict[str, Any]]:
        """List recent batch jobs for the project."""
        url = f"{self.base_url}/batches"
        headers = {"x-goog-api-key": self.api_key}
        params: dict[str, Any] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("batches", [])

    async def cancel_batch_job(self, batch_name: str) -> dict[str, Any]:
        """Cancel an ongoing batch job."""
        clean_name = batch_name.lstrip("/")
        url = f"{self.base_url}/{clean_name}:cancel"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_batch_job(self, batch_name: str) -> bool:
        """Permanently delete a completed or failed batch job record."""
        clean_name = batch_name.lstrip("/")
        url = f"{self.base_url}/{clean_name}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    # Webhooks API (Static Project-Level)
    async def create_static_webhook(
        self,
        name: str,
        uri: str,
        subscribed_events: list[str]
    ) -> dict[str, Any]:
        """Register a static project-level webhook endpoint."""
        url = f"{self.base_url.replace('/v1beta', '/v1')}/webhooks"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload = {
            "name": name,
            "uri": uri,
            "subscribed_events": subscribed_events
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def list_static_webhooks(self) -> list[dict[str, Any]]:
        """List registered static webhooks."""
        url = f"{self.base_url.replace('/v1beta', '/v1')}/webhooks"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("webhooks", [])

    async def get_static_webhook(self, webhook_id: str) -> dict[str, Any]:
        """Fetch details for a registered webhook."""
        url = f"{self.base_url.replace('/v1beta', '/v1')}/webhooks/{webhook_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_static_webhook(self, webhook_id: str) -> bool:
        """Delete a registered webhook endpoint."""
        url = f"{self.base_url.replace('/v1beta', '/v1')}/webhooks/{webhook_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    async def rotate_static_webhook_secret(
        self,
        webhook_id: str,
        revocation_behavior: str = "REVOKE_PREVIOUS_SECRETS_AFTER_H24"
    ) -> dict[str, Any]:
        """Rotate the signing secret for a webhook."""
        url = f"{self.base_url.replace('/v1beta', '/v1')}/webhooks/{webhook_id}/rotate_secret"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload = {"revocation_behavior": revocation_behavior}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def verify_static_webhook(
        raw_body: bytes,
        webhook_id: str,
        webhook_timestamp: str,
        webhook_signature: str,
        secret: str,
        max_drift_seconds: int = 300
    ) -> bool:
        """Verify Standard Webhooks HMAC-SHA256 signature with replay window validation."""
        now = int(time.time())
        try:
            ts = int(webhook_timestamp)
        except (ValueError, TypeError):
            return False

        if abs(now - ts) > max_drift_seconds:
            return False  # Replay attack protection (rejected if > 5 minutes old)

        signature_payload = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + raw_body
        expected = hmac.new(secret.encode("utf-8"), signature_payload, hashlib.sha256).digest()
        expected_b64 = base64.b64encode(expected).decode("utf-8")

        for sig in webhook_signature.split(" "):
            parts = sig.split(",", 1)
            if len(parts) == 2 and parts[0] == "v1":
                if hmac.compare_digest(parts[1], expected_b64):
                    return True
            elif hmac.compare_digest(sig, expected_b64):
                return True
        return False

    async def stream_interaction(
        self,
        request: CompletionRequest,
        last_event_id: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream an interaction turn using Server-Sent Events (SSE).
        
        Yields structured SSE event dictionaries (event, data, id).
        Supports seamless resumption via last_event_id.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        payload, headers, timeout = self._build_interaction_payload(request)
        payload["stream"] = True

        url = f"{self.base_url}/interactions"
        if last_event_id:
            url += f"?last_event_id={last_event_id}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                current_event = "message"
                current_id = None
                data_lines: list[str] = []

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        if data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = raw_data
                            yield {
                                "event": current_event,
                                "data": parsed,
                                "id": current_id
                            }
                            data_lines = []
                            current_event = "message"
                        continue

                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line.split(":", 1)[1].strip())
                    elif line.startswith("id:"):
                        current_id = line.split(":", 1)[1].strip()

                if data_lines:
                    raw_data = "\n".join(data_lines)
                    try:
                        parsed = json.loads(raw_data)
                    except Exception:
                        parsed = raw_data
                    yield {
                        "event": current_event,
                        "data": parsed,
                        "id": current_id
                    }

    async def get_interaction(self, interaction_id: str) -> dict[str, Any]:
        """Retrieve an interaction resource and its step history."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        url = f"{self.base_url}/interactions/{interaction_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def cancel_interaction(self, interaction_id: str) -> dict[str, Any]:
        """Cancel an in-flight background or long-running interaction."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        url = f"{self.base_url}/interactions/{interaction_id}:cancel"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def delete_interaction(self, interaction_id: str) -> dict[str, Any]:
        """Purge an interaction session and server-side state."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        url = f"{self.base_url}/interactions/{interaction_id}"
        headers = {"x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def register_gcs_file(
        self,
        uri: str,
        mime_type: str,
        display_name: str | None = None
    ) -> dict[str, Any]:
        """Register a Google Cloud Storage file (gs://) directly with the Gemini File API.
        
        Enables zero-download/zero-upload instant referencing of large cloud datasets
        using the Gemini Service Agent IAM permissions.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        url = f"{self.base_url}/files:register"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        file_obj: dict[str, Any] = {"uri": uri, "mime_type": mime_type}
        if display_name:
            file_obj["display_name"] = display_name
        payload = {"file": file_obj}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def format_agentic_prompt(
        task: str,
        role: str | None = None,
        constraints: list[str] | None = None,
        context: str | None = None,
        output_format: str | None = None,
        anchor_2026: bool = True
    ) -> str:
        """Format an agentic prompt according to Gemini 3 structured XML best practices.
        
        Includes optional 2026 calendar anchoring and knowledge cutoff rules.
        """
        parts = []
        if role:
            parts.append(f"<role>\n{role.strip()}\n</role>")
        
        constraint_items = list(constraints or [])
        if anchor_2026:
            constraint_items.append("For time-sensitive queries, remember it is 2026 this year. Your knowledge cutoff is January 2025.")
        if constraint_items:
            formatted_constraints = "\n".join(f"- {c}" for c in constraint_items)
            parts.append(f"<constraints>\n{formatted_constraints}\n</constraints>")

        if context:
            parts.append(f"<context>\n{context.strip()}\n</context>")

        parts.append(f"<task>\n{task.strip()}\n</task>")

        if output_format:
            parts.append(f"<output_format>\n{output_format.strip()}\n</output_format>")

        return "\n\n".join(parts)
