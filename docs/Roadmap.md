# ASEP — Roadmap

> **Current Phase**: 0.1 — Production Scaffold ✅

---

## Phase 0.1 — Production Scaffold ✅

**Goal**: Empty but deployable repository with enterprise-grade structure.

- [x] FastAPI application factory
- [x] Pydantic v2 settings + env loading
- [x] Structured logging (structlog)
- [x] Health + readiness endpoints
- [x] PostgreSQL / Redis / Neo4j / Qdrant connection managers
- [x] LangGraph placeholders (state, planner, supervisor, registry, checkpoint)
- [x] Execution engine placeholder
- [x] Memory / Knowledge / Governance service stubs
- [x] Multi-stage Docker image (backend)
- [x] Docker Compose (6 services + healthchecks + volumes + network)
- [x] pyproject.toml with Black + Ruff + MyPy + Pytest
- [x] pre-commit configuration
- [x] GitHub Actions CI (lint + test + docker build)
- [x] Makefile developer shortcuts
- [x] Documentation (README + Architecture + FolderStructure + Roadmap + Development)
- [x] Passing test suite (health endpoint)

---

## Phase 0.2 — Core Infrastructure

**Goal**: All services connected. First agent run completes end-to-end.

- [ ] Alembic migration setup + first migration
- [ ] PostgreSQL models: AgentRun, Task, AuditLog, MemoryEntry
- [ ] All database health-check pings (readiness endpoint goes green)
- [ ] LangGraph: compile full supervisor graph with planner + executor
- [ ] LangGraph: PostgreSQL checkpointer integration
- [ ] ExecutionEngine: async task queue (Redis Streams)
- [ ] MemoryService: Qdrant integration (store + retrieve)
- [ ] GovernanceService: audit log writes to PostgreSQL
- [ ] First end-to-end agent run: accept goal → plan → execute → return result
- [ ] Streaming API endpoint (SSE) for agent run output
- [ ] Frontend: dashboard scaffold with run submission form
- [ ] OpenTelemetry tracing (traces → Jaeger)
- [ ] Prometheus metrics endpoint

---

## Phase 0.3 — Agent Capabilities

**Goal**: Agents can write, test, and review code autonomously.

- [ ] FileSystemTool (read / write / list)
- [ ] ShellExecutorTool (sandboxed subprocess)
- [ ] GitTool (clone, commit, diff, PR creation)
- [ ] CodeAnalysisTool (AST parsing, linting, type checking)
- [ ] WebSearchTool (DuckDuckGo / Brave)
- [ ] CodeWriterAgent
- [ ] CodeReviewerAgent
- [ ] TestRunnerAgent
- [ ] KnowledgeService: AST → Neo4j code graph ingestion
- [ ] KnowledgeService: code → Qdrant embedding pipeline

---

## Phase 0.4 — Memory & Knowledge

**Goal**: Agents have long-term memory and understand entire codebases.

- [ ] Episodic memory: past runs → Qdrant embeddings
- [ ] Semantic memory: codebase knowledge graph (Neo4j + Qdrant)
- [ ] Memory consolidation (short → long term)
- [ ] Memory retrieval ranking (recency × relevance)
- [ ] Cross-run knowledge sharing between agents

---

## Phase 0.5 — Evaluation & Observability

**Goal**: Full observability and benchmarked agent performance.

- [ ] SWE-bench evaluation harness
- [ ] HumanEval evaluation harness
- [ ] Latency / throughput benchmarks (pytest-benchmark)
- [ ] Cost tracking (token usage per run)
- [ ] Grafana dashboard (Prometheus metrics)
- [ ] Distributed tracing UI (Jaeger / Tempo)
- [ ] Replay engine (deterministic run replay from checkpoints)

---

## Phase 1.0 — Production Release

**Goal**: Stable, battle-tested, fully documented platform.

- [ ] Multi-user support (authentication + RBAC)
- [ ] Multi-tenant isolation
- [ ] Horizontal scaling (Kubernetes Helm chart)
- [ ] GPU support for Ollama
- [ ] Plugin system (third-party agent/tool contributions)
- [ ] Full API documentation
- [ ] Security audit
- [ ] Performance SLAs
