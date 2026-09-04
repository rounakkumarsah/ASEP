import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai_runtime.providers.openrouter import OpenRouterProvider
from src.ai_runtime.contracts import CompletionRequest, Message

def test_openrouter_headers_and_options():
    provider = OpenRouterProvider(api_key="test-key")
    headers = provider._build_headers()
    assert headers["Authorization"] == "Bearer test-key"
    assert "X-OpenRouter-Cache" in headers
    assert "X-OpenRouter-Metadata" in headers
    assert headers["X-OpenRouter-Title"] == "ASEP AI"
    
    opts = provider._build_provider_options()
    assert opts.get("data_collection") == "deny"

@pytest.mark.asyncio
async def test_openrouter_complete_with_metadata_and_cache():
    provider = OpenRouterProvider(api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-OpenRouter-Cache-Status": "HIT"}
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello from cache"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        "openrouter_metadata": {"strategy": "free", "summary": "cache-hit"}
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="test")],
            model="openrouter/free"
        )
        res = await provider.complete(req)
        assert res.text == "Hello from cache"
        assert res.usage.cache_status == "HIT"
        assert res.usage.total_tokens == 0
        assert res.router_metadata == {"strategy": "free", "summary": "cache-hit"}

@pytest.mark.asyncio
async def test_openrouter_complete_structured():
    provider = OpenRouterProvider(api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "{\"valid\": true}"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="test schema")],
            model="openrouter/free"
        )
        schema = {"type": "object", "properties": {"valid": {"type": "boolean"}}}
        res = await provider.complete_structured(req, schema)
        assert res.text == '{"valid": true}'
        assert res.provider == "openrouter"

@pytest.mark.asyncio
async def test_openrouter_broadcast_parameters():
    provider = OpenRouterProvider(api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 2}
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="ping")],
            model="openrouter/free",
            user="user_42",
            session_id="session_99",
            trace={"trace_id": "tr_1", "span_name": "sp_1"}
        )
        await provider.complete(req)
        
        # Verify post payload and headers
        call_kwargs = mock_post.call_args[1]
        sent_payload = call_kwargs["json"]
        sent_headers = call_kwargs["headers"]
        
        assert sent_payload["user"] == "user_42"
        assert sent_payload["session_id"] == "session_99"
        assert sent_payload["trace"] == {"trace_id": "tr_1", "span_name": "sp_1"}
        assert sent_headers["x-session-id"] == "session_99"

@pytest.mark.asyncio
async def test_openrouter_reasoning_and_latency():
    provider = OpenRouterProvider(api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": "Answer is 42",
                "reasoning": "Step 1: Compute 6*7=42",
                "reasoning_details": [{"type": "reasoning.text", "text": "Step 1: Compute 6*7=42"}]
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "reasoning_tokens": 20,
            "prompt_tokens_details": {"cached_tokens": 8}
        }
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[
                Message(role="user", content="Calculate 6*7"),
                Message(role="assistant", content="Working on it...", reasoning="Considering multiplication"),
            ],
            model="deepseek/deepseek-r1",
            reasoning={"effort": "high"},
            preferred_max_latency={"p90": 2.5}
        )
        res = await provider.complete(req)
        
        # Verify sent payload
        call_kwargs = mock_post.call_args[1]
        sent_payload = call_kwargs["json"]
        
        assert sent_payload["reasoning"] == {"effort": "high"}
        assert sent_payload["provider"]["preferred_max_latency"] == {"p90": 2.5}
        assert sent_payload["messages"][1]["reasoning"] == "Considering multiplication"
        
        # Verify parsed response
        assert res.reasoning == "Step 1: Compute 6*7=42"
        assert res.reasoning_details[0]["type"] == "reasoning.text"
        assert res.usage.reasoning_tokens == 20
        assert res.usage.cached_tokens == 8


