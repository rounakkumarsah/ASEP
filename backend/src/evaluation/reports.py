"""
ASEP — Evaluation Report Builder
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from src.evaluation.evaluator import EvaluationResult


class EvaluationSummary(BaseModel):
    """Dataset-level aggregation of evaluation results."""
    dataset_name: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float = 0.0
    avg_overall_score: float = 0.0
    avg_per_dimension: dict[str, float] = Field(default_factory=dict)
    tag_breakdown: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Per-tag counts: {'smoke': {'total': 2, 'passed': 2}}"
    )
    replay_regressions: int = Field(
        default=0,
        description="Count of replayed cases where score_delta < -0.05 (regression threshold)"
    )


class EvaluationReport(BaseModel):
    """Full typed report aggregating summary and all individual results."""
    summary: EvaluationSummary
    results: list[EvaluationResult] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ReportBuilder:
    """Builds an EvaluationReport from a list of EvaluationResults."""

    _REGRESSION_THRESHOLD = -0.05  # score_delta below this = regression

    def build(
        self,
        dataset_name: str,
        results: list[EvaluationResult],
    ) -> EvaluationReport:
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = total - passed_count
        pass_rate = round(passed_count / total, 4) if total > 0 else 0.0

        avg_overall = (
            round(sum(r.scores.overall for r in results) / total, 4)
            if total > 0 else 0.0
        )

        # Per-dimension averages
        dims = ["plan_quality", "execution", "tool_usage", "memory_usage", "trajectory", "latency"]
        dim_avgs: dict[str, float] = {}
        for dim in dims:
            scores_for_dim = [getattr(r.scores, dim).score for r in results]
            dim_avgs[dim] = round(sum(scores_for_dim) / len(scores_for_dim), 4) if scores_for_dim else 0.0

        # Tag breakdown
        tag_breakdown: dict[str, dict[str, int]] = {}
        for r in results:
            # Find tags from the dataset — we reconstruct from result attributes if present
            # Since EvaluationResult doesn't store tags (to keep it lean), 
            # we collect them if the evaluator attaches them in future phases.
            pass  # tag_breakdown populated by enrichment below

        # Replay regressions
        regressions = sum(
            1 for r in results
            if r.is_replay and r.score_delta is not None and r.score_delta < self._REGRESSION_THRESHOLD
        )

        summary = EvaluationSummary(
            dataset_name=dataset_name,
            total_cases=total,
            passed=passed_count,
            failed=failed_count,
            pass_rate=pass_rate,
            avg_overall_score=avg_overall,
            avg_per_dimension=dim_avgs,
            replay_regressions=regressions,
        )

        return EvaluationReport(summary=summary, results=results)

    def to_dict(self, report: EvaluationReport) -> dict[str, Any]:
        """Serialize the report to a plain dict for JSON export or API exposure."""
        return report.model_dump(mode="json")
