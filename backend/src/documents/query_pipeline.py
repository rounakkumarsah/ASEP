"""
ASEP — Query Analysis & Retrieval Pipeline Router
==================================================
Classifies user intent, selects retrieval strategies, executes hybrid search,
re-ranks results, and attaches source citations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.documents.context_merge import ContextMergeEngine, MergedContext
from src.documents.hybrid_retrieval import HybridRetrievalPipeline, HybridSearchResult

logger = logging.getLogger(__name__)


class RetrievalStrategy(str, Enum):
    VECTOR_ONLY = "vector_only"
    GRAPH_ONLY = "graph_only"
    HYBRID = "hybrid"
    MULTI_HOP_GRAPH = "multi_hop_graph"


@dataclass
class Citation:
    source_id: str
    filename: Optional[str]
    file_path: Optional[str]
    chunk_id: str
    relevance_score: float


@dataclass
class RetrievalPipelineOutput:
    query: str
    strategy_used: RetrievalStrategy
    merged_context: MergedContext
    citations: List[Citation]
    latency_ms: float


class QueryIntentAnalyzer:
    """Analyzes user query to detect intent and choose retrieval strategy."""

    def analyze_intent(self, query: str) -> RetrievalStrategy:
        q_lower = query.lower()
        graph_keywords = ["relationship", "connected to", "hierarchy", "graph", "link", "depend", "how is"]
        factual_keywords = ["what is", "define", "summary", "list", "code", "file"]

        is_graph_heavy = any(k in q_lower for k in graph_keywords)
        is_factual = any(k in q_lower for k in factual_keywords)

        if is_graph_heavy and not is_factual:
            return RetrievalStrategy.MULTI_HOP_GRAPH
        elif is_graph_heavy:
            return RetrievalStrategy.HYBRID
        else:
            return RetrievalStrategy.HYBRID


class RetrievalPipeline:
    """Orchestrates Query Analysis, Hybrid Retrieval, Context Merging, and Citation Generation."""

    def __init__(
        self,
        hybrid_pipeline: HybridRetrievalPipeline,
        context_merger: Optional[ContextMergeEngine] = None,
    ) -> None:
        self.hybrid = hybrid_pipeline
        self.analyzer = QueryIntentAnalyzer()
        self.context_merger = context_merger or ContextMergeEngine()

    async def execute_retrieval(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> RetrievalPipelineOutput:
        import time
        start_time = time.perf_counter()

        strategy = self.analyzer.analyze_intent(query)
        logger.info("Retrieved intent strategy for query '%s': %s", query, strategy)

        # Execute hybrid retrieval
        hybrid_results: List[HybridSearchResult] = await self.hybrid.search_hybrid(
            query=query,
            limit=limit,
            filters=filters,
        )

        # Merge contexts
        merged = self.context_merger.merge_contexts(hybrid_results)

        # Generate Citations
        citations = [
            Citation(
                source_id=item.document_id or item.chunk_id,
                filename=item.filename,
                file_path=item.file_path,
                chunk_id=item.chunk_id,
                relevance_score=item.score,
            )
            for item in hybrid_results
        ]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalPipelineOutput(
            query=query,
            strategy_used=strategy,
            merged_context=merged,
            citations=citations,
            latency_ms=round(elapsed_ms, 2),
        )
