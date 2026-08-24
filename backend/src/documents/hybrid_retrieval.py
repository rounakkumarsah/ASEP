"""
ASEP — Hybrid Retrieval Pipeline & Ranking Engine
=================================================
Combines dense vector retrieval (Qdrant), graph traversal (Neo4j),
and BM25 lexical keyword matching with Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.documents.embedding_service import EmbeddingProvider
from src.graph.expansion import ExpandedGraphNode, GraphExpansionEngine
from src.graph.graph_service import GraphService
from src.vector import VectorSearchResult, VectorService

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    chunk_id: str
    score: float
    text: str
    document_id: str
    parent_id: str | None = None
    filename: str | None = None
    file_path: str | None = None
    source_type: str = "hybrid"
    vector_score: float = 0.0
    graph_score: float = 0.0
    bm25_score: float = 0.0
    graph_connections: list[dict[str, Any]] = field(default_factory=list)


class ReciprocalRankFusion:
    """Combines ranked lists from multiple search modalities using RRF."""

    @staticmethod
    def fuse(
        rank_lists: list[list[dict[str, Any]]],
        k: int = 60,
    ) -> list[dict[str, Any]]:
        scores: dict[str, float] = {}
        item_map: dict[str, dict[str, Any]] = {}

        for rank_list in rank_lists:
            for rank, item in enumerate(rank_list, start=1):
                item_id = item.get("chunk_id") or item.get("id")
                if not item_id:
                    continue

                if item_id not in item_map:
                    item_map[item_id] = dict(item)

                scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k + rank))

        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results: list[dict[str, Any]] = []
        for item_id, score in sorted_items:
            res = dict(item_map[item_id])
            res["rrf_score"] = round(score, 6)
            results.append(res)

        return results


class LexicalBM25Retriever:
    """Token matching lexical search engine for keyword queries."""

    def search_bm25(self, query: str, documents: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        query_tokens = set(query.lower().split())
        scored: list[dict[str, Any]] = []

        for doc in documents:
            text = (doc.get("text") or "").lower()
            text_tokens = text.split()
            if not text_tokens:
                continue

            score = 0.0
            for token in query_tokens:
                count = text_tokens.count(token)
                if count > 0:
                    tf = count / len(text_tokens)
                    score += (tf * (1.5 + 1)) / (tf + 1.5)

            if score > 0.0:
                d = dict(doc)
                d["bm25_score"] = round(score, 4)
                scored.append(d)

        scored.sort(key=lambda x: x.get("bm25_score", 0.0), reverse=True)
        return scored[:limit]


class HybridRetrievalPipeline:
    """Production hybrid retriever combining Qdrant, Neo4j, BM25, and metadata filters."""

    def __init__(
        self,
        vector_service: VectorService,
        embedding_provider: EmbeddingProvider,
        graph_service: GraphService | None = None,
        collection_name: str = "asep_documents",
    ) -> None:
        self.vector = vector_service
        self.embedder = embedding_provider
        self.graph = graph_service
        self.collection_name = collection_name
        self.graph_expansion = GraphExpansionEngine(graph_service) if graph_service else None
        self.bm25 = LexicalBM25Retriever()

    async def search_hybrid(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.0,
    ) -> list[HybridSearchResult]:
        # 1. Vector Search
        query_vector = await self.embedder.embed_query(query)
        vector_hits: list[VectorSearchResult] = await self.vector.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            payload_filters=filters,
            score_threshold=score_threshold,
        )

        vector_results = [
            {
                "chunk_id": hit.id,
                "vector_score": hit.score,
                "text": hit.payload.get("text", ""),
                "document_id": hit.payload.get("document_id", ""),
                "parent_id": hit.payload.get("parent_id"),
                "filename": hit.payload.get("filename"),
                "file_path": hit.payload.get("file_path"),
            }
            for hit in vector_hits
        ]

        # 2. BM25 Lexical Search over retrieved set
        bm25_results = self.bm25.search_bm25(query, vector_results, limit=limit)

        # 3. Multi-hop Graph Search
        graph_connections: list[ExpandedGraphNode] = []
        if self.graph_expansion and vector_results:
            seed_ids = [r["chunk_id"] for r in vector_results]
            graph_connections = await self.graph_expansion.expand_multi_hop(seed_ids, depth=2)

        # 4. RRF Rank Fusion
        fused = ReciprocalRankFusion.fuse([vector_results, bm25_results], k=60)

        # 5. Format HybridSearchResult list
        conn_map: dict[str, list[dict[str, Any]]] = {}
        for conn in graph_connections:
            if conn.parent_id:
                conn_map.setdefault(conn.parent_id, []).append({
                    "node_id": conn.node_id,
                    "relationship": conn.relationship,
                    "labels": conn.labels,
                    "properties": conn.properties,
                })

        final_results: list[HybridSearchResult] = []
        for item in fused[:limit]:
            chunk_id = item["chunk_id"]
            final_results.append(
                HybridSearchResult(
                    chunk_id=chunk_id,
                    score=item.get("rrf_score", 0.0),
                    text=item.get("text", ""),
                    document_id=item.get("document_id", ""),
                    parent_id=item.get("parent_id"),
                    filename=item.get("filename"),
                    file_path=item.get("file_path"),
                    vector_score=item.get("vector_score", 0.0),
                    bm25_score=item.get("bm25_score", 0.0),
                    graph_connections=conn_map.get(chunk_id, []),
                )
            )

        return final_results
