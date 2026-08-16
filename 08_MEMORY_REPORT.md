# 08 — Memory Architecture Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/memory/` and `backend/src/api/routers/memory.py`.

---

## 1. 3-Tier Memory Architecture

Implemented in `backend/src/memory/runtime.py` (`MemoryRuntime`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ASEP 3-TIER MEMORY ENGINE                       │
├───────────────────────┬────────────────────────┬───────────────────────┤
│ Tier 1: Working       │ Tier 2: Semantic       │ Tier 3: Procedural    │
│ Context Window        │ Vector Store           │ Graph AST             │
├───────────────────────┼────────────────────────┼───────────────────────┤
│ • In-memory sliding   │ • Dense embeddings in  │ • Node relationships  │
│   context window      │   Qdrant (Cosine sim)  │   in Neo4j Graph DB   │
│ • Session turn cache  │ • Cross-session recall │ • Historical code     │
│ • Context compression │ • Semantic similarity  │   evolution traces    │
└───────────────────────┴────────────────────────┴───────────────────────┘
```

---

## 2. Granular Tier Specifications

### 2.1 Working Memory (`backend/src/memory/working.py`)
- Tracks active session execution turns, intermediate tool arguments, and LLM reasoning steps.
- Implements automated context compaction when token budgets exceed threshold limits.

### 2.2 Semantic Memory (`backend/src/memory/semantic.py`)
- Stores consolidated episodic learnings and historical debug traces in Qdrant collection `asep_memory`.
- Enables agents to recall past solutions to recurring compiler/runtime errors across projects.

### 2.3 Procedural Memory (`backend/src/memory/procedural.py`)
- Represents execution rules, organizational coding standards, and architectural blueprints as Neo4j graph nodes.

---

## 3. Consolidation & Compaction Lifecycle

- **Consolidation Trigger**: `POST /api/v1/memory/consolidate`
- **Logic**: Extracts high-value facts and lessons learned from the completed session, vectors them, and writes them to Qdrant while updating Neo4j relationship weights.
