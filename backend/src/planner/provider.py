"""
ASEP — Provider-Agnostic LLM Client
"""

import json
import logging
from abc import ABC, abstractmethod

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM Chat Completion providers."""

    @abstractmethod
    async def chat_complete(
        self,
        messages: list[dict[str, str]],
        json_output: bool = False
    ) -> str:
        """Execute chat completion request."""
        pass


class OpenAICompatibleLLMProvider(LLMProvider):
    """LLM client that communicates with any OpenAI-compatible chat completions endpoint."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None, model: str | None = None, timeout: float = 90.0) -> None:
        settings = get_settings()
        self.api_url = api_url or settings.LLM_API_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        self.client = httpx.AsyncClient(headers=headers, timeout=timeout)

    async def chat_complete(
        self,
        messages: list[dict[str, str]],
        json_output: bool = False
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        if json_output:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            logger.debug(f"Calling LLM provider at {self.api_url} with model {self.model}")
            response = await self.client.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM Chat Completion: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()
