# Verified Repository Capabilities & Executive Specification (v3)
==================================================================================

This report maps out the actual executable classes, routers, engines, and tests discovered inside the **OpenSEP** repository, detailing their inputs, outputs, models, and dependencies.

---

## 1. Complete Capability Inventory

### 1. LangGraph StateGraph Compilation Engine
* **Classification**: Engine
* **Purpose**: Orchestrates multi-node state graphs featuring validation loops, conditional edge routing, and checkpoint halts.
* **How it works**: Registers custom nodes, defines transitions, intercepts execution prior to the `validate` step to persist state snapshots to PostgreSQL, and resumes from payload values.
* **Inputs**: `AgentState`
* **Outputs**: `CompiledStateGraph`
* **AI Models**: None.
* **Memory Used**: PostgreSQL checkpointer database.
* **LangGraph Nodes Used**: `start`, `process`, `validate`, `end`.
* **Tools Used**: None.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/runtime/graph.py`](file:///c:/Users/sachi/ASEP/backend/src/runtime/graph.py)
* **Exact Class**: `StateGraphWrapper`
* **Exact Functions**: `assemble_default_flow`, `compile`
* **Related Database Models**: None.
* **Related API Endpoints**: None.
* **Related Frontend Pages**: None.
* **Related Tests**: [`backend/tests/unit/runtime/test_checkpoints.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/runtime/test_checkpoints.py)
* **Confidence**: 100%

### 2. Multi-Agent Concurrency DAG Engine
* **Classification**: Engine
* **Purpose**: Coordinates a decentralized DAG of specialized, registered worker agents, resolving dependencies and executing ready tasks concurrently.
* **How it works**: Parses subtask dependency lists, schedules parallel operations using `asyncio.gather`, merges parent response payloads into downstream inputs, and checks compliance before final output generation.
* **Inputs**: `execution_id`, `correlation_id`, `tasks` list.
* **Outputs**: Mapped dictionary of `AgentResponse` results.
* **AI Models**: None.
* **Memory Used**: Ephemeral local dictionaries.
* **LangGraph Nodes Used**: None.
* **Tools Used**: None.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/multi_agent/engine.py`](file:///c:/Users/sachi/ASEP/backend/src/multi_agent/engine.py)
* **Exact Class**: `ExecutionEngine`
* **Exact Functions**: `execute_dag`
* **Related Database Models**: None.
* **Related API Endpoints**: `/api/v1/conversations/run`
* **Related Frontend Pages**: `/sessions`
* **Related Tests**: [`backend/tests/unit/multi_agent/test_orchestration.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/multi_agent/test_orchestration.py)
* **Confidence**: 100%

### 3. PTY Terminal Stream & Multiplexer Router
* **Classification**: Service / Router
* **Purpose**: Spawns and interacts with interactive shell processes inside local PTY master-slave forks, streaming buffers over WebSockets.
* **How it works**: Handshakes user tokens, forks processes, runs select loops to capture stdout streams, publishes stdout events to Redis Pub/Sub channels to sync horizontal backend API gateway nodes, and intercepts command inputs using OPA validation check overrides.
* **Inputs**: WebSocket binary frames, JSON resize packets.
* **Outputs**: Raw terminal stdout bytes.
* **AI Models**: None.
* **Memory Used**: Ephemeral Redis caching channels.
* **LangGraph Nodes Used**: None.
* **Tools Used**: Local `os.write` writing to master file descriptor.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/api/routers/terminal.py`](file:///c:/Users/sachi/ASEP/backend/src/api/routers/terminal.py)
* **Exact Class**: `TerminalRouter`
* **Exact Functions**: `__init__`, `_validate_command_with_opa`
* **Related Database Models**: None.
* **Related API Endpoints**: `/api/v1/ws/sessions/{session_id}/terminal`
* **Related Frontend Pages**: `/sessions/[id]`
* **Related Tests**: None (Manual verification).
* **Confidence**: 100%

### 4. Human-in-the-Loop (HITL) Governance Engine
* **Classification**: Service
* **Purpose**: Pauses execution paths to await operator review, persisting session logs to PostgreSQL.
* **How it works**: Determines risk level classifications based on the target action. Creates a pending database log entry, halts execution, and updates session states on resolution.
* **Inputs**: Tool name, arguments, justification notes.
* **Outputs**: Mapped database `HITLSession` models.
* **AI Models**: None.
* **Memory Used**: PostgreSQL database.
* **LangGraph Nodes Used**: `validate` node interrupts.
* **Tools Used**: None.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/governance/hitl.py`](file:///c:/Users/sachi/ASEP/backend/src/governance/hitl.py)
* **Exact Class**: `HITLEngine`
* **Exact Functions**: `create_session`, `get_session`, `evaluate_risk`
* **Related Database Models**: `HITLSession` in [`backend/src/db/models/hitl_session.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/hitl_session.py)
* **Related API Endpoints**: `/api/v1/governance/hitl/queue`
* **Related Frontend Pages**: `/approvals`
* **Related Tests**: [`backend/tests/unit/governance/test_hitl.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/governance/test_hitl.py)
* **Confidence**: 100%

### 5. Multi-Provider LLM Runtime wrapper
* **Classification**: Service
* **Purpose**: Coordinates completions across multiple cloud and local model providers.
* **How it works**: Implements lazy SDK client initializations, parses chat lists, structures format parameters, and outputs completions or streams.
* **Inputs**: `CompletionRequest`
* **Outputs**: `CompletionResponse`
* **AI Models**:
  - `claude-3-5-sonnet-20241022` (Anthropic)
  - `gemini-2.5-flash` (Gemini)
  - `llama3.2` (Ollama)
  - `gpt-4o` (OpenAI)
* **Memory Used**: None.
* **LangGraph Nodes Used**: None.
* **Tools Used**: None.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/ai_runtime/providers/anthropic.py`](file:///c:/Users/sachi/ASEP/backend/src/ai_runtime/providers/anthropic.py) (`AnthropicProvider`)
* **Exact File Path**: [`backend/src/ai_runtime/providers/gemini.py`](file:///c:/Users/sachi/ASEP/backend/src/ai_runtime/providers/gemini.py) (`GeminiProvider`)
* **Exact File Path**: [`backend/src/ai_runtime/registry.py`](file:///c:/Users/sachi/ASEP/backend/src/ai_runtime/registry.py) (`ProviderRegistry`)
* **Related Database Models**: None.
* **Related API Endpoints**: None.
* **Related Frontend Pages**: None.
* **Related Tests**: [`backend/tests/unit/ai_runtime/test_service.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/ai_runtime/test_service.py)
* **Confidence**: 100%

