# ASEP — System Architecture

> **Version**: 0.1.0 (Scaffold)
> **Status**: Phase 0.1 complete

---

## Overview

ASEP follows **Clean Architecture** with **Domain-Driven Design** principles. Every layer has a single responsibility and depends only on layers below it.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│                    Dashboard · REST API                     │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────▼───────────────────────────────┐
│                   API Layer (FastAPI)                       │
│              Routers · Schemas · Middleware                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│               Agent Runtime (LangGraph)                     │
│         Supervisor → Planner → Worker Agents                │
│              Checkpoint · Registry · State                  │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
  ┌────▼────┐   ┌─────▼────┐  ┌────▼────┐  ┌─────▼────┐
  │ Memory  │   │Knowledge │  │Governance│  │  Tools   │
  │ Service │   │ Service  │  │ Service  │  │ Registry │
  └────┬────┘   └─────┬────┘  └─────────┘  └──────────┘
       │              │
┌──────▼──────────────▼──────────────────────────────────────┐
│                   Database Layer                            │
│    PostgreSQL · Redis · Neo4j · Qdrant · Ollama             │
└─────────────────────────────────────────────────────────────┘
```

---

## Architectural Principles

### Clean Architecture
- **Entities** — Core domain objects (AgentState, Task, MemoryEntry)
- **Use Cases** — Application logic (SubmitRun, PlanTask, SearchMemory)
- **Interface Adapters** — FastAPI routers, DB repositories
- **Infrastructure** — PostgreSQL, Redis, Neo4j, Qdrant, Ollama

Dependencies **always point inward**. Inner layers never import from outer layers.

### Domain-Driven Design
Each bounded context has its own package:
- `agents/` — Agent lifecycle domain
- `memory/` — Memory domain
- `knowledge/` — Knowledge graph domain
- `governance/` — Policy & audit domain
- `evaluation/` — Benchmarking domain
- `replay/` — Trace replay domain

### SOLID
- **S** — Each class/function has one reason to change
- **O** — Extend via new classes, not modifying existing ones
- **L** — All implementations are substitutable for their abstractions
- **I** — Small, focused interfaces (no god-objects)
- **D** — Depend on abstractions (protocols), not concrete implementations

---

## Key Components

### API Layer (`src/api/`)
FastAPI application factory pattern. All routers are plug-in modules. CORS, exception handlers, and middleware are configured centrally in `app.py`.

### Agent Runtime (`src/agents/`)
LangGraph-based multi-agent system. The **Supervisor** routes between specialised **Worker Agents** based on the current plan step. All state is typed via `AgentState` and persisted via LangGraph checkpointers.

### Memory System (`src/memory/`)
Three-tier memory:
- **Working memory** — Redis (ephemeral, fast)
- **Episodic memory** — Qdrant (vector similarity, agent history)
- **Semantic memory** — Qdrant + Neo4j (code knowledge graph)

### Governance (`src/governance/`)
Policy-as-code engine that intercepts every agent tool call. Enforces budgets, RBAC, rate limits, and writes full audit trails to PostgreSQL.

### Knowledge Graph (`src/knowledge/`)
Neo4j stores the code graph (file → module → class → function). Qdrant stores code embeddings for semantic retrieval.

---

## Data Flow: Agent Run

```
User Request
    │
    ▼
POST /api/v1/tasks
    │
    ▼
ExecutionEngine.submit(goal)
    │
    ▼
LangGraph Graph:
  [Planner] → decompose goal → plan[]
      │
      ▼
  [Supervisor] → route → [Worker Agent]
      │                       │
      │                  GovernanceService.check_policy()
      │                       │
      │                  ToolRegistry.invoke(tool)
      │                       │
      ◄───────────── result ──┘
      │
      ▼  (all steps done)
  [Finaliser] → produce output
    │
    ▼
Response streamed to user
```

---

## Database Schema (TODO Phase 0.2)

| Table | Database | Purpose |
|---|---|---|
| `agent_runs` | PostgreSQL | Run metadata, status, timing |
| `tasks` | PostgreSQL | Individual task records |
| `audit_log` | PostgreSQL | Immutable governance audit trail |
| `memory_entries` | PostgreSQL | Structured memory metadata |
| *(vectors)* | Qdrant | Memory + code embeddings |
| *(graph)* | Neo4j | Code knowledge graph |
| *(cache)* | Redis | Ephemeral state, rate limits |
