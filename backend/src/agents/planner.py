"""
ASEP — LangGraph Planner Node
==============================
Decomposes a high-level goal into an ordered list of executable subtasks
using an LLM via AIRuntimeService.

Fallback strategy:
  1. Call AIRuntimeService with a structured decomposition prompt.
  2. Parse the JSON array of tasks from the LLM response.
  3. If parsing fails, extract bullet-point tasks from the raw text.
  4. If LLM is unavailable, return an error-state plan that surfaces the
     failure to the graph rather than silently producing stub output.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.agents.state import AgentState

logger = logging.getLogger(__name__)

_PLANNER_SYSTEM_PROMPT = """You are a senior software engineer acting as a task planner for an autonomous AI agent.

Your role is to decompose a high-level goal into a precise, ordered list of concrete executable subtasks.

Rules:
- Output ONLY a valid JSON array of strings. Nothing else. No markdown, no explanation.
- Each task must be a single, actionable sentence.
- Tasks must be ordered by execution dependency (earlier tasks enable later ones).
- Minimum 3 tasks, maximum 10 tasks.
- Each task must be concrete and verifiable.
- Do NOT include placeholders, stubs, or meta-instructions like "identify tools".

Example output for goal "Deploy a FastAPI service to AWS Lambda":
[
  "Write a Dockerfile with Python 3.12 slim base image and install requirements.txt",
  "Configure AWS Lambda handler using Mangum adapter wrapping the FastAPI app",
  "Create an AWS Lambda function with 512 MB memory and 30s timeout via AWS CLI",
  "Set required environment variables (DATABASE_URL, SECRET_KEY) in Lambda configuration",
  "Run smoke test by invoking the Lambda function URL and verifying HTTP 200 response"
]"""


async def planner_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node: Planner.

    Receives:
        state.goal  — The user's high-level task description.

    Produces:
        state.plan  — A list of decomposed subtasks from LLM decomposition.

    Args:
        state: Current agent state.

    Returns:
        Updated state with plan populated.
    """
    logger.info("Planner node invoked", extra={"run_id": str(state.get("run_id")), "goal": state.get("goal")})

    goal = state.get("goal", "")
    if not goal or not goal.strip():
        return {
            "plan": [],
            "error": "Planner received an empty goal. Cannot decompose.",
            "is_complete": True,
        }

    plan = await _decompose_with_llm(goal)
    logger.info("Plan generated", extra={"run_id": str(state.get("run_id")), "task_count": len(plan)})
    return {"plan": plan}


async def _decompose_with_llm(goal: str) -> list[str]:
    """Call AIRuntimeService to decompose the goal. Returns a list of task strings."""
    try:
        from src.ai_runtime.contracts import CompletionRequest, Message
        from src.ai_runtime.service import AIRuntimeService
        from src.config.settings import get_settings

        settings = get_settings()
        model = settings.LLM_MODEL or "qwen2.5-coder:7b"

        runtime = AIRuntimeService()
        request = CompletionRequest(
            messages=[
                Message(role="system", content=_PLANNER_SYSTEM_PROMPT),
                Message(role="user", content=f"Decompose this goal into executable subtasks:\n\n{goal}"),
            ],
            model=model,
            temperature=0.3,
            max_tokens=1024,
        )
        response = await runtime.complete(request)
        raw = response.text.strip()
        return _parse_plan(raw, goal)

    except Exception as exc:
        logger.error("LLM planner failed: %s", exc)
        # Fail loud — surface the error in the plan rather than hiding it with stubs
        return [
            f"[PLANNING_ERROR] LLM decomposition unavailable: {type(exc).__name__}",
            "Check AI provider configuration (LLM_API_URL, LLM_MODEL) and retry the agent run.",
        ]



def _parse_plan(raw: str, goal: str) -> list[str]:
    """Parse LLM output into a list of task strings.

    Attempts JSON array parsing first; falls back to bullet-point extraction.
    """
    # Attempt 1: parse JSON array directly
    try:
        candidate = raw
        # Strip markdown code fences if present
        if "```" in candidate:
            candidate = re.sub(r"```(?:json)?\s*", "", candidate).strip().rstrip("`").strip()
        tasks = json.loads(candidate)
        if isinstance(tasks, list) and all(isinstance(t, str) for t in tasks):
            clean = [t.strip() for t in tasks if t.strip()]
            if clean:
                return clean
    except (json.JSONDecodeError, ValueError):
        pass

    # Attempt 2: extract bullet/numbered list items
    lines = raw.splitlines()
    tasks = []
    for line in lines:
        line = line.strip()
        # Match "- task", "* task", "1. task", "1) task"
        match = re.match(r"^(?:[-*•]|\d+[.):])\s+(.+)", line)
        if match:
            tasks.append(match.group(1).strip())

    if tasks:
        return tasks

    # Attempt 3: use non-empty lines as tasks (last resort)
    tasks = [line.strip() for line in lines if len(line.strip()) > 10]
    if tasks:
        return tasks[:10]  # Cap at 10

    # Completely unparseable — return error task
    logger.warning("Planner could not parse LLM output for goal: %s", goal)
    return [
        "[PARSING_ERROR] LLM response could not be parsed into a task list.",
        "Retry the agent run or simplify the goal description.",
    ]

