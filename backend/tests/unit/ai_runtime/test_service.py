from __future__ import annotations
import pytest
from src.ai_runtime.contracts import CompletionRequest, Message
from src.ai_runtime.circuit_breaker import CircuitBreaker
from src.ai_runtime.registry import ProviderRegistry
from src.ai_runtime.context import ConversationContextManager
from src.ai_runtime.service import AIRuntimeService

def test_circuit_breaker_states():
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)
    assert breaker.state == "CLOSED"
    assert breaker.allow_request() is True
    
    # Trigger 1st failure
    breaker.record_failure("error 1")
    assert breaker.state == "CLOSED"
    
    # Trigger 2nd failure -> OPEN
    breaker.record_failure("error 2")
    assert breaker.state == "OPEN"
    assert breaker.allow_request() is False
    
    # Wait for cooldown to transition to HALF_OPEN
    import time
    time.sleep(0.12)
    assert breaker.allow_request() is True
    assert breaker.state == "HALF_OPEN"
    
    # Success -> CLOSED
    breaker.record_success()
    assert breaker.state == "CLOSED"

def test_context_manager_trimming():
    manager = ConversationContextManager(token_budget=50)
    
    messages = [
        Message(role="user", content="Hello, how are you doing today? Let's write a very long sentence to check context limits."),
        Message(role="assistant", content="I am doing great! How can I help you?"),
        Message(role="user", content="Can you write a python script?")
    ]
    
    trimmed = manager.trim_messages(messages, system_prompt="System prompt content")
    # System prompt is injected at front
    assert trimmed[0].role == "system"
    assert trimmed[0].content == "System prompt content"
    
    # The last message must always be retained
    assert trimmed[-1].content == "Can you write a python script?"
    
    # Check that overall sum of estimated tokens fits budget
    total_est = sum(manager.estimate_message_tokens(m) for m in trimmed)
    assert total_est <= 50

@pytest.mark.asyncio
async def test_mock_provider_execution():
    service = AIRuntimeService()
    req = CompletionRequest(
        messages=[Message(role="user", content="test request")],
        model="mock-lite"
    )
    
    response = await service.complete(req)
    assert response.provider == "mock"
    assert "Mock completion" in response.text
    assert response.usage.total_tokens > 0

@pytest.mark.asyncio
async def test_failover_mechanism():
    registry = ProviderRegistry()
    
    # Inject a failing Ollama url to trigger circuit breaker failover
    from src.ai_runtime.providers.ollama import OllamaProvider
    registry.providers["ollama"] = OllamaProvider(base_url="http://localhost:11111")
    registry.circuit_breakers["ollama"].failure_threshold = 1
    
    service = AIRuntimeService(registry=registry)
    req = CompletionRequest(
        messages=[Message(role="user", content="test failover")],
        model="llama3.2"  # Should default to ollama, fail, and fallback to mock
    )
    
    response = await service.complete(req)
    # Confirm it fell back to mock successfully
    assert response.provider == "mock"
    assert registry.circuit_breakers["ollama"].state == "OPEN"
