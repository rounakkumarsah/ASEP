"""
ASEP — Voice Transcription API Router
======================================
POST /api/v1/voice/transcribe
Provides Universal Voice Typing fallback transcription across:
1. Groq (Whisper-large-v3)
2. Gemini (gemini-2.0-flash inline audio)
3. OpenRouter (audio model fallback)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.services.voice import VoiceTranscriptionError, VoiceTranscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Transcription"])


class FallbackEvent(BaseModel):
    from_provider: str = Field(alias="from")
    to_provider: str = Field(alias="to")
    reason: str
    toast: str


class TranscribeResponse(BaseModel):
    transcript: str
    provider: str
    latency_ms: float
    fallbacks: list[dict[str, Any]] = []


_voice_service = VoiceTranscriptionService()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_voice(
    file: UploadFile = File(..., description="Audio file blob recorded from browser"),
    language: str | None = Form(None, description="Optional BCP-47 / ISO language code"),
) -> TranscribeResponse:
    """
    Transcribe recorded audio file using the 3-provider fallback chain.
    """
    settings = get_settings()
    max_mb = getattr(settings, "VOICE_MAX_SIZE_MB", 25)
    max_bytes = max_mb * 1024 * 1024

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio payload received.",
        )

    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio payload exceeds maximum allowable size of {max_mb}MB.",
        )

    filename = file.filename or "recording.webm"
    content_type = file.content_type or "audio/webm"

    try:
        result = await _voice_service.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
            language=language,
        )
        return TranscribeResponse(
            transcript=result["transcript"],
            provider=result["provider"],
            latency_ms=result["latency_ms"],
            fallbacks=result["fallbacks"],
        )
    except VoiceTranscriptionError as vte:
        logger.error("Voice transcription failed across all providers: %s", vte.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": vte.message,
                "fallbacks": vte.fallbacks,
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during voice transcription: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
