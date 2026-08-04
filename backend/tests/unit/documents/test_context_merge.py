"""
ASEP — Unit Tests for Context Merge Engine
"""

import pytest
from src.documents.context_merge import ContextMergeEngine
from src.documents.hybrid_retrieval import HybridSearchResult


def test_context_merge_deduplication_and_packing():
    merger = ContextMergeEngine(token_budget=100)

    item1 = HybridSearchResult(chunk_id="c1", score=0.9, text="Duplicate text statement.", document_id="d1")
    item2 = HybridSearchResult(chunk_id="c2", score=0.8, text="Duplicate text statement.", document_id="d1")
    item3 = HybridSearchResult(chunk_id="c3", score=0.7, text="Unique third sentence.", document_id="d2")

    merged = merger.merge_contexts([item1, item2, item3])

    assert merged.deduplicated_count == 1
    assert len(merged.chunks) == 2
    assert "Duplicate text statement." in merged.formatted_context
    assert "Unique third sentence." in merged.formatted_context
