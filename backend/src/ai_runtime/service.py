from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from src.ai_runtime.context import ConversationContextManager
from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    ProviderHealth,
    StreamChunk,
)
from src.ai_runtime.registry import ProviderRegistry

logger = structlog.get_logger(__name__)

class AIRuntimeService:
    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.context_manager = ConversationContextManager()

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        logger.info("RequestStarted", model=request.model, temperature=request.temperature)

        router_reason = None
        is_auto = request.model == "auto-router"
        if is_auto:
            from src.ai_runtime.router import auto_router
            prompt_text = "".join(m.content for m in request.messages if m.content)
            has_tools = bool(request.tool_callables) or bool(request.tools)
            decision = auto_router.route(prompt_text, has_tools, request.research_mode)
            request.model = decision["model"]
            router_reason = decision["reason"]
            logger.info("AutoRouterDecision", model=request.model, reason=router_reason)

        last_error = None
        
        while True:
            chain = self.registry.get_priority_chain(request.model)
            model_success = False

            # Diagnostic logging: key_present booleans in priority order
            key_status_str = ", ".join(f"{p}:key_present={self.registry.is_key_present(p)}" for p in self.registry.priority)
            logger.info("AI Provider priority key check", key_statuses=key_status_str)

            primary_name = self.registry.resolve_provider_for_model(request.model)

            for idx, provider in enumerate(chain):
                breaker = self.registry.get_breaker(provider.name)
                reason = "priority[0]" if provider.name == primary_name and (self.registry.priority and self.registry.priority[0] == primary_name) else (f"model_match({request.model})" if provider.name == primary_name else f"priority_fallback[{idx}]")
                logger.info(f"Provider resolved: provider={provider.name}, reason={reason}")
                logger.info("ProviderSelected", provider=provider.name, model=request.model, reason=reason)

                cap = provider.get_capability_matrix()
                self.context_manager.token_budget = cap.context_window
                trimmed_messages = self.context_manager.trim_messages(request.messages)

                trimmed_request = CompletionRequest(
                    messages=trimmed_messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    response_format=request.response_format
                )

                for attempt in range(1, 3):
                    try:
                        current_request = trimmed_request
                        max_iterations = 10
                        iterations = 0
                        
                        while iterations < max_iterations:
                            iterations += 1
                            res = await provider.complete(current_request)
                            
                            if res.finish_reason == "tool_calls" and res.tool_calls:
                                import json
                                import inspect
                                
                                from src.ai_runtime.contracts import Message
                                assistant_msg = Message(role="assistant", content=res.text or "", tool_calls=[tc.model_dump() for tc in res.tool_calls])
                                current_request.messages.append(assistant_msg)
                                
                                for tool_call in res.tool_calls:
                                    if tool_call.name.startswith("openrouter:"):
                                        continue
                                        
                                    tool_result_str = ""
                                    try:
                                        args = json.loads(tool_call.arguments)
                                        if current_request.tool_callables and tool_call.name in current_request.tool_callables:
                                            func = current_request.tool_callables[tool_call.name]
                                            if inspect.iscoroutinefunction(func):
                                                tool_result = await func(**args)
                                            else:
                                                tool_result = func(**args)
                                            tool_result_str = json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result
                                        else:
                                            tool_result_str = json.dumps({"error": f"Tool '{tool_call.name}' not found locally"})
                                    except Exception as e:
                                        tool_result_str = json.dumps({"error": str(e)})
                                    
                                    tool_msg = Message(role="tool", content=tool_result_str, tool_call_id=tool_call.id)
                                    current_request.messages.append(tool_msg)
                                
                                continue
                                
                            if breaker:
                                breaker.record_success()
                                
                            if is_auto:
                                auto_router.record_success(request.model)

                            logger.info(
                                "UsageCollected",
                                provider=provider.name,
                                model=request.model,
                                prompt_tokens=res.usage.prompt_tokens,
                                completion_tokens=res.usage.completion_tokens,
                                total_tokens=res.usage.total_tokens,
                                latency_ms=res.usage.latency_ms
                            )
                            if router_reason:
                                res.router_reason = router_reason
                            return res
                    except Exception as exc:
                        logger.warning(
                            "RetryAttempt",
                            provider=provider.name,
                            attempt=attempt,
                            exception_type=type(exc).__name__,
                            error=str(exc)
                        )
                        last_error = exc
                        import time
                        time.sleep(0.1)

                if breaker:
                    breaker.record_failure(last_error)
                    
                error_msg = str(last_error)
                if not error_msg and type(last_error).__name__ == "ReadTimeout":
                    error_msg = "Connection timed out"
                    
                logger.warning(
                    "Failover",
                    provider=provider.name,
                    exception_type=type(last_error).__name__ if last_error else "None",
                    error=error_msg,
                )
                
                # If AutoRouter is active, check if we tripped the model circuit breaker
                if is_auto:
                    is_429 = "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower() or "quota" in error_msg.lower()
                    tripped = auto_router.record_failure(request.model, is_429)
                    if tripped:
                        decision = auto_router.route(prompt_text, has_tools, request.research_mode)
                        new_model = decision["model"]
                        if new_model != request.model:
                            router_reason = f"Switched to {new_model} due to rate limits. " + decision["reason"]
                            logger.warn(f"AutoRouter switched from {request.model} to {new_model} due to rate limits")
                            request.model = new_model
                            # Break the provider loop to restart the chain logic with the new model
                            break 
            else:
                # If we exhausted the provider chain WITHOUT breaking (which means no AutoRouter model switch happened)
                break
                
        logger.error("RuntimeError", error="All providers in priority chain failed")
        
        error_msg = str(last_error) if last_error else "Unknown error"
        if last_error and not str(last_error) and type(last_error).__name__ == "ReadTimeout":
            error_msg = "Connection timed out"
            
        raise RuntimeError(f"AI runtime failed to process request. All providers exhausted. Last error: {error_msg}") from last_error

    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        logger.info("RequestStarted", model=request.model, streaming=True)

        chain = self.registry.get_priority_chain(request.model)
        last_error = None

        for provider in chain:
            breaker = self.registry.get_breaker(provider.name)
            logger.info("ProviderSelected", provider=provider.name, model=request.model)
            logger.info("StreamStarted", provider=provider.name)

            # Auto fallback context trimming based on provider capabilities window
            cap = provider.get_capability_matrix()
            self.context_manager.token_budget = cap.context_window
            trimmed_messages = self.context_manager.trim_messages(request.messages)

            trimmed_request = CompletionRequest(
                messages=trimmed_messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format
            )

            try:
                async for chunk in provider.stream(trimmed_request):
                    yield chunk

                if breaker:
                    breaker.record_success()
                logger.info("StreamFinished", provider=provider.name)
                return
            except Exception as exc:
                if breaker:
                    breaker.record_failure(exc)
                logger.warn("Failover", provider=provider.name, error=str(exc))
                last_error = exc

        logger.error("RuntimeError", error="All providers failed during stream initialization")
        raise RuntimeError("AI runtime stream failed.") from last_error

    async def complete_structured(self, request: CompletionRequest, schema: dict[str, Any]) -> CompletionResponse:
        logger.info("RequestStarted", model=request.model, structured=True)

        router_reason = None
        if request.model == "auto-router":
            from src.ai_runtime.router import auto_router
            prompt_text = "".join(m.content for m in request.messages if m.content)
            has_tools = bool(request.tool_callables) or bool(request.tools)
            decision = auto_router.route(prompt_text, has_tools, request.research_mode)
            request.model = decision["model"]
            router_reason = decision["reason"]
            logger.info("AutoRouterDecision", model=request.model, reason=router_reason)

        chain = self.registry.get_priority_chain(request.model)
        last_error = None

        for provider in chain:
            breaker = self.registry.get_breaker(provider.name)
            logger.info("ProviderSelected", provider=provider.name, model=request.model)

            # Auto fallback context trimming based on provider capabilities window
            cap = provider.get_capability_matrix()
            self.context_manager.token_budget = cap.context_window
            trimmed_messages = self.context_manager.trim_messages(request.messages)

            trimmed_request = CompletionRequest(
                messages=trimmed_messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format
            )

            for attempt in range(1, 3):
                try:
                    res = await provider.complete_structured(trimmed_request, schema)
                    if breaker:
                        breaker.record_success()
                    logger.info("UsageCollected", provider=provider.name, total_tokens=res.usage.total_tokens)
                    if router_reason:
                        res.router_reason = router_reason
                    return res
                except Exception as exc:
                    logger.warn("RetryAttempt", provider=provider.name, attempt=attempt, error=str(exc))
                    last_error = exc
                    time.sleep(0.1)

            if breaker:
                breaker.record_failure(last_error)
            logger.warn("Failover", provider=provider.name, error=str(last_error))

        logger.error("RuntimeError", error="All providers in priority chain failed structured completion")
        raise RuntimeError("AI runtime structured output failed.") from last_error

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        # Default embeddings selects the first healthy provider supporting embeddings
        chain = self.registry.get_priority_chain("default")
        for provider in chain:
            cap = provider.get_capability_matrix()
            if cap.embeddings:
                try:
                    return await provider.embeddings(texts)
                except Exception:
                    continue
        # Fallback empty vectors
        return [[0.0] * 1536 for _ in texts]

    async def check_health(self) -> list[ProviderHealth]:
        statuses = []
        for name, provider in self.registry.providers.items():
            status = await provider.check_health()
            breaker = self.registry.get_breaker(name)
            if breaker:
                status.circuit_breaker_state = breaker.state
                status.error_count = breaker.consecutive_failures
                status.last_error = breaker.last_error
            statuses.append(status)
        return statuses
