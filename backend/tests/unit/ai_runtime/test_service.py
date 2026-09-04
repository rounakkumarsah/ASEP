import pytest
from unittest.mock import AsyncMock, MagicMock
from src.ai_runtime.service import AIRuntimeService
from src.ai_runtime.contracts import CompletionRequest, Message, CompletionResponse, UsageInfo

def test_mock_provider_execution():
    service = AIRuntimeService()
    
    request = CompletionRequest(
        messages=[Message(role="user", content="Hello")],
        model="mock-gpt"
    )
    
    # We force the mock provider to be first
    mock_provider = AsyncMock()
    mock_provider.name = "mock"
    mock_provider.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
    mock_provider.complete.return_value = CompletionResponse(
        text="Mock response", 
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="mock",
        model="mock-gpt"
    )
    service.registry.providers["mock"] = mock_provider
    # Temporarily override chain for testing
    original_chain = service.registry.get_priority_chain
    service.registry.get_priority_chain = MagicMock(return_value=[mock_provider])
    
    import asyncio
    res = asyncio.run(service.complete(request))
    
    assert res is not None
    assert res.provider == "mock"
    service.registry.get_priority_chain = original_chain

def test_failover_mechanism():
    service = AIRuntimeService()
    
    request = CompletionRequest(
        messages=[Message(role="user", content="Hello")],
        model="gpt-4o"
    )
    
    mock_failing = AsyncMock()
    mock_failing.name = "failing"
    mock_failing.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
    mock_failing.complete.side_effect = Exception("Failing API")
    
    mock_success = AsyncMock()
    mock_success.name = "success"
    mock_success.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
    mock_success.complete.return_value = CompletionResponse(
        text="Success fallback", 
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="success",
        model="gpt-4o"
    )
    
    original_chain = service.registry.get_priority_chain
    service.registry.get_priority_chain = MagicMock(return_value=[mock_failing, mock_success])
    
    import asyncio
    res = asyncio.run(service.complete(request))
    
    assert res.provider == "success"
    service.registry.get_priority_chain = original_chain
