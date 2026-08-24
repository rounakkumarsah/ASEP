"""
ASEP — Unit Tests for GraphRAG Evaluation Engine
"""

from src.documents.context_merge import MergedContext
from src.documents.graphrag_evaluation import GraphRAGEvaluator
from src.documents.query_pipeline import Citation, RetrievalPipelineOutput, RetrievalStrategy


def test_graphrag_evaluator():
    evaluator = GraphRAGEvaluator()

    output = RetrievalPipelineOutput(
        query="GraphRAG query",
        strategy_used=RetrievalStrategy.HYBRID,
        merged_context=MergedContext(
            chunks=[{"chunk_id": "c1", "text": "text"}],
            graph_facts=[],
            formatted_context="text",
            token_estimate=500,
            deduplicated_count=1,
        ),
        citations=[
            Citation(source_id="d1", filename="doc.txt", file_path="/path", chunk_id="c1", relevance_score=0.9)
        ],
        latency_ms=120.5,
    )

    metrics = evaluator.evaluate_run(output, ground_truth_chunk_ids=["c1", "c2"])

    assert metrics.precision == 1.0
    assert metrics.recall == 0.5
    assert metrics.latency_ms == 120.5
    assert metrics.token_usage == 500
    assert metrics.estimated_cost_usd > 0.0
