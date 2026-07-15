"""
ASEP — Heuristic Evaluation Scorer

Six independent scoring dimensions, all pure Python math — zero LLM calls.
Weights and thresholds are defined as module-level constants for transparency.
"""

from pydantic import BaseModel, Field

from src.evaluation.metrics import LatencyMetrics, MemoryMetrics, SessionMetrics
from src.evaluation.trajectory import Trajectory, TrajectoryAnalysis
from src.planner.models import DecomposedPlan


# ─────────────────────────────────────────────────────────────────────────────
# Score dimension models  (each 0.0 – 1.0)
# ─────────────────────────────────────────────────────────────────────────────

class PlanQualityScore(BaseModel):
    """Measures the structural quality of the generated plan."""
    task_count: int = 0
    parallelism_ratio: float = 0.0   # tasks with no deps / total
    tool_assignment_ratio: float = 0.0  # tasks with tool_name set / total
    score: float = 0.0


class ExecutionScore(BaseModel):
    """Measures how cleanly the plan was executed."""
    success_rate: float = 0.0
    retry_rate: float = 0.0
    timeout_rate: float = 0.0
    skip_rate: float = 0.0
    score: float = 0.0


class ToolUsageScore(BaseModel):
    """Measures how effectively tools were invoked."""
    tools_invoked: int = 0
    tools_succeeded: int = 0
    tools_failed: int = 0
    success_ratio: float = 0.0
    score: float = 0.0


class MemoryUsageScore(BaseModel):
    """Measures breadth of memory layer utilisation."""
    memory_events: int = 0
    layers_used: int = 0
    episodic_writes: int = 0
    score: float = 0.0


class TrajectoryScore(BaseModel):
    """Measures path efficiency and completeness."""
    path_efficiency_ratio: float = 0.0
    steps_per_task: float = 0.0
    had_cancellation: bool = False
    valid_alternative_path: bool = False
    score: float = 0.0


class LatencyScore(BaseModel):
    """Grades overall session latency."""
    total_ms: float = 0.0
    planning_ms: float = 0.0
    execution_ms: float = 0.0
    grade: str = "unknown"   # excellent | good | acceptable | slow
    score: float = 0.0


class AllScores(BaseModel):
    """All six scoring dimensions for one evaluation run."""
    plan_quality: PlanQualityScore = Field(default_factory=PlanQualityScore)
    execution: ExecutionScore = Field(default_factory=ExecutionScore)
    tool_usage: ToolUsageScore = Field(default_factory=ToolUsageScore)
    memory_usage: MemoryUsageScore = Field(default_factory=MemoryUsageScore)
    trajectory: TrajectoryScore = Field(default_factory=TrajectoryScore)
    latency: LatencyScore = Field(default_factory=LatencyScore)
    overall: float = 0.0
    passed: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Weights (must sum to 1.0)
# ─────────────────────────────────────────────────────────────────────────────
_W_PLAN = 0.15
_W_EXEC = 0.30
_W_TOOL = 0.15
_W_MEM  = 0.10
_W_TRAJ = 0.20
_W_LAT  = 0.10

# Latency grade thresholds (ms)
_LAT_EXCELLENT = 5_000
_LAT_GOOD      = 30_000
_LAT_ACCEPTABLE = 60_000


# ─────────────────────────────────────────────────────────────────────────────
# Scorer
# ─────────────────────────────────────────────────────────────────────────────

