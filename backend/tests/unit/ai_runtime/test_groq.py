import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai_runtime.providers.groq import GroqProvider
from src.ai_runtime.contracts import CompletionRequest, Message

def test_groq_provider_basics():
    provider = GroqProvider(api_key="test-groq-key")
    assert provider.name == "groq"
    assert provider.base_url == "https://api.groq.com/openai/v1"
    caps = provider.get_capability_matrix()
    assert caps.streaming is True
    assert caps.tool_calling is True
    assert caps.context_window == 131072

@pytest.mark.asyncio
async def test_groq_complete():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Fast answer from Groq"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Hello Groq")],
            model="groq"
        )
        res = await provider.complete(req)
        assert res.text == "Fast answer from Groq"
        assert res.provider == "groq"
        assert res.usage.total_tokens == 20
        assert res.finish_reason == "stop"

@pytest.mark.asyncio
async def test_groq_complete_structured():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "{\"status\": \"success\"}"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 5, "total_tokens": 20}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Return status json")],
            model="qwen/qwen3.8-27b"
        )
        res = await provider.complete_structured(req, {"type": "object"})
        assert res.text == '{"status": "success"}'
        assert res.provider == "groq"

@pytest.mark.asyncio
async def test_groq_check_health():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"id": "qwen/qwen3.8-27b"}, {"id": "openai/gpt-oss-120b"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.check_health()
        assert health.is_healthy is True
        assert health.provider_name == "groq"
        assert "qwen/qwen3.8-27b" in health.loaded_models

@pytest.mark.asyncio
async def test_groq_tool_calling():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": "{\"location\": \"San Francisco\"}"
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {"prompt_tokens": 25, "completion_tokens": 15, "total_tokens": 40}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Weather in SF?")],
            model="qwen/qwen3.6-27b",
            tools=[{"type": "function", "function": {"name": "get_weather"}}],
            tool_choice="auto"
        )
        res = await provider.complete(req)
        assert res.finish_reason == "tool_calls"
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].name == "get_weather"
        assert res.tool_calls[0].id == "call_123"

@pytest.mark.asyncio
async def test_groq_builtin_executed_tools():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": "Here is the search result",
                "executed_tools": [{
                    "type": "web_search",
                    "arguments": "{\"query\": \"latest AI news\"}",
                    "output": "Found AI news"
                }]
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Latest AI news?")],
            model="groq/compound",
            router_metadata={"compound_custom": {"tools": {"enabled_tools": ["web_search"]}}}
        )
        res = await provider.complete(req)
        assert res.text == "Here is the search result"
        assert res.router_metadata is not None
        assert "executed_tools" in res.router_metadata
        assert res.router_metadata["executed_tools"][0]["type"] == "web_search"

@pytest.mark.asyncio
async def test_groq_responses_api():
    provider = GroqProvider(api_key="test-groq-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "resp_test123",
        "object": "response",
        "status": "completed",
        "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Hello!"}]}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.complete_response(input_text="Hello", model="openai/gpt-oss-120b")
        assert res["id"] == "resp_test123"
        assert res["status"] == "completed"

@pytest.mark.asyncio
async def test_groq_batches_and_files():
    provider = GroqProvider(api_key="test-groq-key")
    file_resp = MagicMock()
    file_resp.status_code = 200
    file_resp.json.return_value = {"id": "file_test123", "object": "file", "purpose": "batch"}

    batch_resp = MagicMock()
    batch_resp.status_code = 200
    batch_resp.json.return_value = {"id": "batch_test123", "object": "batch", "status": "validating"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [file_resp, batch_resp]
        uploaded = await provider.upload_file(file_content="{}", filename="test.jsonl")
        assert uploaded["id"] == "file_test123"

        batch = await provider.create_batch(input_file_id="file_test123")
        assert batch["id"] == "batch_test123"
        assert batch["status"] == "validating"

@pytest.mark.asyncio
async def test_groq_audio_apis():
    provider = GroqProvider(api_key="test-groq-key")
    trans_resp = MagicMock()
    trans_resp.status_code = 200
    trans_resp.json.return_value = {"text": "Bonjour translated to Hello"}

    speech_resp = MagicMock()
    speech_resp.status_code = 200
    speech_resp.content = b"RIFFWAVE"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [trans_resp, speech_resp]
        trans = await provider.translate_audio(audio_bytes=b"dummy", filename="test.wav")
        assert trans["text"] == "Bonjour translated to Hello"

        audio_out = await provider.generate_speech(text="Hello", voice="troy")
        assert audio_out.startswith(b"RIFF")
