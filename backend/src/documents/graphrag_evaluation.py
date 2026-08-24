"""
ASEP — GraphRAG Evaluation & Metrics Engine
============================================
Evaluates retrieval precision, recall, latency, token usage, and cost metrics
for Hybrid GraphRAG performance monitoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.documents.query_pipeline import RetrievalPipelineOutput

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    precision: float
    recall: float
    latency_ms: float
    token_usage: int
    estimated_cost_usd: float
    deduplication_efficiency: float


class GraphRAGEvaluator:
    """Evaluates accuracy, efficiency, latency, and cost metrics of GraphRAG runs."""

    def __init__(self, cost_per_1k_tokens: float = 0.00015) -> None:
        self.cost_per_1k_tokens = cost_per_1k_tokens

    def evaluate_run(
        self,
        output: RetrievalPipelineOutput,
        ground_truth_chunk_ids: list[str] | None = None,
    ) -> EvaluationMetrics:
        retrieved_ids = [c.chunk_id for c in output.citations]
        precision = 0.0
        recall = 0.0

        if ground_truth_chunk_ids and retrieved_ids:
            hits = set(retrieved_ids).intersection(set(ground_truth_chunk_ids))
            precision = len(hits) / len(retrieved_ids)
            recall = len(hits) / len(ground_truth_chunk_ids)
        elif retrieved_ids:
            # Fallback heuristic: all returned items considered relevant in ungrounded mode
            precision = 1.0
            recall = 1.0

        token_count = output.merged_context.token_estimate
        estimated_cost = (token_count / 1000.0) * self.cost_per_1k_tokens

        dedup_count = output.merged_context.deduplicated_count
        total_chunks = len(output.merged_context.chunks) + dedup_count
        dedup_eff = (dedup_count / total_chunks) if total_chunks > 0 else 0.0

        metrics = EvaluationMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            latency_ms=output.latency_ms,
            token_usage=token_count,
            estimated_cost_usd=round(estimated_cost, 6),
            deduplication_efficiency=round(dedup_eff, 4),
        )

        logger.info(
            "GraphRAG Run Evaluated: precision=%.2f, recall=%.2f, latency=%.2fms, cost=$%.6f",
            metrics.precision,
            metrics.recall,
            metrics.latency_ms,
            metrics.estimated_cost_usd,
        )

        return metrics
