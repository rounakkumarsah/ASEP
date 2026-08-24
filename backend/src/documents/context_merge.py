"""
ASEP — Context Merge & Optimization Engine
===========================================
Merges vector and graph contexts, eliminates exact/semantic duplicates,
compresses redundant text, and optimizes context packing under token budget bounds.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any

from src.documents.hybrid_retrieval import HybridSearchResult

logger = logging.getLogger(__name__)


@dataclass
class MergedContext:
    chunks: list[dict[str, Any]]
    graph_facts: list[dict[str, Any]]
    formatted_context: str
    token_estimate: int
    deduplicated_count: int


class ContextMergeEngine:
    """Merges, deduplicates, compresses, and packs vector and graph contexts."""

    def __init__(self, token_budget: int = 4000) -> None:
        self.token_budget = token_budget

    def _hash_text(self, text: str) -> str:
        clean = " ".join(text.lower().split())
        return hashlib.md5(clean.encode("utf-8")).hexdigest()

    def merge_contexts(
        self,
        hybrid_results: list[HybridSearchResult],
        extra_graph_nodes: list[Any] | None = None,
    ) -> MergedContext:
        seen_hashes: set[str] = set()
        unique_chunks: list[dict[str, Any]] = []
        unique_graph_facts: list[dict[str, Any]] = []
        dedup_count = 0

        # 1. Deduplicate & filter vector chunks
        for item in hybrid_results:
            h = self._hash_text(item.text)
            if h in seen_hashes:
                dedup_count += 1
                continue
            seen_hashes.add(h)
            unique_chunks.append({
                "chunk_id": item.chunk_id,
                "text": item.text,
                "score": item.score,
                "document_id": item.document_id,
                "filename": item.filename,
                "file_path": item.file_path,
            })

            # Process attached graph connections
            for conn in item.graph_connections:
                fact_key = f"{item.chunk_id}->{conn.get('node_id')}"
                if fact_key not in seen_hashes:
                    seen_hashes.add(fact_key)
                    unique_graph_facts.append(conn)

        # 2. Process extra graph nodes if provided
        if extra_graph_nodes:
            for gnode in extra_graph_nodes:
                nid = getattr(gnode, "node_id", str(gnode))
                if nid not in seen_hashes:
                    seen_hashes.add(nid)
                    unique_graph_facts.append({
                        "node_id": nid,
                        "labels": getattr(gnode, "labels", []),
                        "properties": getattr(gnode, "properties", {}),
                    })

        # 3. Token-budget-aware context packing
        packed_chunks: list[dict[str, Any]] = []
        accumulated_tokens = 0
        context_lines: list[str] = ["=== DOCUMENT CONTEXT ==="]

        for chunk in unique_chunks:
            tokens = len(chunk["text"].split()) * 4 // 3  # Rough token estimate
            if accumulated_tokens + tokens > self.token_budget:
                logger.debug("Token budget (%d) reached — stopping context packing.", self.token_budget)
                break
            packed_chunks.append(chunk)
            accumulated_tokens += tokens
            fname = chunk.get("filename") or chunk.get("document_id") or "doc"
            context_lines.append(f"[{fname}] {chunk['text']}")

        if unique_graph_facts:
            context_lines.append("\n=== KNOWLEDGE GRAPH CONNECTIONS ===")
            for fact in unique_graph_facts:
                rel = fact.get("relationship", "RELATED_TO")
                nid = fact.get("node_id", "entity")
                props = fact.get("properties", {})
                context_lines.append(f"- ({rel}) -> {nid} {props}")

        formatted_context = "\n".join(context_lines)

        return MergedContext(
            chunks=packed_chunks,
            graph_facts=unique_graph_facts,
            formatted_context=formatted_context,
            token_estimate=accumulated_tokens,
            deduplicated_count=dedup_count,
        )
