"""
ASEP — Voice Transcription Service
===================================
Implements Universal Voice Typing Layer 2 fallback chain:
1. PRIMARY: Groq (whisper-large-v3)
   - On 429/quota/failure -> auto-fallthrough to next, log provider switch in console
     and emit fallback event: "Groq busy → switching to Gemini"
2. BACKUP 1: Gemini (gemini-2.0-flash)
   - Uploads audio blob as inline audio data with prompt:
     "Transcribe this audio exactly. Output only the spoken text."
   - On failure -> auto-fallthrough to OpenRouter: "Gemini busy → switching to OpenRouter"
3. BACKUP 2: OpenRouter (configurable audio model, e.g. google/gemini-2.0-flash-exp:free)
   - Same audio+prompt approach
4. ALL FAIL -> raises VoiceTranscriptionError with descriptive message:
   "Voice transcription unavailable right now. Please type or try again in a minute."
"""

from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class VoiceTranscriptionError(Exception):
    """Raised when all transcription providers fail."""
    def __init__(self, message: str, fallbacks: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.message = message
        self.fallbacks = fallbacks or []


class VoiceTranscriptionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_order(self) -> list[str]:
        raw_order = getattr(self.settings, "VOICE_PROVIDER_ORDER", "groq,gemini,openrouter")
        return [p.strip().lower() for p in raw_order.split(",") if p.strip()]

    def _normalize_mime_type(self, mime_type: str | None, filename: str) -> str:
        if mime_type:
            # Strip codec parameters: audio/webm;codecs=opus -> audio/webm
            clean_mime = mime_type.split(";")[0].strip().lower()
            if clean_mime in ("audio/webm", "audio/wav", "audio/x-wav", "audio/mp4", "audio/m4a", "audio/ogg", "audio/mpeg", "audio/mp3", "audio/aac"):
                return "audio/wav" if clean_mime == "audio/x-wav" else clean_mime

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        ext_map = {
            "webm": "audio/webm",
            "wav": "audio/wav",
            "mp3": "audio/mp3",
            "mp4": "audio/mp4",
            "m4a": "audio/m4a",
            "ogg": "audio/ogg",
            "aac": "audio/aac",
        }
        return ext_map.get(ext, "audio/webm")

    async def _transcribe_groq(
        self,
        audio_bytes: bytes,
        filename: str,
        mime_type: str,
        language: str | None = None,
    ) -> str:
        api_key = getattr(self.settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        model = getattr(self.settings, "VOICE_GROQ_MODEL", "whisper-large-v3")
        headers = {"Authorization": f"Bearer {api_key}"}

        # Ensure filename has an audio extension expected by Whisper
        upload_name = filename
        if not any(upload_name.lower().endswith(ext) for ext in (".wav", ".mp3", ".webm", ".m4a", ".ogg", ".mp4")):
            upload_name = f"{filename}.webm"

        files = {
            "file": (upload_name, audio_bytes, mime_type),
        }
        data: dict[str, Any] = {
            "model": model,
            "response_format": "json",
            "temperature": "0.0",
        }
        if language:
            data["language"] = language

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
            resp.raise_for_status()
            res_json = resp.json()
            text = res_json.get("text", "").strip()
            if not text:
                raise ValueError("Empty transcript received from Groq Whisper")
            return text

    async def _transcribe_gemini(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> str:
        raw_key = getattr(self.settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY", "")
        if not raw_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        if raw_key.startswith("AQ.AQ."):
            raw_key = raw_key[3:]
        elif raw_key.startswith("SAQ."):
            raw_key = raw_key[1:]

        model = getattr(self.settings, "VOICE_GEMINI_MODEL", "gemini-2.0-flash")
        # Ensure model is audio capable
        if model.startswith("gemini/"):
            model = model[len("gemini/"):]

        clean_mime = mime_type.split(";")[0].strip()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")

        prompt = "Transcribe this audio exactly. Output only the spoken text."
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": clean_mime,
                                "data": b64_audio,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
            },
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"X-goog-api-key": raw_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Parse transcript from candidates
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini")

            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts).strip()
            if not text:
                raise ValueError("Empty transcript received from Gemini")
            return text

    async def _transcribe_openrouter(
        self,
        audio_bytes: bytes,
        mime_type: str,
    ) -> str:
        api_key = getattr(self.settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        model = getattr(self.settings, "VOICE_OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        clean_mime = mime_type.split(";")[0].strip()
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")

        prompt = "Transcribe this audio exactly. Output only the spoken text."
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{clean_mime};base64,{b64_audio}",
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.0,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://asep-ai.vercel.app",
            "X-Title": "ASEP Universal Voice Typing",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=18.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No completion choices returned from OpenRouter")

            text = choices[0].get("message", {}).get("content", "").strip()
            if not text:
                raise ValueError("Empty transcript returned from OpenRouter")
            return text

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        content_type: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """
        Transcribe audio using 3-provider fallback chain:
        1. Groq (Whisper large v3)
        2. Gemini (gemini-2.0-flash inline audio)
        3. OpenRouter (gemini-2.0-flash-exp:free or configured)
        """
        mime_type = self._normalize_mime_type(content_type, filename)
        providers = self.provider_order
        fallbacks: list[dict[str, Any]] = []

        logger.info("Voice transcription request received: size=%d bytes, mime=%s, order=%s", len(audio_bytes), mime_type, providers)

        for i, provider in enumerate(providers):
            start_time = time.perf_counter()
            next_provider = providers[i + 1] if i + 1 < len(providers) else None

            try:
                if provider == "groq":
                    transcript = await self._transcribe_groq(
                        audio_bytes=audio_bytes,
                        filename=filename,
                        mime_type=mime_type,
                        language=language,
                    )
                elif provider == "gemini":
                    transcript = await self._transcribe_gemini(
                        audio_bytes=audio_bytes,
                        mime_type=mime_type,
                    )
                elif provider == "openrouter":
                    transcript = await self._transcribe_openrouter(
                        audio_bytes=audio_bytes,
                        mime_type=mime_type,
                    )
                else:
                    raise ValueError(f"Unknown voice provider: {provider}")

                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                logger.info(
                    "Voice transcription succeeded via provider '%s' in %.2fms",
                    provider,
                    latency_ms,
                )

                return {
                    "transcript": transcript,
                    "provider": provider,
                    "latency_ms": latency_ms,
                    "fallbacks": fallbacks,
                }

            except Exception as exc:
                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                err_msg = str(exc)
                logger.warning(
                    "Voice provider '%s' failed (%.2fms): %s",
                    provider,
                    latency_ms,
                    err_msg,
                )

                if next_provider:
                    provider_names = {
                        "groq": "Groq",
                        "gemini": "Gemini",
                        "openrouter": "OpenRouter",
                    }
                    from_name = provider_names.get(provider, provider.capitalize())
                    to_name = provider_names.get(next_provider, next_provider.capitalize())
                    toast_msg = f"{from_name} busy → switching to {to_name}"
                    logger.info("Auto-fallthrough: %s", toast_msg)
                    fallbacks.append({
                        "from": provider,
                        "to": next_provider,
                        "reason": err_msg,
                        "toast": toast_msg,
                    })

        # All providers failed
        all_fail_msg = "Voice transcription unavailable right now. Please type or try again in a minute."
        logger.error("All voice transcription providers failed: %s", fallbacks)
        raise VoiceTranscriptionError(all_fail_msg, fallbacks=fallbacks)
