"""
ASEP — Semantic Memory (Qdrant + Neo4j Backends)
"""

import uuid
from typing import Any

from src.documents.embedding_service import EmbeddingProvider
from src.graph.graph_service import GraphService
from src.vector import VectorRecord, VectorService
from src.vector.collections import DEFAULT_COLLECTION


class SemanticMemory:
    """Manages general facts, relations, and concept associations."""

    def __init__(
        self,
        vector_service: VectorService,
        graph_service: GraphService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.vector = vector_service
        self.graph = graph_service
        self.embedder = embedding_provider

    async def add_fact(
        self,
        fact_id: str,
        text: str,
        collection_name: str = DEFAULT_COLLECTION,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Symmetrically register a fact in both Qdrant and Neo4j."""
        # 1. Generate embedding
        vector = await self.embedder.embed_query(text)
        
        # 2. Qdrant Upsert
        record = VectorRecord(
            id=fact_id,
            vector=vector,
            payload={"text": text, "type": "semantic_memory", **(metadata or {})}
        )
        await self.vector.upsert(collection_name, record)
        
        # 3. Neo4j write: MERGE a Fact node
        query = """
        MERGE (f:Fact {id: $id})
        SET f.text = $text, f.type = "semantic_memory"
        RETURN f
        """
        await self.graph.execute_write(query, {"id": fact_id, "text": text})

    async def query_facts(
        self,
        query_text: str,
        limit: int = 5,
        collection_name: str = DEFAULT_COLLECTION,
        payload_filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Perform semantic search against Qdrant to find similar factual concepts."""
        query_vector = await self.embedder.embed_query(query_text)
        
        results = await self.vector.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            payload_filters=payload_filters
        )
        
        return [
            {"id": hit.id, "score": hit.score, "text": hit.payload.get("text", ""), "payload": hit.payload}
            for hit in results
        ]
