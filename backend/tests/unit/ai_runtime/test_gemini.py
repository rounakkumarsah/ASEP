import base64
import hashlib
import hmac
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_runtime.contracts import CompletionRequest, Message
from src.ai_runtime.providers.gemini import GeminiProvider


def test_gemini_resolve_model():
    assert GeminiProvider._resolve_model("gemini") == "gemini-3.8-flash"
    assert GeminiProvider._resolve_model("antigravity-default") == "gemini-3.8-flash"
    assert GeminiProvider._resolve_model("gemini-pro") == "gemini-3.1-pro"
    assert GeminiProvider._resolve_model("gemini-flash-lite") == "gemini-3.5-flash-lite"
    assert GeminiProvider._resolve_model("nano-banana") == "gemini-3.1-flash-image"
    assert GeminiProvider._resolve_model("nano-banana-pro") == "gemini-3-pro-image"
    assert GeminiProvider._resolve_model("veo") == "veo-3.1-generate-preview"
    assert GeminiProvider._resolve_model("lyria-pro") == "lyria-3.5-pro-preview"
    assert GeminiProvider._resolve_model("gemini-3.8-flash") == "gemini-3.8-flash"


@pytest.mark.asyncio
async def test_gemini_interact_success():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "v1_test_interaction",
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "Interaction response!"}]
            }
        ],
        "usage": {
            "total_tokens": 42,
            "total_input_tokens": 12,
            "total_output_tokens": 30
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Hello")],
            model="gemini-3.8-flash"
        )
        res = await provider.interact(req)
        assert res.text == "Interaction response!"
        assert res.router_metadata is not None
        assert res.router_metadata["interaction_id"] == "v1_test_interaction"
        assert res.usage.total_tokens == 42


@pytest.mark.asyncio
async def test_gemini_interact_fallback():
    provider = GeminiProvider(api_key="test-key")
    error_resp = MagicMock()
    error_resp.status_code = 401

    fallback_resp = MagicMock()
    fallback_resp.status_code = 200
    fallback_resp.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Fallback content"}]}
        }],
        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 10}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [error_resp, fallback_resp]
        req = CompletionRequest(
            messages=[Message(role="user", content="Hello")],
            model="gemini"
        )
        res = await provider.interact(req)
        assert res.text == "Fallback content"


def test_gemini_vision_coordinate_parsers():
    # Test bounding box descaling from [0, 1000] to pixels
    raw_boxes = [
        {"box_2d": [100, 200, 500, 600], "label": "coffee cup"}
    ]
    parsed_boxes = GeminiProvider.parse_bounding_boxes(raw_boxes, image_width=800, image_height=600)
    assert len(parsed_boxes) == 1
    assert parsed_boxes[0]["label"] == "coffee cup"
    # ymin: 100/1000 * 600 = 60; xmin: 200/1000 * 800 = 160; ymax: 500/1000 * 600 = 300; xmax: 600/1000 * 800 = 480
    assert parsed_boxes[0]["box_pixel"] == [60, 160, 300, 480]

    # Test segmentation polygon mask descaling
    raw_masks = [
        {"mask": [[100, 100], [200, 300]], "label": "flower"}
    ]
    parsed_masks = GeminiProvider.parse_segmentation_masks(raw_masks, image_width=1000, image_height=500)
    assert len(parsed_masks) == 1
    assert parsed_masks[0]["mask_polygon"] == [[100, 50], [200, 150]]


@pytest.mark.asyncio
async def test_gemini_interact_function_calling():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "v1_fc_interaction",
        "status": "completed",
        "steps": [
            {
                "type": "thought",
                "signature": "sig_abc",
                "summary": [{"type": "text", "text": "Need to fetch weather"}]
            },
            {
                "type": "function_call",
                "id": "call_123",
                "name": "get_weather",
                "arguments": {"location": "London"}
            }
        ],
        "usage": {"total_tokens": 50, "total_input_tokens": 30, "total_output_tokens": 20}
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="What's the weather in London?")],
            model="gemini",
            tools=[{"type": "function", "name": "get_weather", "parameters": {}}]
        )
        res = await provider.interact(req)
        assert res.finish_reason == "tool_calls"
        assert res.tool_calls is not None
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].name == "get_weather"
        assert "London" in res.tool_calls[0].arguments
        assert res.router_metadata["thought_summary"][0]["text"] == "Need to fetch weather"


