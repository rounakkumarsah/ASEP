from __future__ import annotations
from typing import List, Dict, Any, Tuple
from src.ai_runtime.context import ConversationContextManager

class ContextBuilder:
    """Production ContextBuilder deduplicating, ordering, and formatting retrieved RAG context."""

    def __init__(self, token_budget: int = 2048) -> None:
        self.token_budget = token_budget
        self.context_manager = ConversationContextManager(token_budget=token_budget)

    def deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_ids = set()
        deduped = []
        for chunk in chunks:
            cid = chunk.get("chunk_id")
            if cid not in seen_ids:
                seen_ids.add(cid)
                deduped.append(chunk)
        return deduped

    def order_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order sources by score descending (primary) or filename (secondary)."""
        return sorted(chunks, key=lambda x: x.get("score", 0.0), reverse=True)

    def build_context_and_citations(
        self,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Processes chunks and returns:
        - formatted context string
        - selected chunks list fitting budget
        - citations index mapping
        """
        deduped = self.deduplicate_chunks(chunks)
        ordered = self.order_chunks(deduped)
        
        selected_chunks = []
        accumulated_tokens = 0
        
        for chunk in ordered:
            text = chunk.get("text", "")
            est_tokens = self.context_manager.estimate_tokens(text)
            
            if accumulated_tokens + est_tokens > self.token_budget:
                break
                
            selected_chunks.append(chunk)
            accumulated_tokens += est_tokens
            
        # Build context blocks and inline citations list
        context_blocks = []
        citations_blocks = []
        
        for idx, chunk in enumerate(selected_chunks, 1):
            filename = chunk.get("filename", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)
            
            context_blocks.append(f"--- Context Segment [{idx}] (Source: {filename}, Score: {score:.2f}) ---\n{text}\n")
            citations_blocks.append(f"[{idx}] {filename} (ID: {chunk.get('document_id', 'unknown')})")
            
        formatted_context = "\n".join(context_blocks)
        citations_str = "\n".join(citations_blocks)
        
        return formatted_context, selected_chunks, citations_str

    def compress_context_hook(self, text: str) -> str:
        """Hook for semantic text compression (Scaffold Only)."""
        return text
