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


def test_circuit_breaker_aborts_after_three_failures():
    from src.ai_runtime.circuit_breaker import CircuitBreakerError
    service = AIRuntimeService()

    request = CompletionRequest(
        messages=[Message(role="user", content="Hello")],
        model="gpt-4o",
        session_id="test-circuit-run",
    )

    mock_failing = AsyncMock()
    mock_failing.name = "failing"
    mock_failing.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
    mock_failing.complete.side_effect = Exception("Downstream API Failure")

    service.registry.get_priority_chain = MagicMock(return_value=[mock_failing])

    import asyncio
    # Calls 1 and 2 fail with RuntimeError (exhausted)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            asyncio.run(service.complete(request))

    # Call 3 hits threshold 3 and raises CircuitBreakerError
    with pytest.raises(CircuitBreakerError) as exc_info:
        asyncio.run(service.complete(request))

    assert "Circuit breaker tripped after 3 consecutive LLM failures" in str(exc_info.value)


def test_429_rate_limit_logged_loudly(caplog):
    import logging
    from src.ai_runtime.telemetry import StepTelemetry, set_current_step_telemetry, get_current_step_telemetry
    set_current_step_telemetry(StepTelemetry())
    service = AIRuntimeService()

    request = CompletionRequest(
        messages=[Message(role="user", content="Hello")],
        model="gpt-4o",
        session_id="test-429-run",
    )

    mock_rate_limited = AsyncMock()
    mock_rate_limited.name = "gemini"
    mock_rate_limited.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
    mock_rate_limited.complete.side_effect = Exception("HTTP 429: Resource has been exhausted (rate limit)")

    service.registry.get_priority_chain = MagicMock(return_value=[mock_rate_limited])

    import asyncio
    with caplog.at_level(logging.WARNING):
        with pytest.raises(Exception):
            asyncio.run(service.complete(request))

    assert any("429" in record.message and record.levelno >= logging.WARNING for record in caplog.records)
    assert get_current_step_telemetry().llm_provider_response_status == "429"


def test_circuit_breaker_shares_run_id_across_service_instances():
    """Verify circuit breaker accumulates across distinct AIRuntimeService instances using telemetry run_id."""
    from src.ai_runtime.circuit_breaker import CircuitBreakerError
    from src.ai_runtime.telemetry import StepTelemetry, set_current_step_telemetry

    run_id = "test-shared-run-abc"
    set_current_step_telemetry(StepTelemetry(run_id=run_id))

    # Request has no session_id or trace; run_id comes from StepTelemetry
    request = CompletionRequest(
        messages=[Message(role="user", content="Hello")],
        model="gpt-4o",
    )

    import asyncio
    for attempt in range(1, 4):
        service = AIRuntimeService()  # New instance each time, like LangGraph nodes
        mock_failing = AsyncMock()
        mock_failing.name = "gemini"
        mock_failing.get_capability_matrix = MagicMock(return_value=MagicMock(context_window=8192))
        mock_failing.complete.side_effect = Exception("API error")
        service.registry.get_priority_chain = MagicMock(return_value=[mock_failing])

        if attempt < 3:
            with pytest.raises(RuntimeError):
                asyncio.run(service.complete(request))
        else:
            with pytest.raises(CircuitBreakerError) as exc_info:
                asyncio.run(service.complete(request))
            assert "Circuit breaker tripped after 3 consecutive LLM failures" in str(exc_info.value)


def test_failover_model_mapping_groq_to_gemini():
    service = AIRuntimeService()
    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_groq.complete = AsyncMock(side_effect=Exception("Groq failure"))

    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_gemini.complete = AsyncMock(return_value=CompletionResponse(
        text="Fallback to Gemini",
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="gemini",
        model="gemini-2.0-flash"
    ))

    service.registry.get_priority_chain = MagicMock(return_value=[mock_groq, mock_gemini])

    request = CompletionRequest(
        messages=[Message(role="user", content="Test prompt")],
        model="groq/llama-3.1-8b-instant",
        session_id="test-failover-gemini"
    )

    import asyncio
    res = asyncio.run(service.complete(request))
    assert res.provider == "gemini"
    passed_request = mock_gemini.complete.call_args[0][0]
    assert passed_request.model == "gemini-2.0-flash"


def test_failover_model_mapping_groq_to_openrouter():
    service = AIRuntimeService()
    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_groq.complete = AsyncMock(side_effect=Exception("Groq failure"))

    mock_openrouter = MagicMock()
    mock_openrouter.name = "openrouter"
    mock_openrouter.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_openrouter.complete = AsyncMock(return_value=CompletionResponse(
        text="Fallback to OpenRouter",
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="openrouter",
        model="meta-llama/llama-3.1-8b-instruct"
    ))

    service.registry.get_priority_chain = MagicMock(return_value=[mock_groq, mock_openrouter])

    request = CompletionRequest(
        messages=[Message(role="user", content="Test prompt")],
        model="groq/llama-3.1-8b-instant",
        session_id="test-failover-openrouter"
    )

    import asyncio
    res = asyncio.run(service.complete(request))
    assert res.provider == "openrouter"
    passed_request = mock_openrouter.complete.call_args[0][0]
    assert passed_request.model == "meta-llama/llama-3.1-8b-instruct"


