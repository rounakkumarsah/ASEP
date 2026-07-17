from __future__ import annotations
from typing import Dict, Any, Optional
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent
from src.documents.embedding_service import RuntimeEmbeddingProvider
from src.documents.retrieval import Retriever
from src.documents.context_builder import ContextBuilder
from src.vector.qdrant import get_qdrant_client
from src.vector import VectorService

class KnowledgeAgent(BaseAgent):
    """Knowledge Agent pulling context segments and citations from the Production RAG Engine."""

    def __init__(self, retriever: Optional[Retriever] = None) -> None:
        manifest = AgentManifest(
            name="KnowledgeAgent",
            version="1.0.0",
            description="Queries the Production RAG Engine for semantically relevant chunks and citations.",
            capabilities=["knowledge_retrieval", "citations_generation"],
            supported_inputs=["query"],
            supported_outputs=["context", "citations", "segments"]
        )
        super().__init__(role=AgentRole.KNOWLEDGE, manifest=manifest)
        self._retriever = retriever
        self.builder = ContextBuilder()

    @property
    def retriever(self) -> Retriever:
        if self._retriever is None:
            qdrant = get_qdrant_client()
            vector_service = VectorService(client=qdrant)
            embedder = RuntimeEmbeddingProvider()
            self._retriever = Retriever(vector_service=vector_service, embedding_provider=embedder)
        return self._retriever

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        query = request.input_data.get("query", "")
        
        # Retrieve documents
        hits = await self.retriever.retrieve(query=query, limit=5)
        context_str, selected, citations_str = self.builder.build_context_and_citations(hits)
        
        return {
            "context": context_str,
            "citations": citations_str,
            "segments": [
                {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "score": chunk.get("score", 0.0),
                    "filename": chunk.get("filename", ""),
                    "text": chunk.get("text", "")
                }
                for chunk in selected
            ]
        }
