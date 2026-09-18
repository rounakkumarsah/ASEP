"""
Unit tests for Voice Transcription endpoint and 3-provider fallback chain:
POST /api/v1/voice/transcribe
- PRIMARY: Groq (whisper-large-v3)
- BACKUP 1: Gemini (gemini-2.0-flash inline audio)
- BACKUP 2: OpenRouter (google/gemini-2.0-flash-exp:free)
- ALL FAIL: 503 Service Unavailable with friendly toast message
"""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.services.voice import VoiceTranscriptionError, VoiceTranscriptionService


@pytest.fixture()
def test_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_service_provider_order() -> None:
    service = VoiceTranscriptionService()
    assert service.provider_order == ["groq", "gemini", "openrouter"]


@pytest.mark.asyncio
async def test_service_groq_success() -> None:
    service = VoiceTranscriptionService()
    dummy_bytes = b"RIFFfakeaudio"

    with patch.object(service, "_transcribe_groq", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = "Hello from Groq Whisper"
        res = await service.transcribe(
            audio_bytes=dummy_bytes,
            filename="recording.webm",
            content_type="audio/webm",
        )

        assert res["transcript"] == "Hello from Groq Whisper"
        assert res["provider"] == "groq"
        assert res["fallbacks"] == []
        mock_groq.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_groq_429_fallthrough_to_gemini() -> None:
    service = VoiceTranscriptionService()
    dummy_bytes = b"RIFFfakeaudio"

    with patch.object(
        service,
        "_transcribe_groq",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=httpx.Request("POST", "https://api.groq.com"),
            response=httpx.Response(429),
        ),
    ), patch.object(
        service,
        "_transcribe_gemini",
        new_callable=AsyncMock,
        return_value="Hello from Gemini fallback",
    ) as mock_gemini:
        res = await service.transcribe(
            audio_bytes=dummy_bytes,
            filename="recording.webm",
            content_type="audio/webm",
        )

        assert res["transcript"] == "Hello from Gemini fallback"
        assert res["provider"] == "gemini"
        assert len(res["fallbacks"]) == 1
        assert res["fallbacks"][0]["from"] == "groq"
        assert res["fallbacks"][0]["to"] == "gemini"
        assert res["fallbacks"][0]["toast"] == "Groq busy → switching to Gemini"
        mock_gemini.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_groq_and_gemini_fail_fallthrough_to_openrouter() -> None:
    service = VoiceTranscriptionService()
    dummy_bytes = b"RIFFfakeaudio"

    with patch.object(
        service,
        "_transcribe_groq",
        new_callable=AsyncMock,
        side_effect=Exception("Groq quota exceeded"),
    ), patch.object(
        service,
        "_transcribe_gemini",
        new_callable=AsyncMock,
        side_effect=Exception("Gemini timeout"),
    ), patch.object(
        service,
        "_transcribe_openrouter",
        new_callable=AsyncMock,
        return_value="Hello from OpenRouter fallback",
    ) as mock_openrouter:
        res = await service.transcribe(
            audio_bytes=dummy_bytes,
            filename="recording.webm",
            content_type="audio/webm",
        )

        assert res["transcript"] == "Hello from OpenRouter fallback"
        assert res["provider"] == "openrouter"
        assert len(res["fallbacks"]) == 2
        assert res["fallbacks"][0]["from"] == "groq"
        assert res["fallbacks"][0]["to"] == "gemini"
        assert res["fallbacks"][0]["toast"] == "Groq busy → switching to Gemini"
        assert res["fallbacks"][1]["from"] == "gemini"
        assert res["fallbacks"][1]["to"] == "openrouter"
        assert res["fallbacks"][1]["toast"] == "Gemini busy → switching to OpenRouter"
        mock_openrouter.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_all_providers_fail() -> None:
    service = VoiceTranscriptionService()
    dummy_bytes = b"RIFFfakeaudio"

    with patch.object(
        service, "_transcribe_groq", new_callable=AsyncMock, side_effect=Exception("Groq 429")
    ), patch.object(
        service, "_transcribe_gemini", new_callable=AsyncMock, side_effect=Exception("Gemini 503")
    ), patch.object(
        service, "_transcribe_openrouter", new_callable=AsyncMock, side_effect=Exception("OpenRouter 502")
    ):
        with pytest.raises(VoiceTranscriptionError) as exc_info:
            await service.transcribe(
                audio_bytes=dummy_bytes,
                filename="recording.webm",
                content_type="audio/webm",
            )

        err = exc_info.value
        assert "Voice transcription unavailable right now" in err.message
        assert len(err.fallbacks) == 2


def test_api_transcribe_success(test_client: TestClient) -> None:
    dummy_audio = io.BytesIO(b"RIFFdummydata")

    with patch(
        "src.api.routers.voice._voice_service.transcribe",
        new_callable=AsyncMock,
        return_value={
            "transcript": "Transcribed voice input",
            "provider": "groq",
            "latency_ms": 250.0,
            "fallbacks": [],
        },
    ):
        response = test_client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("test.webm", dummy_audio, "audio/webm")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Transcribed voice input"
        assert data["provider"] == "groq"
        assert data["latency_ms"] == 250.0
        assert data["fallbacks"] == []


def test_api_transcribe_fallback_toast(test_client: TestClient) -> None:
    dummy_audio = io.BytesIO(b"RIFFdummydata")

    with patch(
        "src.api.routers.voice._voice_service.transcribe",
        new_callable=AsyncMock,
        return_value={
            "transcript": "Fallback audio text",
            "provider": "gemini",
            "latency_ms": 480.0,
            "fallbacks": [
                {
                    "from": "groq",
                    "to": "gemini",
                    "reason": "429 Too Many Requests",
                    "toast": "Groq busy → switching to Gemini",
                }
            ],
        },
    ):
        response = test_client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("test.webm", dummy_audio, "audio/webm")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Fallback audio text"
        assert data["provider"] == "gemini"
        assert len(data["fallbacks"]) == 1
        assert data["fallbacks"][0]["toast"] == "Groq busy → switching to Gemini"


def test_api_transcribe_all_fail_returns_503(test_client: TestClient) -> None:
    dummy_audio = io.BytesIO(b"RIFFdummydata")

    with patch(
        "src.api.routers.voice._voice_service.transcribe",
        new_callable=AsyncMock,
        side_effect=VoiceTranscriptionError(
            "Voice transcription unavailable right now. Please type or try again in a minute.",
            fallbacks=[
                {"from": "groq", "to": "gemini", "reason": "429", "toast": "Groq busy → switching to Gemini"},
                {"from": "gemini", "to": "openrouter", "reason": "500", "toast": "Gemini busy → switching to OpenRouter"},
            ],
        ),
    ):
        response = test_client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("test.webm", dummy_audio, "audio/webm")},
        )
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Voice transcription unavailable right now" in str(data["detail"])


def test_api_transcribe_empty_file(test_client: TestClient) -> None:
    empty_file = io.BytesIO(b"")
    response = test_client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("empty.webm", empty_file, "audio/webm")},
    )
    assert response.status_code == 400


def test_api_transcribe_payload_too_large(test_client: TestClient) -> None:
    # 26MB dummy data exceeds default 25MB limit
    large_file = io.BytesIO(b"0" * (26 * 1024 * 1024))
    response = test_client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("large.webm", large_file, "audio/webm")},
    )
    assert response.status_code == 413
