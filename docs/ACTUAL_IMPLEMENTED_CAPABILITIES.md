# Actual Implemented Capabilities — OpenSEP

This document catalogs every capability implemented in the **OpenSEP** repository, detailing their entry points, execution flows, and supporting database or test elements.

---

## 1. Executive Summary
OpenSEP is a sovereign, self-hosted developer platform coordinating sandboxed tasks. The backend utilizes FastAPI routers and LangGraph state-snapshot checkpointers. The frontend dashboard leverages xterm.js WebGL rendering and Monaco Editor side-by-side diff comparison models.

---

## 2. AI Agents

### Supervisor & Worker Agents
* **Purpose**: Coordinates multi-agent workflows by routing execution steps to planner or executor agents based on plan statuses.
* **Status**: **Prototype**
* **Entry Point**: [`backend/src/agents/supervisor.py`](file:///c:/Users/sachi/ASEP/backend/src/agents/supervisor.py) (`supervisor_node`)
* **Workflow**: The supervisor advances execution step-counters or flags runs as complete. (Planned - LLM-based dynamically-routed graph flows).
* **Tools**: None linked in prototype.
* **Models**: None.
* **Memory**: Receives state maps through Pydantic schemas.
* **Evidence**: [`backend/src/agents/supervisor.py`](file:///c:/Users/sachi/ASEP/backend/src/agents/supervisor.py) (`supervisor_node`)

---

## 3. LangGraph Architecture

* **Graphs Implemented**: A default lifecycle processing loop is configured in the codebase.
  - *START &rarr; start_node &rarr; process_node &rarr; human_validation_node &rarr; (conditional) &rarr; end_node &rarr; END*
* **Executed Graphs**: Yes, fully executed in tests.
* **Nodes**:
  - `start`: [`backend/src/runtime/nodes.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/nodes.py) (`start_node_default`)
  - `process`: [`backend/src/runtime/nodes.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/nodes.py) (`process_node_default`)
  - `validate`: [`backend/src/runtime/nodes.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/nodes.py) (`human_validation_node_default`)
* **Edges**: 
  - `human_validation_router`: [`backend/src/runtime/edges.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/edges.py) (`human_validation_router_default`)
* **Interrupts**: Configured to halt execution *before* the `validate` node to await operator approval payload resumes.
* **Checkpointers**: `AsyncPostgresSaver` handles state serialization.
* **Evidence**: [`backend/src/runtime/graph.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/graph.py) (`StateGraphWrapper`), [`backend/tests/unit/runtime/test_checkpoints.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/runtime/test_checkpoints.py)

---

## 4. Memory Architecture

* **Working Memory**: Evaluated on Redis caching connections (`init_redis` in `backend/src/cache/redis.py`).
* **Episodic Memory**: Document and execution logs stored in PostgreSQL (`agent_runs` table).
* **Semantic & Vector Memory**: Knowledge base schemas mapping embeddings to Qdrant vector spaces and code structures in Neo4j.
  - *Evidence*: [`backend/src/vector/qdrant.py`](file:///c:/Users/sachi/ASEP/backend/src/vector/qdrant.py) (`QdrantVectorService`)
* **Checkpointer**: Durably persists LangGraph thread snapshots in PostgreSQL.
  - *Evidence*: [`backend/src/runtime/checkpoints.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/checkpoints.py) (`AsyncPostgresSaver`)

---

## 5. Research System
* **Code Search**: File search capabilities mapping patterns to repository workspaces.
* **Hybrid Search**: **Planned - Not Implemented**
* **Evidence**: [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py) (`FilesystemTool` handles lists/reads).

---

## 6. Retrieval-Augmented Generation (RAG)
* **Local GraphRAG & Semantic Cache**: Local semantic cache utilizing Redis to store solved code issues, bypassing redundant model calls.
  - *Evidence*: [`backend/src/production/graphrag_engine.py`](file:///c:/Users/sachi/ASEP/backend/src/production/graphrag_engine.py) (`LocalGraphRAGEngine`)
* **Ingestion Pipelines**: Change-detection crawler, chunking, and embedding synchronization catalog.
  - *Evidence*: [`backend/src/knowledge/sync.py`](file:///c:/Users/sachi/ASEP/backend/src/knowledge/sync.py) (`KnowledgeSyncEngine`)

---

## 7. Memory-Augmented Generation (MAG)
* **Status**: **Evidence Not Found**

---

## 8. Vision (UI screenshot analysis / image processing)
* **Status**: **Evidence Not Found**

---

## 9. OCR (Image / PDF text detection)
* **Status**: **Evidence Not Found**

---

## 10. Document Ingestion Pipeline
* **Status**: **Partially Implemented**
* **Capabilities**: Document sync registry engine supporting web, pdf, github, markdown, api, video, and local documents. Tracks crawl status, sync counts, checksum variations, and metadata indexes.
* **Evidence**: [`backend/src/db/models/knowledge_document.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/knowledge_document.py) (`DocumentSourceType`), [`backend/src/knowledge/sync.py`](file:///c:/Users/sachi/ASEP/backend/src/knowledge/sync.py) (`SyncedDocument`)

---

## 11. Coding Assistant

* **Code Workspace Manipulation**: Reads and writes files directly to target locations.
  - *Evidence*: [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py) (`FilesystemTool`)
* **Dependency & Testing execution**: Launches commands inside Python base environments or mounts workspaces inside isolated Docker containers.
  - *Evidence*: [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py) (`TerminalTool` executing docker runs)

---

## 12. Tool Calling

* **Integrated Tools**:
  - `filesystem`: Action read, write, and list.
  - `terminal`: Docker sandbox command execution wrapper.
  - `git`: Executing status, commit, log, and diff.
  - `github`: Mock repo issues/PR query wrapper.
  - `docker`: Interfacing with engine statistics.
  - `http`: Fetching URL methods.
  - `postgres`: Interfacing with postgres queries.
  - `neo4j`: Query Cypher parameters.
  - `qdrant`: Retrieve semantic embeddings status.
  - `redis`: Ping and fetch keys.
  - `environment`: Safely read configurations (with redactions).
  - `browser`: Headless simulation runner.
* **Permissions & Governance**: Checked against RBAC credentials (`ToolPermission.SECRETS`, `ToolPermission.EXECUTE`). Pauses graph execution for manual approval if tool actions are flagged as critical.
  - *Evidence*: [`backend/src/governance/hitl.py`](file:///c:/Users/sachi/ASEP/backend/src/governance/hitl.py) (`RiskLevel`, `HITLEngine`), [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py)

---

## 13. Infrastructure

* **Redis Pub/Sub Sync**: Ephemeral stdout streams publish to Redis channels.
  - *Evidence*: [`backend/src/api/routers/terminal.py`](file:///c:/Users/sachi/ASEP/backend/src/api/routers/terminal.py) (`TerminalRouter`)
* **Docker Compose Networks**: Complete isolation of Neo4j, Postgres, and Redis inside `asep-network`.
  - *Evidence*: [`docker-compose.yml`](file:///c:/Users/sachi/ASEP/docker-compose.yml)

---

## 14. Security

* **PTY Low-Level Direct Write**: Keystrokes write directly to PTY file descriptors via `os.write`, preventing terminal string interpreter bypass.
  - *Evidence*: [`backend/src/api/routers/terminal.py`](file:///c:/Users/sachi/ASEP/backend/src/api/routers/terminal.py)
* **Fail-Fast Environment Validator**: Root validation logic blocks backend startup if APP_ENV is production and local fallback defaults are used.
  - *Evidence*: [`backend/src/config/settings.py`](file:///c:/Users/sachi/ASEP/backend/src/config/settings.py) (`validate_production_environment_variables`)

---

## 15. Enterprise Features

* **Multi-Tenant Organizations**: FK organizational boundary scopes.
  - *Evidence*: [`backend/src/db/models/organization.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/organization.py) (`Organization`)
* **Scoped API Keys**: Key validation via SHA-256 HMAC comparisons.
  - *Evidence*: [`backend/src/db/models/api_key.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/api_key.py) (`ApiKey`)
* **Audit Logging Engine**: Standardized logging of actors, severity levels, target resource IDs, and results.
  - *Evidence*: [`backend/src/db/models/audit_log.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/audit_log.py) (`AuditLog`)

---

## 16. Capabilities that are COMPLETE
* Web PTY Terminal Streaming WebSocket routing.
* Monaco split-screen git diff comparison viewers.
* LangGraph state-snapshot serialization (`AsyncPostgresSaver`).
* Additive database migrations.
* Production environment settings validation.

---

## 17. Capabilities that are PARTIAL
* Ingest Sync Engine change detection.
* Structured logging and middleware request tracing.

---

## 18. Capabilities that are PLANNED
* Advanced SSO (OIDC/SAML) integrations. (*Status: Planned - Not Implemented*)
* Slack/Discord approval alert hook pipelines. (*Status: Planned - Not Implemented*)

---

## 19. Dead Code / Unused Modules
* **agents/supervisor.py**: Prototype placeholder supervisor node that is bypassed in the active production graph.

---

## 20. Missing Production Features
* Fully managed Kubernetes Helm orchestration charts.

---

## 21. Top 20 Strongest Technical Assets
1. `backend/src/api/routers/terminal.py` (Low-level PTY execution & validation loop)
2. `backend/src/runtime/checkpoints.py` (Postgres checkpoint saver integration)
3. `backend/src/config/settings.py` (Fail-fast environment configurations)
4. `frontend/src/components/TerminalEmulator.tsx` (xterm WebGL emulator component)
5. `frontend/src/components/MonacoDiffViewer.tsx` (Side-by-side git diff Monaco viewer)
6. `backend/src/governance/hitl.py` (SLA and Risk classification manager)
7. `backend/src/db/models/audit_log.py` (Append-only immutable audit trail definitions)
8. `backend/src/api/middleware/logging.py` (Request tracking log interceptor middleware)
9. `backend/src/db/models/api_key.py` (SHA-256 HMAC API key verification)
10. `backend/src/production/graphrag_engine.py` (Redis semantic error solution cache engine)

---

## 22. Repository Statistics
* **Unit Tests**: 140 passing test cases.
* **Static Views**: 38 Next.js app router routing pages.
* **Supported AI Engines**: 4 (Gemini, Claude, Ollama, OpenAI).
