"""
ASEP — Reflection Generators
"""

import json
import logging
from typing import Any

from src.evaluation.metrics import SessionMetrics
from src.evaluation.trajectory import Trajectory
from src.evaluation.scoring import AllScores
from src.planner.provider import LLMProvider
from src.reflection.models import FailureAnalysis, ReflectionItem, ReflectionReport

logger = logging.getLogger(__name__)


_REFLECTION_SYSTEM_PROMPT = """You are an expert AI software engineering supervisor evaluating an agent's execution session.
Your task is to analyze the agent's trajectory, metrics, and scores to extract actionable lessons and perform failure analysis if the session failed.

Rules:
1. Output strictly valid JSON matching the provided schema.
2. Structure every lesson with: failure_description, root_cause, evidence, recommendation, and confidence.
3. Categorize lessons strictly using the allowed enum values: planning, tool_usage, memory, execution, context, policy, performance.
4. Recommendations must be actionable IF-THEN rules or concrete guidelines for future agent behavior. Do not suggest rewriting code directly.
5. If the session passed, provide success analysis (what went well, edge cases avoided). If failed, perform deep root-cause failure analysis.
"""


class ReflectionGenerator:
    """Generates structured ReflectionReports using an LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def generate_reflection(
        self,
        session_id: str,
        run_id: str,
        passed: bool,
        trajectory: Trajectory,
        metrics: SessionMetrics,
        scores: AllScores,
    ) -> ReflectionReport:
        """Call the LLM to generate a comprehensive ReflectionReport."""

        # Serialize inputs
        traj_data = [{"step": s.step_index, "event": s.event_type, "status": s.status, "tool": s.tool_name, "summary": s.payload_summary} for s in trajectory.steps]
        
        # Build prompt
        prompt = f"""
Session Analysis Request
------------------------
Session Passed: {passed}

Scores:
- Plan Quality: {scores.plan_quality.score}
- Execution: {scores.execution.score}
- Tool Usage: {scores.tool_usage.score}
- Trajectory: {scores.trajectory.score}
- Overall: {scores.overall}

Metrics summary:
- Tasks: {metrics.task_count}, Succeeded: {metrics.succeeded}, Failed: {metrics.failed}
- Tool Invocations: {metrics.tool_invocations}
- Latency (ms): {metrics.latency.total_ms}

Trajectory steps (abbreviated):
{json.dumps(traj_data[:20], indent=2)}
{f'... and {len(traj_data) - 20} more steps' if len(traj_data) > 20 else ''}

Generate a ReflectionReport JSON object containing:
1. `passed`: boolean
2. `failure_analysis`: object with `category` (tool_failure, planning_error, timeout, permission_denied, logic_error, unknown) and `contributing_factors` (array of strings). Only include if passed == false.
3. `items`: array of extracted lessons. Each item must have:
   - category (planning, tool_usage, memory, execution, context, policy, performance)
   - failure_description
   - root_cause
   - evidence
   - recommendation
   - confidence (0.0 to 1.0)
"""
        messages = [
            {"role": "system", "content": _REFLECTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        logger.info(f"[{session_id}] Generating reflection report via LLM")
        raw_json = await self._provider.chat_complete(messages, json_output=True)
        
        try:
            data = json.loads(raw_json)
            # Inject known IDs
            data["session_id"] = session_id
            data["run_id"] = run_id
            return ReflectionReport.model_validate(data)
        except Exception as exc:
            logger.error(f"[{session_id}] Failed to parse reflection JSON: {exc}\nRaw: {raw_json}")
            # Fallback to empty report
            return ReflectionReport(session_id=session_id, run_id=run_id, passed=passed)