@pytest.mark.asyncio
async def test_gemini_cancel_interaction():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "int_123", "status": "canceled"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.cancel_interaction("int_123")
        assert res["status"] == "canceled"


@pytest.mark.asyncio
async def test_gemini_environments_api():
    provider = GeminiProvider(api_key="test-key")

    list_resp = MagicMock()
    list_resp.status_code = 200
    list_resp.json.return_value = {"environments": [{"environment_id": "env_abc", "type": "remote"}]}

    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.json.return_value = {"environment_id": "env_abc", "type": "remote"}

    del_resp = MagicMock()
    del_resp.status_code = 204

    snap_resp = MagicMock()
    snap_resp.status_code = 200
    snap_resp.content = b"fake-tar-bytes"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_get.side_effect = [list_resp, get_resp, snap_resp]
        mock_del.return_value = del_resp

        envs = await provider.list_environments()
        assert len(envs["environments"]) == 1
        assert envs["environments"][0]["environment_id"] == "env_abc"

        env = await provider.get_environment("env_abc")
        assert env["environment_id"] == "env_abc"

        snapshot = await provider.download_environment_snapshot("env_abc")
        assert snapshot == b"fake-tar-bytes"

        deleted = await provider.delete_environment("env_abc")
        assert deleted is True


@pytest.mark.asyncio
async def test_gemini_agents_registry():
    provider = GeminiProvider(api_key="test-key")

    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.json.return_value = {"id": "code-analyst", "base_agent": "antigravity-preview-05-2026"}

    list_resp = MagicMock()
    list_resp.status_code = 200
    list_resp.json.return_value = {"agents": [{"id": "code-analyst"}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_post.return_value = create_resp
        mock_get.return_value = list_resp
        mock_del.return_value = MagicMock(status_code=204)

        agent = await provider.create_agent("code-analyst", system_instruction="Analyze code")
        assert agent["id"] == "code-analyst"

        agents = await provider.list_agents()
        assert len(agents) == 1
        assert agents[0]["id"] == "code-analyst"

        assert await provider.delete_agent("code-analyst") is True


@pytest.mark.asyncio
async def test_gemini_triggers_api():
    provider = GeminiProvider(api_key="test-key")

    create_resp = MagicMock()
    create_resp.status_code = 200
    create_resp.json.return_value = {"id": "trig_1", "status": "active"}

    patch_resp = MagicMock()
    patch_resp.status_code = 200
    patch_resp.json.return_value = {"id": "trig_1", "status": "paused"}

    run_resp = MagicMock()
    run_resp.status_code = 200
    run_resp.json.return_value = {"execution_id": "exec_1", "status": "running"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.patch", new_callable=AsyncMock) as mock_patch, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_post.side_effect = [create_resp, run_resp]
        mock_patch.return_value = patch_resp
        mock_del.return_value = MagicMock(status_code=204)

        trig = await provider.create_trigger(
            schedule="0 9 * * *",
            time_zone="UTC",
            interaction={"input": "run daily check"}
        )
        assert trig["id"] == "trig_1"

        updated = await provider.update_trigger("trig_1", "paused")
        assert updated["status"] == "paused"

        run = await provider.run_trigger("trig_1")
        assert run["execution_id"] == "exec_1"

        assert await provider.delete_trigger("trig_1") is True


def test_gemini_hooks_config_generator():
    cfg = GeminiProvider.generate_hooks_config(
        command_deny_patterns=["rm -rf"],
        http_telemetry_url="https://telemetry.corp.internal/events"
    )
    assert "security-gate" in cfg
    assert cfg["security-gate"]["enabled"] is True
    assert cfg["security-gate"]["pre_tool_execution"][0]["matcher"] == "code_execution"

    assert "audit-telemetry" in cfg
    assert cfg["audit-telemetry"]["enabled"] is True
    assert cfg["audit-telemetry"]["post_tool_execution"][0]["hooks"][0]["url"] == "https://telemetry.corp.internal/events"


def test_gemini_coordinate_scaling():
    # 500, 500 on 1920x1080 -> 960, 540
    px, py = GeminiProvider.denormalize_coordinates(500, 500, 1920, 1080)
    assert px == 960
    assert py == 540

    # 960, 540 on 1920x1080 -> 500, 500
    nx, ny = GeminiProvider.normalize_coordinates(960, 540, 1920, 1080)
    assert nx == 500
    assert ny == 500


@pytest.mark.asyncio
async def test_gemini_interact_multi_tool_step_parsing():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "int_multi_tool",
        "environment_id": "env_test_99",
        "status": "completed",
        "steps": [
            {
                "type": "thought",
                "signature": "sig_thought_xyz",
                "summary": [{"type": "text", "text": "Analyzing user query..."}]
            },
            {
                "type": "google_search_call",
                "arguments": {"queries": ["python fibonacci benchmark"]}
            },
            {
                "type": "google_search_result",
                "result": [{"search_suggestions": "<div>search widget</div>"}]
            },
            {
                "type": "code_execution_call",
                "arguments": {"code": "print(sum(range(10)))"}
            },
            {
                "type": "code_execution_result",
                "result": "45\n"
            },
            {
                "type": "url_context_result",
                "url": "https://example.com/docs",
                "status": "success"
            },
            {
                "type": "function_call",
                "id": "call_click_1",
                "name": "click",
                "arguments": {
                    "x": 450,
                    "y": 120,
                    "intent": "Click search button",
                    "safety_decision": {
                        "decision": "require_confirmation",
                        "explanation": "Modifies system preferences"
                    }
                }
            },
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "text",
                        "text": "The sum is 45.",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url": "https://example.com/python",
                                "start_index": 0,
                                "end_index": 14
                            }
                        ]
                    }
                ]
            }
        ],
        "usage": {
            "total_input_tokens": 100,
            "total_output_tokens": 50,
            "total_tokens": 150
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Calculate and verify")],
            model="gemini-3.8-flash"
        )
        res = await provider.interact(req)
        assert res.text == "The sum is 45."
        assert res.router_metadata["environment_id"] == "env_test_99"
        assert res.router_metadata["search_queries"] == ["python fibonacci benchmark"]
        assert res.router_metadata["search_suggestions"] == ["<div>search widget</div>"]
        assert res.router_metadata["code_executions"] == ["print(sum(range(10)))"]
        assert res.router_metadata["code_results"] == ["45\n"]
        assert len(res.router_metadata["url_context_results"]) == 1
        assert len(res.router_metadata["citations"]) == 1
        assert len(res.router_metadata["safety_decisions"]) == 1
        assert res.router_metadata["safety_decisions"][0]["decision"] == "require_confirmation"
        assert res.router_metadata["thought_signatures"] == ["sig_thought_xyz"]


