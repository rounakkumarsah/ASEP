"""
ASEP — Neural Cross-Encoder Reranker for RAG
============================================
Reranks hybrid search candidate chunks using a local cross-encoder model
to maximize retrieval precision.
"""

from __future__ import annotations

from typing import Any
import structlog

logger = structlog.get_logger(__name__)

_RERANKER_INSTANCE: Reranker | None = None


class Reranker:
    """Neural cross-encoder reranker using sentence-transformers CrossEncoder."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model_name
        self._model: Any = None
        self._load_attempted: bool = False

    def _get_model(self) -> Any:
        if not self._load_attempted:
            self._load_attempted = True
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.model_name)
                logger.info("reranker_loaded", model_name=self.model_name)
            except Exception as exc:
                logger.warning("reranker_unavailable", error=str(exc), model_name=self.model_name)
                self._model = None
        return self._model

    def is_available(self) -> bool:
        """Check if the cross-encoder model can be loaded successfully."""
        return self._get_model() is not None

    def rerank(self, query: str, documents: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Rerank a list of document dicts against a query string.

        Each document dict must have a 'content' field.
        Returns top_k documents sorted by score descending with doc['rerank_score'].
        Degrades gracefully returning original documents if model is unavailable.
        """
        if not documents:
            return []

        model = self._get_model()
        if model is None:
            logger.warning("reranker_unavailable", reason="fallback_to_unranked")
            return documents[:top_k]

        try:
            pairs = [(query, str(doc.get("content") or "")) for doc in documents]
            scores = model.predict(pairs)

            if not hasattr(scores, "__iter__") or (hasattr(scores, "ndim") and scores.ndim == 0):
                scores = [scores]

            scored_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = float(score)
                scored_docs.append(doc_copy)

            scored_docs.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            result = scored_docs[:top_k]

            top_score = result[0]["rerank_score"] if result else 0.0
            logger.info("reranked", input_count=len(documents), output_count=len(result), top_score=top_score)
            return result
        except Exception as exc:
            logger.warning("rerank_error", error=str(exc))
            return documents[:top_k]


def get_reranker(model_name: str = "BAAI/bge-reranker-base") -> Reranker:
    """Return a singleton instance of the Reranker."""
    global _RERANKER_INSTANCE
    if _RERANKER_INSTANCE is None:
        _RERANKER_INSTANCE = Reranker(model_name=model_name)
    return _RERANKER_INSTANCE
