from __future__ import annotations
import structlog
import time
from typing import AsyncGenerator, Dict, Any, List
from src.ai_runtime.contracts import (
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    ProviderHealth,
)
from src.ai_runtime.registry import ProviderRegistry
from src.ai_runtime.context import ConversationContextManager

logger = structlog.get_logger(__name__)

class AIRuntimeService:
    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.context_manager = ConversationContextManager()

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        logger.info("RequestStarted", model=request.model, temperature=request.temperature)
        
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

            # Execution attempt with retries
            for attempt in range(1, 3):
                try:
                    res = await provider.complete(trimmed_request)
                    if breaker:
                        breaker.record_success()
                    
                    logger.info(
                        "UsageCollected",
                        provider=provider.name,
                        model=request.model,
                        prompt_tokens=res.usage.prompt_tokens,
                        completion_tokens=res.usage.completion_tokens,
                        total_tokens=res.usage.total_tokens,
                        latency_ms=res.usage.latency_ms
                    )
                    return res
                except Exception as exc:
                    logger.warn(
                        "RetryAttempt",
                        provider=provider.name,
                        attempt=attempt,
                        error=str(exc)
                    )
                    last_error = exc
                    time.sleep(0.1)  # Brief backoff
            
            # Record failure to trigger circuit breaker
            if breaker:
                breaker.record_failure(last_error)
            
            logger.warn("Failover", provider=provider.name, error=str(last_error))
            
        logger.error("RuntimeError", error="All providers in priority chain failed")
        raise RuntimeError("AI runtime failed to process request. All providers exhausted.") from last_error

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

    async def complete_structured(self, request: CompletionRequest, schema: Dict[str, Any]) -> CompletionResponse:
        logger.info("RequestStarted", model=request.model, structured=True)
        
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

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
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

    async def check_health(self) -> List[ProviderHealth]:
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
