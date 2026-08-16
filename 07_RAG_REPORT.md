# 07 — Retrieval-Augmented Generation (RAG) Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/knowledge/`, `backend/src/vector/`, and `backend/src/production/graphrag_engine.py`.

---

## 1. Document Ingestion & Chunking Pipeline

Implemented in `backend/src/knowledge/sources.py` and `sync.py`.

1. **Document Validation**:
   - File types: Markdown (`.md`), TypeScript/JavaScript (`.ts`, `.tsx`, `.js`), Python (`.py`), Text (`.txt`).
   - Change Detection: Computes SHA-256 `content_hash` to prevent redundant embeddings.
2. **Semantic Chunking**:
   - Chunks text on heading, function, and class boundaries.
   - Preserves file paths, line ranges, and AST metadata tags.
3. **Dense Vector Embeddings**:
   - Generates embeddings via OpenAI `text-embedding-3-small` (1536 dim) or Gemini/Ollama embeddings (768 dim).

---

## 2. Vector Search (Qdrant)

Implemented in `backend/src/vector/collections.py` and `backend/src/api/routers/rag.py`.
- **Collection**: `asep_knowledge_base`
- **Distance Metric**: Cosine Similarity
- **Filtering**: Project ID, file extension, and tag filters
- **Query Endpoint**: `POST /api/v1/rag/query` with threshold &ge;0.75

---

## 3. GraphRAG Codebase Ingestion (Neo4j)

Implemented in `backend/src/production/graphrag_engine.py` and `backend/src/graph/neo4j.py`.
- Maps repository AST relationships:
  - Modules &rarr; Classes &rarr; Methods &rarr; Imports &rarr; Exports
- Enables cross-file dependency impact analysis before code modification.
