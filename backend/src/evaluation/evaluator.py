"""
ASEP — Evaluation Orchestrator

Runs a single EvaluationCase or a full EvaluationDataset through a generic async
AgentRunner callable. Preserves all four run identifiers in every result.
Supports replay for regression testing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable

from pydantic import BaseModel, Field

from src.agent.events import AgentEvent, AgentEventType
from src.evaluation.datasets import EvaluationCase, EvaluationDataset
from src.evaluation.metrics import MetricsCollector, SessionMetrics
from src.evaluation.scoring import AllScores, Scorer
from src.evaluation.tracing import Trace, TraceStore, Tracer
from src.evaluation.trajectory import Trajectory, TrajectoryAnalysis, TrajectoryAnalyzer

logger = logging.getLogger(__name__)

# Generic async runner type — accepts a goal string, yields AgentEvents
AgentRunner = Callable[[str], AsyncGenerator[AgentEvent, None]]


# ─────────────────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────────────────

class EvaluationResult(BaseModel):
    """Complete typed result for one evaluation case run."""
    case_id: str
    goal: str

    # All four identifiers preserved
    session_id: str
    run_id: str
    thread_id: str
    trace_id: str

    trajectory: Trajectory
    trajectory_analysis: TrajectoryAnalysis
    metrics: SessionMetrics
    scores: AllScores

    passed: bool
    error: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # Replay metadata
    is_replay: bool = False
    baseline_overall_score: float | None = None
    score_delta: float | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Evaluator
# ─────────────────────────────────────────────────────────────────────────────

class Evaluator:
    """Drives evaluation cases through a generic AgentRunner and produces typed results.

    Design constraints:
      - Accepts any callable matching AgentRunner — not coupled to Agent class.
      - evaluate_dataset() is strictly sequential for deterministic ordering.
      - Measurement-only: results are never fed back to the runner.
    """

    def __init__(self, runner: AgentRunner, trace_store: TraceStore | None = None) -> None:
        self._runner = runner
        self._trace_store = trace_store if trace_store is not None else TraceStore()
        self._trajectory_analyzer = TrajectoryAnalyzer()
        self._metrics_collector = MetricsCollector()
        self._scorer = Scorer()

    # ──────────────────────────────────────────────────────────────────────────
    # Single case evaluation
    # ──────────────────────────────────────────────────────────────────────────

    async def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        """Run one evaluation case end-to-end and return a fully scored result."""
        logger.info(f"Evaluating case '{case.id}': {case.goal!r}")
        trace_id = str(uuid.uuid4())

        # Temporary identity placeholders — resolved from SESSION_STARTED event
        session_id = "pending"
        run_id = "pending"
        thread_id = "pending"
        error: str | None = None
        events: list[AgentEvent] = []

        # Create a trace scoped to this evaluation run
        trace = Trace(
            trace_id=trace_id,
            session_id=session_id,
            thread_id=thread_id,
            run_id=run_id,
        )
        tracer = Tracer(trace)

        try:
            async with tracer.span("evaluation_run", case_id=case.id, goal=case.goal):
                async with tracer.span("agent_execution"):
                    async for ev in self._runner(case.goal):
                        events.append(ev)

                        # Capture identity from the first SESSION_STARTED event
                        if ev.event_type == AgentEventType.SESSION_STARTED:
                            session_id = ev.session_id
                            run_id = ev.payload.get("run_id", run_id)
                            thread_id = ev.payload.get("thread_id", thread_id)
                            # Backfill trace identity
                            trace.session_id = session_id
                            trace.run_id = run_id
                            trace.thread_id = thread_id

        except Exception as exc:
            error = str(exc)
            logger.error(f"Evaluation case '{case.id}' raised exception: {exc}")

        # Store trace
        self._trace_store.add(trace)

        # Build trajectory
        trajectory = self._trajectory_analyzer.build_from_events(
            events, session_id, thread_id, run_id, trace_id
        )
        traj_analysis = self._trajectory_analyzer.analyze(trajectory)

        # Collect metrics
        metrics = self._metrics_collector.collect(
            events, session_id, run_id, thread_id, trace_id
        )

        # Score all six dimensions
        # We don't have a live plan object here — reconstruct a lightweight proxy from events
        plan_score = self._score_plan_from_events(events)
        exec_score = self._scorer.score_execution(metrics)
        tool_score = self._scorer.score_tool_usage(metrics)
        mem_score = self._scorer.score_memory_usage(metrics)
        traj_score = self._scorer.score_trajectory(traj_analysis)
        lat_score = self._scorer.score_latency(metrics.latency)

        scores = self._scorer.compute_overall(
            plan=plan_score,
            execution=exec_score,
            tool=tool_score,
            memory=mem_score,
            trajectory=traj_score,
            latency=lat_score,
            pass_threshold=case.pass_threshold,
        )

        result = EvaluationResult(
            case_id=case.id,
            goal=case.goal,
            session_id=session_id,
            run_id=run_id,
            thread_id=thread_id,
            trace_id=trace_id,
            trajectory=trajectory,
            trajectory_analysis=traj_analysis,
            metrics=metrics,
            scores=scores,
            passed=scores.passed,
            error=error,
        )
        logger.info(
            f"Case '{case.id}' — passed={result.passed}, "
            f"overall={scores.overall:.3f}, error={error!r}"
        )
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Dataset evaluation (sequential, deterministic)
    # ──────────────────────────────────────────────────────────────────────────

    async def evaluate_dataset(self, dataset: EvaluationDataset) -> list[EvaluationResult]:
        """Run every case in the dataset sequentially and return all results."""
        results: list[EvaluationResult] = []
        for case in dataset.cases:
            result = await self.evaluate_case(case)
            results.append(result)
        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Replay (regression testing)
    # ──────────────────────────────────────────────────────────────────────────

    async def replay(
        self,
        case: EvaluationCase,
        baseline: EvaluationResult | None = None,
    ) -> EvaluationResult:
        """Re-run a case for regression testing. Compares against an optional baseline.

        The result is tagged with is_replay=True, baseline_overall_score, and score_delta
        so regression dashboards can surface regressions automatically.
        """
        logger.info(f"Replaying case '{case.id}' for regression testing")
        result = await self.evaluate_case(case)
        result.is_replay = True

        if baseline is not None:
            result.baseline_overall_score = baseline.scores.overall
            result.score_delta = round(result.scores.overall - baseline.scores.overall, 4)
            logger.info(
                f"Replay '{case.id}' — Δscore={result.score_delta:+.3f} "
                f"(was {baseline.scores.overall:.3f}, now {result.scores.overall:.3f})"
            )

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _score_plan_from_events(self, events: list[AgentEvent]):
        """Build a lightweight PlanQualityScore from the PLAN_CREATED event payload
        when we don't have direct access to the DecomposedPlan object."""
        from src.evaluation.scoring import PlanQualityScore

        for ev in events:
            if ev.event_type == AgentEventType.PLAN_CREATED:
                tasks = ev.payload.get("tasks", [])
                n = len(tasks)
                if n == 0:
                    return PlanQualityScore(score=0.0)
                independent = sum(1 for t in tasks if not t.get("depends_on"))
                with_tool = sum(1 for t in tasks if t.get("tool_name"))
                parallelism = round(independent / n, 4)
                tool_ratio = round(with_tool / n, 4)
                size_score = 1.0 if 2 <= n <= 10 else (0.6 if n == 1 else 0.7)
                score = round(size_score * 0.5 + parallelism * 0.3 + tool_ratio * 0.2, 4)
                return PlanQualityScore(
                    task_count=n,
                    parallelism_ratio=parallelism,
                    tool_assignment_ratio=tool_ratio,
                    score=score,
                )
        # No plan event found — plan phase may have failed
        return PlanQualityScore(score=0.0)