class Scorer:
    """Computes all six evaluation dimensions from structured evaluation data.

    All methods are pure functions — same inputs always produce the same score.
    """

    # ── 1. Plan quality ──────────────────────────────────────────────────────

    def score_plan(self, plan: DecomposedPlan) -> PlanQualityScore:
        n = len(plan.tasks)
        if n == 0:
            return PlanQualityScore(score=0.0)

        independent = sum(1 for t in plan.tasks if not t.depends_on)
        with_tool = sum(1 for t in plan.tasks if t.tool_name)

        parallelism = round(independent / n, 4)
        tool_ratio = round(with_tool / n, 4)

        # Reward plans that decompose meaningfully (2-10 tasks is ideal)
        size_score = 1.0 if 2 <= n <= 10 else (0.6 if n == 1 else 0.7)
        score = round(size_score * 0.5 + parallelism * 0.3 + tool_ratio * 0.2, 4)

        return PlanQualityScore(
            task_count=n,
            parallelism_ratio=parallelism,
            tool_assignment_ratio=tool_ratio,
            score=score,
        )

    # ── 2. Execution ─────────────────────────────────────────────────────────

    def score_execution(self, metrics: SessionMetrics) -> ExecutionScore:
        n = metrics.task_count or 1
        succeeded = metrics.succeeded
        failed = metrics.failed
        skipped = metrics.skipped

        # Count retried tasks (attempts > 1) from per_task list
        retried = sum(1 for t in metrics.per_task if t.attempts > 1)
        timed_out = sum(1 for t in metrics.per_task if t.status == "timed_out")

        success_rate = round(succeeded / n, 4)
        retry_rate = round(retried / n, 4)
        timeout_rate = round(timed_out / n, 4)
        skip_rate = round(skipped / n, 4)

        score = round(
            success_rate * 0.70
            + (1 - retry_rate) * 0.15
            + (1 - timeout_rate) * 0.10
            + (1 - skip_rate) * 0.05,
            4,
        )

        return ExecutionScore(
            success_rate=success_rate,
            retry_rate=retry_rate,
            timeout_rate=timeout_rate,
            skip_rate=skip_rate,
            score=max(0.0, min(1.0, score)),
        )

    # ── 3. Tool usage ────────────────────────────────────────────────────────

    def score_tool_usage(self, metrics: SessionMetrics) -> ToolUsageScore:
        invoked = metrics.tool_invocations
        # Derive succeeded/failed from per_task: tasks with a tool that succeeded/failed
        succeeded = sum(
            1 for t in metrics.per_task
            if t.tool_name and t.status == "succeeded"
        )
        failed_count = sum(
            1 for t in metrics.per_task
            if t.tool_name and t.status in ("failed", "timed_out")
        )

        if invoked == 0:
            # No tools configured — neutral score (tools may not be needed)
            return ToolUsageScore(score=0.5)

        ratio = round(succeeded / invoked, 4) if invoked else 0.0
        score = round(ratio * 0.8 + (1 - failed_count / max(invoked, 1)) * 0.2, 4)

        return ToolUsageScore(
            tools_invoked=invoked,
            tools_succeeded=succeeded,
            tools_failed=failed_count,
            success_ratio=ratio,
            score=max(0.0, min(1.0, score)),
        )

    # ── 4. Memory usage ──────────────────────────────────────────────────────

    def score_memory_usage(self, metrics: SessionMetrics) -> MemoryUsageScore:
        mem = metrics.memory
        layers = len(mem.layers_used)
        events = mem.total_memory_events

        # Reward using multiple memory layers (max 4)
        layer_score = min(layers / 4, 1.0)
        event_score = min(events / 5, 1.0)   # ≥5 events = full marks
        score = round(layer_score * 0.6 + event_score * 0.4, 4)

        return MemoryUsageScore(
            memory_events=events,
            layers_used=layers,
            episodic_writes=mem.episodic_writes,
            score=score,
        )

    # ── 5. Trajectory ────────────────────────────────────────────────────────

    def score_trajectory(self, analysis: TrajectoryAnalysis) -> TrajectoryScore:
        efficiency = analysis.path_efficiency_ratio  # 0.0 – 1.0

        # Alternative paths that still succeed are not penalised
        if analysis.valid_alternative_path:
            efficiency = max(efficiency, 0.8)

        cancellation_penalty = 0.3 if analysis.had_cancellation else 0.0

        # Penalise very high steps-per-task overhead (>5 steps per task = bloated)
        overhead_ratio = min(analysis.steps_per_task / 5.0, 1.0)
        overhead_score = 1.0 - overhead_ratio * 0.2

        score = round(
            efficiency * 0.70
            + overhead_score * 0.30
            - cancellation_penalty,
            4,
        )

        return TrajectoryScore(
            path_efficiency_ratio=efficiency,
            steps_per_task=analysis.steps_per_task,
            had_cancellation=analysis.had_cancellation,
            valid_alternative_path=analysis.valid_alternative_path,
            score=max(0.0, min(1.0, score)),
        )

    # ── 6. Latency ───────────────────────────────────────────────────────────

    def score_latency(self, latency: LatencyMetrics) -> LatencyScore:
        total = latency.total_ms

        if total < _LAT_EXCELLENT:
            grade, score = "excellent", 1.0
        elif total < _LAT_GOOD:
            grade, score = "good", 0.8
        elif total < _LAT_ACCEPTABLE:
            grade, score = "acceptable", 0.5
        else:
            grade, score = "slow", 0.2

        return LatencyScore(
            total_ms=round(total, 2),
            planning_ms=round(latency.planning_ms, 2),
            execution_ms=round(latency.execution_ms, 2),
            grade=grade,
            score=score,
        )

    # ── Overall ──────────────────────────────────────────────────────────────

    def compute_overall(
        self,
        plan: PlanQualityScore,
        execution: ExecutionScore,
        tool: ToolUsageScore,
        memory: MemoryUsageScore,
        trajectory: TrajectoryScore,
        latency: LatencyScore,
        pass_threshold: float = 0.6,
    ) -> AllScores:
        overall = round(
            plan.score      * _W_PLAN
            + execution.score * _W_EXEC
            + tool.score      * _W_TOOL
            + memory.score    * _W_MEM
            + trajectory.score * _W_TRAJ
            + latency.score   * _W_LAT,
            4,
        )
        return AllScores(
            plan_quality=plan,
            execution=execution,
            tool_usage=tool,
            memory_usage=memory,
            trajectory=trajectory,
            latency=latency,
            overall=overall,
            passed=overall >= pass_threshold,
        )
