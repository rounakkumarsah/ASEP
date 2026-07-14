"""
ASEP — Goal Parser
"""

import json
import logging

from src.planner.models import Goal
from src.planner.prompts import GOAL_PARSER_SYSTEM_PROMPT
from src.planner.provider import LLMProvider

logger = logging.getLogger(__name__)


class GoalParser:
    """Uses LLM completions to convert raw text requests into structured Goal schemas."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def parse_goal(self, raw_goal: str) -> Goal:
        """Parse raw goal text into a validated Goal object."""
        logger.info(f"Parsing raw goal input: '{raw_goal[:60]}...'")
        
        messages = [
            {"role": "system", "content": GOAL_PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this goal: '{raw_goal}'"}
        ]
        
        response_content = await self.provider.chat_complete(messages, json_output=True)
        
        try:
            parsed_data = json.loads(response_content)
            # Strict validation through Pydantic model
            return Goal.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"Failed to validate goal output: {e}. Raw response: {response_content}")
            raise ValueError(f"Goal parser response is invalid: {e}")