@pytest.mark.asyncio
async def test_gemini_file_search_stores_api():
    provider = GeminiProvider(api_key="test-key")

    create_resp = MagicMock(status_code=200)
    create_resp.json.return_value = {"name": "fileSearchStores/store_1", "displayName": "My Store"}

    list_resp = MagicMock(status_code=200)
    list_resp.json.return_value = {"fileSearchStores": [{"name": "fileSearchStores/store_1"}]}

    get_resp = MagicMock(status_code=200)
    get_resp.json.return_value = {"name": "fileSearchStores/store_1"}

    media_resp = MagicMock(status_code=200)
    media_resp.content = b"fake-png-bytes"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_post.return_value = create_resp
        mock_get.side_effect = [list_resp, get_resp, media_resp]
        mock_del.return_value = MagicMock(status_code=204)

        store = await provider.create_file_search_store("My Store")
        assert store["name"] == "fileSearchStores/store_1"

        stores = await provider.list_file_search_stores()
        assert len(stores) == 1

        fetched = await provider.get_file_search_store("store_1")
        assert fetched["name"] == "fileSearchStores/store_1"

        media = await provider.download_media("media/blob_123")
        assert media == b"fake-png-bytes"

        assert await provider.delete_file_search_store("store_1") is True


@pytest.mark.asyncio
async def test_gemini_ephemeral_token_creation():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {
        "name": "authTokens/eph_12345",
        "uses": 1,
        "expireTime": "2026-09-05T02:00:00Z"
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        token = await provider.create_ephemeral_token(ttl_seconds=900)
        assert token["name"] == "authTokens/eph_12345"


def test_gemini_live_api_helpers():
    provider = GeminiProvider(api_key="test-key")

    # 1. URL builders
    std_url = provider.get_live_websocket_url()
    assert "GenerativeService.BidiGenerateContent?key=test-key" in std_url

    eph_url = provider.get_live_websocket_url(api_key_or_token="token_xyz", is_ephemeral=True)
    assert "BidiGenerateContentConstrained?access_token=token_xyz" in eph_url

    # 2. Setup message builder
    setup_msg = provider.build_live_setup_message(
        model="gemini-3.1-flash-live-preview",
        voice_name="Puck",
        thinking_level="high",
        system_instruction="Be a voice copilot.",
        tools=[{"googleSearch": {}}],
        context_compression_trigger=75000,
        session_resumption_handle="handle_abc"
    )
    assert "setup" in setup_msg
    setup = setup_msg["setup"]
    assert setup["model"] == "models/gemini-3.1-flash-live-preview"
    assert setup["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Puck"
    assert setup["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "high"
    assert setup["systemInstruction"]["parts"][0]["text"] == "Be a voice copilot."
    assert setup["contextWindowCompression"]["triggerTokens"] == 75000
    assert setup["sessionResumption"]["handle"] == "handle_abc"

    # 3. Media framing
    audio_frame = provider.format_realtime_audio_chunk(b"\x00\x01\x02", rate=16000)
    assert audio_frame["realtimeInput"]["mediaChunks"][0]["mimeType"] == "audio/pcm;rate=16000"
    assert isinstance(audio_frame["realtimeInput"]["mediaChunks"][0]["data"], str)

    video_frame = provider.format_realtime_video_frame(b"\xff\xd8\xff", mime_type="image/jpeg")
    assert video_frame["realtimeInput"]["mediaChunks"][0]["mimeType"] == "image/jpeg"

    stream_end = provider.format_realtime_stream_end()
    assert stream_end["realtimeInput"]["audioStreamEnd"] is True

    # 4. Tool response formatting
    tool_resp = provider.format_live_tool_response(
        call_id="call_001",
        name="run_cmd",
        result={"status": "ok"},
        scheduling="WHEN_IDLE"
    )
    fn_resp = tool_resp["toolResponse"]["functionResponses"][0]
    assert fn_resp["id"] == "call_001"
    assert fn_resp["response"]["scheduling"] == "WHEN_IDLE"
    assert fn_resp["response"]["result"]["status"] == "ok"


@pytest.mark.asyncio
async def test_gemini_service_tiers_and_caching():
    provider = GeminiProvider(api_key="test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"x-gemini-service-tier": "priority"}
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Priority response"}]}
        }],
        "usageMetadata": {
            "promptTokenCount": 5000,
            "candidatesTokenCount": 200,
            "cachedContentTokenCount": 4096,
            "totalTokenCount": 5200
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Urgent task")],
            model="gemini-3.8-flash",
            service_tier="priority"
        )
        res = await provider.complete(req)
        assert res.text == "Priority response"
        assert res.usage.cached_tokens == 4096
        assert "hit:priority" in res.usage.cache_status
        assert res.router_metadata["service_tier"] == "priority"


@pytest.mark.asyncio
async def test_gemini_batch_jobs_api():
    provider = GeminiProvider(api_key="test-key")

    create_resp = MagicMock(status_code=200)
    create_resp.json.return_value = {"name": "batches/job_123", "state": "JOB_STATE_PENDING"}

    get_resp = MagicMock(status_code=200)
    get_resp.json.return_value = {"name": "batches/job_123", "state": "JOB_STATE_SUCCEEDED"}

    list_resp = MagicMock(status_code=200)
    list_resp.json.return_value = {"batches": [{"name": "batches/job_123"}]}

    cancel_resp = MagicMock(status_code=200)
    cancel_resp.json.return_value = {"name": "batches/job_123", "state": "JOB_STATE_CANCELLED"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_post.side_effect = [create_resp, cancel_resp]
        mock_get.side_effect = [get_resp, list_resp]
        mock_del.return_value = MagicMock(status_code=204)

        job = await provider.create_batch_job(
            model="gemini-3.8-flash",
            inline_requests=[{"contents": [{"parts": [{"text": "Hi"}]}]}],
            display_name="batch-test"
        )
        assert job["name"] == "batches/job_123"

        status = await provider.get_batch_job("batches/job_123")
        assert status["state"] == "JOB_STATE_SUCCEEDED"

        jobs = await provider.list_batch_jobs()
        assert len(jobs) == 1

        cancelled = await provider.cancel_batch_job("batches/job_123")
        assert cancelled["state"] == "JOB_STATE_CANCELLED"

        assert await provider.delete_batch_job("batches/job_123") is True


@pytest.mark.asyncio
async def test_gemini_webhooks_api_and_verification():
    provider = GeminiProvider(api_key="test-key")

    create_resp = MagicMock(status_code=200)
    create_resp.json.return_value = {
        "id": "wh_123",
        "name": "AuditWebhook",
        "new_signing_secret": "my_test_secret"
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        mock_post.return_value = create_resp
        mock_del.return_value = MagicMock(status_code=204)

        wh = await provider.create_static_webhook(
            name="AuditWebhook",
            uri="https://api.asep.internal/callback",
            subscribed_events=["batch.succeeded"]
        )
        assert wh["id"] == "wh_123"
        assert wh["new_signing_secret"] == "my_test_secret"

        assert await provider.delete_static_webhook("wh_123") is True

    # Test Webhook Signature Verification (Standard Webhooks HMAC-SHA256)
    secret = "test_signing_key_42"
    webhook_id = "msg_pqrst123"
    webhook_timestamp = str(int(time.time()))
    body = b'{"type":"batch.succeeded","data":{"id":"batch_999"}}'

    # Valid signature generation
    sig_payload = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + body
    valid_sig = base64.b64encode(hmac.new(secret.encode("utf-8"), sig_payload, hashlib.sha256).digest()).decode("utf-8")
    header_sig = f"v1,{valid_sig}"

    # Verify valid
    is_valid = GeminiProvider.verify_static_webhook(
        raw_body=body,
        webhook_id=webhook_id,
        webhook_timestamp=webhook_timestamp,
        webhook_signature=header_sig,
        secret=secret
    )
    assert is_valid is True

    # Verify expired replay (600s in past)
    expired_ts = str(int(time.time()) - 600)
    is_replay = GeminiProvider.verify_static_webhook(
        raw_body=body,
        webhook_id=webhook_id,
        webhook_timestamp=expired_ts,
        webhook_signature=header_sig,
        secret=secret,
        max_drift_seconds=300
    )
    assert is_replay is False

    # Verify invalid signature
    is_tampered = GeminiProvider.verify_static_webhook(
        raw_body=body,
        webhook_id=webhook_id,
        webhook_timestamp=webhook_timestamp,
        webhook_signature="v1,tampered_signature==",
        secret=secret
    )
    assert is_tampered is False


@pytest.mark.asyncio
async def test_gemini_stream_interaction_sse():
    provider = GeminiProvider(api_key="test-key")
    
    class FakeStreamResponse:
        def raise_for_status(self):
            pass

        async def aiter_lines(self):
            lines = [
                "id: evt_1",
                "event: interaction.created",
                'data: {"interaction": {"id": "int_999", "status": "in_progress"}}',
                "",
                "id: evt_2",
                "event: step.start",
                'data: {"step": {"type": "model_output"}}',
                "",
                "id: evt_3",
                "event: step.delta",
                'data: {"delta": {"type": "text", "text": "Streaming tokens..."}}',
                "",
                "id: evt_4",
                "event: step.stop",
                'data: {"index": 0}',
                "",
                "id: evt_5",
                "event: interaction.completed",
                'data: {"interaction": {"id": "int_999", "usage": {"total_tokens": 15, "total_input_tokens": 5, "total_output_tokens": 10}}}',
                ""
            ]
            for line in lines:
                yield line

    class FakeAsyncContextManager:
        async def __aenter__(self):
            return FakeStreamResponse()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with patch("httpx.AsyncClient.stream", return_value=FakeAsyncContextManager()):
        req = CompletionRequest(
            messages=[Message(role="user", content="Stream this")],
            model="gemini-3.8-flash"
        )
        events = []
        async for evt in provider.stream_interaction(req, last_event_id="evt_0"):
            events.append(evt)

        assert len(events) == 5
        assert events[0]["event"] == "interaction.created"
        assert events[0]["data"]["interaction"]["id"] == "int_999"
        assert events[0]["id"] == "evt_1"
        assert events[2]["event"] == "step.delta"
        assert events[2]["data"]["delta"]["text"] == "Streaming tokens..."
        assert events[4]["event"] == "interaction.completed"


@pytest.mark.asyncio
async def test_gemini_stream_with_interactions_api():
    provider = GeminiProvider(api_key="test-key")
    
    mock_events = [
        {"event": "step.delta", "data": {"delta": {"type": "text", "text": "Part 1"}}},
        {"event": "step.delta", "data": {"delta": {"type": "text", "text": " Part 2"}}},
        {
            "event": "interaction.completed",
            "data": {
                "interaction": {
                    "usage": {
                        "total_input_tokens": 10,
                        "total_output_tokens": 5,
                        "total_tokens": 15,
                        "total_cached_tokens": 0
                    }
                }
            }
        }
    ]

    async def fake_stream_interaction(request, last_event_id=None):
        for evt in mock_events:
            yield evt

    with patch.object(provider, "stream_interaction", side_effect=fake_stream_interaction):
        req = CompletionRequest(
            messages=[Message(role="user", content="Hello")],
            model="gemini-3.8-flash",
            router_metadata={"use_interactions_api": True}
        )
        chunks = []
        async for chunk in provider.stream(req):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].text == "Part 1"
        assert chunks[1].text == " Part 2"
        assert chunks[2].finish_reason == "stop"
        assert chunks[2].usage.total_tokens == 15


def test_gemini_media_resolution_payload():
    provider = GeminiProvider(api_key="test-key")
    req = CompletionRequest(
        messages=[Message(role="user", content="Inspect screen")],
        model="gemini-3.8-flash",
        router_metadata={
            "multimodal_parts": [
                {"type": "image", "uri": "https://example.com/screenshot.png", "media_resolution": "ultra_high"},
                {"type": "video", "uri": "gs://bucket/vid.mp4", "media_resolution": "low"}
            ]
        }
    )
    payload, headers, timeout = provider._build_interaction_payload(req)
    contents = payload["input"][0]["content"]
    assert contents[0]["text"] == "Inspect screen"
    assert contents[1]["media_resolution"] == "ultra_high"
    assert contents[2]["media_resolution"] == "low"


@pytest.mark.asyncio
async def test_gemini_interaction_lifecycle_and_gcs_registration():
    provider = GeminiProvider(api_key="test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "int_test", "status": "canceled"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_del:
        
        mock_get.return_value = mock_resp
        mock_post.return_value = mock_resp
        mock_del.return_value = mock_resp

        get_res = await provider.get_interaction("int_test")
        assert get_res["id"] == "int_test"

        cancel_res = await provider.cancel_interaction("int_test")
        assert cancel_res["status"] == "canceled"

        del_res = await provider.delete_interaction("int_test")
        assert del_res["id"] == "int_test"

        # Test GCS file registration
        mock_resp.json.return_value = {"name": "files/gcs-12345", "uri": "gs://my-bucket/doc.pdf"}
        reg_res = await provider.register_gcs_file(
            uri="gs://my-bucket/doc.pdf",
            mime_type="application/pdf",
            display_name="Enterprise Report"
        )
        assert reg_res["name"] == "files/gcs-12345"


@pytest.mark.asyncio
async def test_gemini_usage_info_thought_and_tool_tokens():
    provider = GeminiProvider(api_key="test-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "v1_test_usage_tokens",
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "Answer with detailed telemetry."}]
            }
        ],
        "usage": {
            "total_tokens": 1500,
            "total_input_tokens": 400,
            "total_output_tokens": 300,
            "total_cached_tokens": 200,
            "total_thought_tokens": 500,
            "total_tool_use_tokens": 100
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        req = CompletionRequest(
            messages=[Message(role="user", content="Analyze video")],
            model="gemini-3.8-flash"
        )
        res = await provider.interact(req)
        assert res.usage.thought_tokens == 500
        assert res.usage.tool_use_tokens == 100
        assert res.usage.cached_tokens == 200
        assert res.usage.total_tokens == 1500


def test_gemini_temperature_guard_gemini3():
    provider = GeminiProvider(api_key="test-key")
    
    # Gemini 3.1 Pro with temperature=0.7 (default) should NOT have temperature in generation_config
    req_gemini3 = CompletionRequest(
        messages=[Message(role="user", content="Solve math problem")],
        model="gemini-3.1-pro",
        temperature=0.7
    )
    payload_g3, _, _ = provider._build_interaction_payload(req_gemini3)
    gen_config_g3 = payload_g3.get("generation_config", {})
    assert "temperature" not in gen_config_g3
    assert gen_config_g3.get("thinking_level") == "medium"

    # Non-Gemini 3 model (e.g. gemini-1.0-pro) should allow temperature=0.7
    req_non_g3 = CompletionRequest(
        messages=[Message(role="user", content="Write poem")],
        model="gemini-1.0-pro",
        temperature=0.7
    )
    payload_non_g3, _, _ = provider._build_interaction_payload(req_non_g3)
    gen_config_non_g3 = payload_non_g3.get("generation_config", {})
    assert gen_config_non_g3.get("temperature") == 0.7


def test_gemini_format_agentic_prompt():
    prompt = GeminiProvider.format_agentic_prompt(
        task="Audit system telemetry and identify memory leaks.",
        role="Lead Site Reliability Engineer",
        constraints=["Zero false positives", "Provide concrete remediation steps"],
        context="Service cluster running Kubernetes v1.30 in production.",
        output_format="JSON object with 'leaks' and 'action_items'",
        anchor_2026=True
    )
    assert "<role>\nLead Site Reliability Engineer\n</role>" in prompt
    assert "<constraints>" in prompt
    assert "remember it is 2026 this year" in prompt
    assert "knowledge cutoff is January 2025" in prompt
    assert "- Zero false positives" in prompt
    assert "<context>\nService cluster running Kubernetes v1.30 in production.\n</context>" in prompt
    assert "<task>\nAudit system telemetry and identify memory leaks.\n</task>" in prompt
    assert "<output_format>\nJSON object with 'leaks' and 'action_items'\n</output_format>" in prompt
