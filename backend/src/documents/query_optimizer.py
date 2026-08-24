"""
ASEP — Query Rewriter & Optimization Engine
============================================
Rewrites queries, performs sub-query expansion, integrates response caching,
and handles degraded retrieval fallback strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QueryExpansionResult:
    original_query: str
    expanded_queries: list[str]
    sub_queries: list[str]
    is_cached: bool = False
    cached_response: dict[str, Any] | None = None


class QueryOptimizer:
    """Optimizes input queries through expansion, rewriting, and cache checks."""

    def __init__(self, cache_client: Any | None = None) -> None:
        self.cache = cache_client

    async def optimize_query(self, query: str) -> QueryExpansionResult:
        original = query.strip()
        if not original:
            return QueryExpansionResult(original_query="", expanded_queries=[], sub_queries=[])

        # 1. Check Redis / Memory cache if available
        if self.cache:
            try:
                cached = await self.cache.get(f"rag_query:{original}")
                if cached:
                    logger.info("RAG query cache hit for '%s'", original)
                    return QueryExpansionResult(
                        original_query=original,
                        expanded_queries=[original],
                        sub_queries=[],
                        is_cached=True,
                        cached_response={"result": cached},
                    )
            except Exception as exc:
                logger.warning("Cache retrieval error: %s", exc)

        # 2. Heuristic Query Expansion
        expanded = [original]
        if " architecture" not in original.lower():
            expanded.append(f"{original} architecture overview")
        if " system" not in original.lower():
            expanded.append(f"{original} implementation details")

        # 3. Sub-query Decomposition
        sub_queries: list[str] = []
        if " and " in original.lower():
            sub_queries = [s.strip() for s in original.split(" and ") if len(s.strip()) > 3]

        return QueryExpansionResult(
            original_query=original,
            expanded_queries=expanded,
            sub_queries=sub_queries,
            is_cached=False,
        )