def test_failover_model_mapping_openrouter_to_groq():
    service = AIRuntimeService()
    mock_openrouter = MagicMock()
    mock_openrouter.name = "openrouter"
    mock_openrouter.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_openrouter.complete = AsyncMock(side_effect=Exception("OpenRouter error"))

    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_groq.complete = AsyncMock(return_value=CompletionResponse(
        text="Groq fallback",
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="groq",
        model="llama-3.1-8b-instant"
    ))

    service.registry.get_priority_chain = MagicMock(return_value=[mock_openrouter, mock_groq])

    request = CompletionRequest(
        messages=[Message(role="user", content="Test")],
        model="meta-llama/llama-3.1-8b-instruct",
        session_id="test-failover-openrouter-to-groq"
    )

    import asyncio
    res = asyncio.run(service.complete(request))
    assert res.provider == "groq"
    passed_request = mock_groq.complete.call_args[0][0]
    assert passed_request.model == "llama-3.1-8b-instant"


def test_failover_model_mapping_deepseek_groq_to_openrouter():
    service = AIRuntimeService()
    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_groq.complete = AsyncMock(side_effect=Exception("Groq error"))

    mock_openrouter = MagicMock()
    mock_openrouter.name = "openrouter"
    mock_openrouter.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_openrouter.complete = AsyncMock(return_value=CompletionResponse(
        text="OpenRouter deepseek",
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="openrouter",
        model="deepseek/deepseek-r1"
    ))

    service.registry.get_priority_chain = MagicMock(return_value=[mock_groq, mock_openrouter])

    request = CompletionRequest(
        messages=[Message(role="user", content="Test deepseek")],
        model="groq/deepseek-r1-distill-llama-70b",
        session_id="test-deepseek-failover"
    )

    import asyncio
    res = asyncio.run(service.complete(request))
    assert res.provider == "openrouter"
    passed_request = mock_openrouter.complete.call_args[0][0]
    assert passed_request.model == "deepseek/deepseek-r1"


@pytest.mark.asyncio
async def test_failover_stream_model_mapping():
    service = AIRuntimeService()
    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)

    async def groq_stream_fail(req):
        raise Exception("Groq stream failed")
        yield  # Make it an async generator

    mock_groq.stream = groq_stream_fail

    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.get_capability_matrix.return_value = MagicMock(context_window=8192)

    gemini_requests = []

    async def gemini_stream_ok(req):
        from src.ai_runtime.contracts import StreamChunk
        gemini_requests.append(req)
        yield StreamChunk(text="Gemini streamed answer", finish_reason="stop")

    mock_gemini.stream = gemini_stream_ok

    service.registry.get_priority_chain = MagicMock(return_value=[mock_groq, mock_gemini])

    request = CompletionRequest(
        messages=[Message(role="user", content="Test stream failover")],
        model="groq/llama-3.1-8b-instant",
        session_id="test-stream-failover"
    )

    chunks = []
    async for chunk in service.stream(request):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].text == "Gemini streamed answer"
    assert len(gemini_requests) == 1
    assert gemini_requests[0].model == "gemini-2.0-flash"


@pytest.mark.asyncio
async def test_failover_complete_structured_model_mapping():
    service = AIRuntimeService()
    mock_groq = MagicMock()
    mock_groq.name = "groq"
    mock_groq.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_groq.complete_structured = AsyncMock(side_effect=Exception("Groq structured fail"))

    mock_gemini = MagicMock()
    mock_gemini.name = "gemini"
    mock_gemini.get_capability_matrix.return_value = MagicMock(context_window=8192)
    mock_gemini.complete_structured = AsyncMock(return_value=CompletionResponse(
        text='{"key": "value"}',
        usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        provider="gemini",
        model="gemini-2.0-flash"
    ))

    service.registry.get_priority_chain = MagicMock(return_value=[mock_groq, mock_gemini])

    request = CompletionRequest(
        messages=[Message(role="user", content="Structured failover test")],
        model="groq/llama-3.1-8b-instant",
        session_id="test-structured-failover"
    )

    schema = {"type": "object", "properties": {"key": {"type": "string"}}}
    res = await service.complete_structured(request, schema)
    assert res.provider == "gemini"
    passed_request = mock_gemini.complete_structured.call_args[0][0]
    assert passed_request.model == "gemini-2.0-flash"