### 6. Local GraphRAG Semantic Cache
* **Classification**: Pipeline / Cache
* **Purpose**: Hashes and caches solved error codes in Redis to prevent duplicate model calls.
* **How it works**: Formats tracebacks, hashes the cleaned string, queries Redis, and returns solution values.
* **Inputs**: Code traceback error.
* **Outputs**: Cached solution strings.
* **AI Models**: None.
* **Memory Used**: Redis.
* **LangGraph Nodes Used**: None.
* **Tools Used**: None.
* **Production Status**: **Production Ready**
* **Exact File Path**: [`backend/src/production/graphrag_engine.py`](file:///c:/Users/sachi/ASEP/backend/src/production/graphrag_engine.py)
* **Exact Class**: `LocalGraphRAGEngine`
* **Exact Functions**: `get_semantic_cache`, `store_semantic_cache`
* **Related Database Models**: None.
* **Related API Endpoints**: None.
* **Related Frontend Pages**: None.
* **Related Tests**: [`backend/tests/unit/production/test_phase3.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/production/test_phase3.py)
* **Confidence**: 100%

### 7. Knowledge Synchronization Engine
* **Classification**: Pipeline
* **Purpose**: Coordinates documentation crawler indexes, updates catalogs, and manages metadata change detection.
* **How it works**: Queries registries, tracks file modifications, processes batches, and saves sync metrics.
* **Inputs**: trusted source metadata, document lists.
* **Outputs**: Sync history log values.
* **AI Models**: None.
* **Memory Used**: Ephemeral local dict checkpoints.
* **LangGraph Nodes Used**: None.
* **Tools Used**: None.
* **Production Status**: **Partially Implemented**
* **Exact File Path**: [`backend/src/knowledge/sync.py`](file:///c:/Users/sachi/ASEP/backend/src/knowledge/sync.py)
* **Exact Class**: `KnowledgeSyncEngine`
* **Exact Functions**: `incremental_sync`, `full_sync`
* **Related Database Models**: `KnowledgeDocument` in [`backend/src/db/models/knowledge_document.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/knowledge_document.py)
* **Related API Endpoints**: `/api/v1/knowledge/sync`
* **Related Frontend Pages**: `/knowledge`
* **Related Tests**: [`backend/tests/unit/knowledge/test_knowledge_sync.py`](file:///c:/Users/sachi/ASEP/backend/tests/unit/knowledge/test_knowledge_sync.py)
* **Confidence**: 100%

---

## SECTION 2 — Strategic Questions

### 1. Does OpenSEP contain a Coding capability?
**Yes.** OpenSEP implements a base `CodingAgent` class (in [`backend/src/multi_agent/coding_agent.py`](file:///c:/Users/sachi/ASEP/backend/src/multi_agent/coding_agent.py)) that produces mock python patches for tests. Real-world edits are supported through filesystem action tools (defined in [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py)), which write raw data directly to disk.

### 2. Does OpenSEP contain a Research capability?
**Yes.** OpenSEP implements `ResearchAgent` (in [`backend/src/multi_agent/research_agent.py`](file:///c:/Users/sachi/ASEP/backend/src/multi_agent/research_agent.py)). Outbound HTTP tools (in [`backend/src/tools/impl.py`](file:///c:/Users/sachi/ASEP/backend/src/tools/impl.py)) facilitate web queries.

### 3. Does OpenSEP contain a GraphRAG capability?
**Yes.** OpenSEP includes `LocalGraphRAGEngine` (in [`backend/src/production/graphrag_engine.py`](file:///c:/Users/sachi/ASEP/backend/src/production/graphrag_engine.py)), which serves as a semantic error-solution cache utilizing local Redis databases.

### 4. Does OpenSEP contain a Knowledge Synchronization capability?
**Yes.** Implemented inside the sync package ([`backend/src/knowledge/sync.py`](file:///c:/Users/sachi/ASEP/backend/src/knowledge/sync.py)), which computes version checksum modifications, tracks incremental sync pipelines, and records history indexes.

### 5. Does OpenSEP contain Memory-Augmented Generation (MAG)?
**No. Evidence Not Found.** No code references exist for MAG.

### 6. Does OpenSEP support Screenshot Analysis?
**No. Evidence Not Found.**

### 7. Does OpenSEP support OCR?
**No. Evidence Not Found.**

### 8. Does OpenSEP support Vision Models?
**No. Evidence Not Found.**

### 9. Which capability is the platform's primary IP?
The low-level, WebSocket-driven pseudo-terminal that bypasses shell execution wrappers for secure command input, integrated with risk-based governance policies.

### 10. Which capabilities are enterprise differentiators?
* Append-only, database-enforced immutable audit logging.
* Scoped organizational multi-tenant workspaces.
* Pydantic-driven fail-fast production environment keys validators.
* Secure execution sandboxing inside isolated Docker containers.
