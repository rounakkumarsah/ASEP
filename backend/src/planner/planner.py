"""
ASEP — Planner Facade & Replanner Extension
"""

import json
import logging

from src.planner.decomposition import TaskDecomposer
from src.planner.goals import GoalParser
from src.planner.models import DecomposedPlan, Goal
from src.planner.plan import PlanManager
from src.planner.prompts import REPLANER_SYSTEM_PROMPT
from src.planner.provider import LLMProvider
from src.planner.validator import PlanValidator

logger = logging.getLogger(__name__)


class Planner:
    """The central planning engine coordinating goal parsing, task splitting, and validation."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self.goals = GoalParser(provider)
        self.decomposer = TaskDecomposer(provider)
        self.validator = PlanValidator()
        self.manager = PlanManager()

    async def create_plan(self, raw_goal: str) -> DecomposedPlan:
        """Parse raw goals, decompose them, validate DAG integrity, and sort topologically."""
        goal = await self.goals.parse_goal(raw_goal)
        plan = await self.decomposer.decompose(goal)
        
        # 1. Validate graph integrity
        is_valid, err = self.validator.validate_plan(plan)
        if not is_valid:
            logger.error(f"Planner generated an invalid execution plan: {err}")
            raise ValueError(f"Generated plan is structurally invalid: {err}")
            
        # 2. Reorder topologically to ensure dependencies run first
        return self.manager.reorder_plan_tasks(plan)


class Replanner(Planner):
    """Extends the basic Planner to handle dynamic updates on execution failures."""

    async def replan(
        self,
        current_plan: DecomposedPlan,
        failed_task_id: str,
        failure_report: str,
        goal: Goal
    ) -> DecomposedPlan:
        """Inject failure contexts into the LLM loop to output an adapted, validated DecomposedPlan."""
        logger.info(f"Replanning triggered for failed task: '{failed_task_id}'")
        
        context = {
            "original_goal": {
                "title": goal.parsed_title,
                "success_criteria": goal.success_criteria
            },
            "failed_task_id": failed_task_id,
            "failure_report": failure_report,
            "current_plan": current_plan.model_dump()
        }
        
        messages = [
            {"role": "system", "content": REPLANER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Replan based on this failure state:\n{json.dumps(context, indent=2)}"}
        ]
        
        response_content = await self.provider.chat_complete(messages, json_output=True)
        
        try:
            parsed_data = json.loads(response_content)
            new_plan = DecomposedPlan.model_validate(parsed_data)
            
            # Validate integrity of the adjusted plan
            is_valid, err = self.validator.validate_plan(new_plan)
            if not is_valid:
                logger.error(f"Replanner generated an invalid execution plan: {err}")
                raise ValueError(f"Replanned plan is structurally invalid: {err}")
                
            return self.manager.reorder_plan_tasks(new_plan)
        except Exception as e:
            logger.error(f"Failed to validate replanned output: {e}. Raw response: {response_content}")
            raise ValueError(f"Replanner response validation failed: {e}")
