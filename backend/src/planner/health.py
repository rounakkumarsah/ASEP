"""
ASEP — Planner Health Check
"""

import logging

from src.planner.provider import OpenAICompatibleLLMProvider

logger = logging.getLogger(__name__)


async def planner_health_check() -> bool:
    """Verifies that the LLM Chat Completion provider is reachable and responsive.
    
    Returns:
        True if the provider responds to a simple ping chat completion, False otherwise.
    """
    provider = None
    try:
        provider = OpenAICompatibleLLMProvider(timeout=3.0)
        messages = [{"role": "user", "content": "ping"}]
        await provider.chat_complete(messages)
        return True
    except Exception as e:
        logger.warning(f"Planner LLM health check failed: {e}")
        return False
    finally:
        if provider:
            await provider.close()
