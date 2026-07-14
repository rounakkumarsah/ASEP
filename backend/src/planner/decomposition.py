"""
ASEP — Task Decomposer
"""

import json
import logging

from src.planner.models import DecomposedPlan, Goal
from src.planner.prompts import TASK_DECOMPOSER_SYSTEM_PROMPT
from src.planner.provider import LLMProvider

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """Uses LLM completions to split a Goal into a list of dependent SubTasks."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def decompose(self, goal: Goal) -> DecomposedPlan:
        """Decompose a structured goal into a plan of logical subtasks."""
        logger.info(f"Decomposing goal: '{goal.parsed_title}'")
        
        goal_summary = {
            "title": goal.parsed_title,
            "success_criteria": goal.success_criteria
        }
        
        messages = [
            {"role": "system", "content": TASK_DECOMPOSER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Decompose this Goal:\n{json.dumps(goal_summary, indent=2)}"}
        ]
        
        response_content = await self.provider.chat_complete(messages, json_output=True)
        
        try:
            parsed_data = json.loads(response_content)
            # Strict validation through Pydantic model
            return DecomposedPlan.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"Failed to validate decomposed plan: {e}. Raw response: {response_content}")
            raise ValueError(f"Decomposer response is invalid: {e}")
