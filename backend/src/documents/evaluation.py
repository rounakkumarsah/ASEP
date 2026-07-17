from __future__ import annotations
from typing import List, Any

class RAGEvaluator:
    """Scaffold evaluation module for assessing search quality metrics (Recall, Precision, MRR, NDCG)."""

    def compute_recall_at_k(self, retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
        """Recall@K = (Retrieved Ground Truth Chunks in Top-K) / (Total Ground Truth Chunks)"""
        if not ground_truth_ids:
            return 0.0
        retrieved_k = set(retrieved_ids[:k])
        hits = len(retrieved_k.intersection(ground_truth_ids))
        return hits / len(ground_truth_ids)

    def compute_precision_at_k(self, retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
        """Precision@K = (Retrieved Ground Truth Chunks in Top-K) / K"""
        if k <= 0:
            return 0.0
        retrieved_k = set(retrieved_ids[:k])
        hits = len(retrieved_k.intersection(ground_truth_ids))
        return hits / k

    def compute_mrr(self, retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
        """Mean Reciprocal Rank (MRR) of first relevant match."""
        ground_set = set(ground_truth_ids)
        for idx, item in enumerate(retrieved_ids, 1):
            if item in ground_set:
                return 1.0 / idx
        return 0.0

    def compute_ndcg(self, retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
        """Normalized Discounted Cumulative Gain (NDCG) for binary relevance."""
        import math
        dcg = 0.0
        ground_set = set(ground_truth_ids)
        for idx, item in enumerate(retrieved_ids, 1):
            if item in ground_set:
                dcg += 1.0 / math.log2(idx + 1)
                
        # Compute Ideal DCG (all ground truth items retrieved first)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(ground_truth_ids), len(retrieved_ids)) + 1))
        
        if idcg == 0.0:
            return 0.0
        return dcg / idcg
