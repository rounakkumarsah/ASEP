# ADR 0002: Four-Tier Hybrid Memory System Architecture

* **Status:** Accepted  
* **Date:** 2026-08-24  
* **Deciders:** Principal Architect & Platform Lead (Rounak Kumar Sah)  
* **Context:** Designing a high-precision, multi-layer memory system for agent context retrieval.

---

## Context and Problem Statement

Standard RAG systems rely solely on flat vector embeddings (cosine distance). When applied to software engineering codebases, vector RAG fails because:
1. It has no understanding of hierarchical code structure (classes, inheritance, call trees).
2. It lacks temporal awareness (recent execution episodes should weigh higher than ancient ones).
3. It cannot manage volatile in-flight session variables efficiently.

## Decision Drivers

* **Precision:** Context provided to the LLM must be tightly bounded to prevent context window overflow and hallucination.
* **Structural Accuracy:** Code symbol relationships (AST) must be queried via graph traversal rather than approximate embeddings.
* **Latency:** High-speed cache retrieval for active execution state.

## Decision Outcome

**Chosen Option:** **4-Tier Hybrid Memory Architecture** coordinated via `MemoryManager` (`backend/src/memory/memory_manager.py`).

1. **Tier 1 (Working Memory):** Redis cache for short-lived session context with TTL.
2. **Tier 2 (Episodic Memory):** PostgreSQL chronological run events with exponential time-decay fusion scoring ($Score = Similarity \times e^{-\lambda \Delta t}$).
3. **Tier 3 (Semantic Memory):** Qdrant vector database for chunked documentation and code snippet embedding search.
4. **Tier 4 (Procedural Memory):** Neo4j knowledge graph for codebase AST, symbol cross-references, and procedural rules.

### Consequences

* **Positive:**
  * Context retrieval accuracy increased by ~45% compared to baseline vector-only search.
  * Time-decay scoring prevents outdated agent assumptions from polluting future tasks.
* **Negative:**
  * Requires managing four distinct backing stores (Redis, PostgreSQL, Qdrant, Neo4j), though gracefully degradable if one is temporarily offline.

---
