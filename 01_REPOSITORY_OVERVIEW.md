# 01 — Repository Overview: ASEP (Autonomous Software Engineering Platform)

**Architecture Classification**: Polyglot Monorepo (Next.js 15 App Router Frontend + FastAPI / LangGraph Async Backend + Hybrid Storage Architecture)  
**Target Domain**: Enterprise Autonomous Software Engineering Control Plane & Multi-Agent Execution Runtime  
**Analysis Date**: August 2026

---

## 1. System Architecture High-Level Map

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               ASEP CONTROL PLANE UI (Next.js 15)                       │
│  - Landing & Showcase (3D Neural Matrix Canvas, Interactive DAG, Telemetry Marquee)   │
│  - Dashboard Suite: Sessions, Projects, Knowledge RAG, Governance Gates, Metrics, Auth│
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ HTTPS / SSE / JSON REST
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FASTAPI ASYNC BACKEND (Python 3.11+)                   │
│  - Routers: Auth, Agent Runs, HITL Governance, Knowledge Sync, Memory, RAG, Payments  │
│  - Middleware: Structured Logging, Sentry Error Tracking, Rate Limiting, Auth Context │
└───────┬──────────────┬───────────────┬────────────────┬───────────────┬────────────────┘
        │              │               │                │               │
        ▼              ▼               ▼                ▼               ▼
┌──────────────┐ ┌───────────┐ ┌───────────────┐ ┌─────────────┐ ┌──────────────┐
│  PostgreSQL  │ │   Redis   │ │  Qdrant RAG   │ │ Neo4j Graph │ │  Docker SDK  │
│ (Relational  │ │  (Streams │ │ (Vector       │ │ (Knowledge  │ │  (Isolated   │
│  & Auth DB)  │ │  & Cache) │ │  Embeddings)  │ │  & AST RAG) │ │  Sandboxes)  │
└──────────────┘ └───────────┘ └───────────────┘ └─────────────┘ └──────────────┘
```

---

## 2. Directory Structure Breakdown

### 2.1 Frontend (`/frontend`)
- **Runtime & Framework**: Next.js 15.1.0 (App Router), React 19, TypeScript 5.7.
- **Styling & UI**: TailwindCSS v3.4, Radix UI primitives, Lucide React icons, Framer Motion v11, `next-themes` (Class-based dark/light mode system).
- **Core Route Groups**:
  - `app/(auth)/`: Auth flows (`/login`, `/signup`, `/forgot-password`, `/reset-password`, `/verify-email`, `/callback`).
  - `app/(dashboard)/`: Multi-agent operational control plane (`/overview`, `/sessions`, `/projects`, `/knowledge`, `/memory`, `/governance`, `/approvals`, `/metrics`, `/audit`, `/billing`, `/api-keys`, `/settings`, `/playground`, `/research`, `/evaluation`, `/copilot`).
  - Public Marketing & Information: `/`, `/pricing`, `/documentation`, `/api-docs`, `/architecture`, `/roadmap`, `/changelog`, `/about`, `/contact`, `/privacy`, `/terms`.

### 2.2 Backend (`/backend`)
- **Core Framework**: FastAPI, Uvicorn, Pydantic v2, Python 3.11+.
- **Agent Orchestration**: LangGraph, LangChain core, custom state machines, Supervisor agent, Research Swarm, and Deconstruction Planner.
- **AI Runtime Providers**: Google Gemini (`google-generativeai`), OpenAI API, Ollama (Local LLM backend), and Mock testing harness.
- **Storage Subsystems**:
  - PostgreSQL 16 via SQLAlchemy 2.0 Async (`asyncpg`) & Alembic migration engine.
  - Redis 7 for task distribution, caching, and stream messaging.
  - Qdrant for dense vector storage & cosine similarity retrieval (384/768/1536-dim embeddings).
  - Neo4j for semantic knowledge graphs and code AST relationship mapping.
- **Tool Protocol**: Model Context Protocol (MCP) v1.0 standard tool registry with Dockerized isolated sandboxing.

### 2.3 Deployment & Infrastructure (`/docker`, root)
- `docker-compose.yml`: Full stack production orchestration (FastAPI backend, Next.js frontend, PostgreSQL 16 Alpine, Redis 7 Alpine, Qdrant Vector DB).
- `Dockerfile` (Backend): Multi-stage Python build with security non-root user and healthcheck curling `/health`.
- `Dockerfile` (Frontend): Standalone optimized Next.js container output.
- `alembic/`: Complete database versioning with auto-generating migration scripts.

---

## 3. Technology Stack Inventory

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend Framework** | Next.js App Router | 15.1.0 | Server-side rendering, static generation, API proxies |
| **Language (Web)** | TypeScript | 5.7.2 | Strict type safety across client interfaces |
| **Styling & Theme** | TailwindCSS + CSS Vars | 3.4.1 | Fluid responsive design, dark/light token switching |
| **Animation** | Framer Motion | 11.15.0 | Dynamic layout springs, 3D Canvas matrix, gestures |
| **Backend Framework** | FastAPI | 0.115.6+ | Asynchronous REST and streaming runtime |
| **Agent Engine** | LangGraph & LangChain | 0.2.0+ | Stateful multi-agent graph orchestration |
| **Relational DB** | PostgreSQL & SQLAlchemy | 16 / 2.0 | Transactional persistence, auth, audit trails |
| **Vector Database** | Qdrant | Latest | Episodic & semantic memory embeddings |
| **Graph Database** | Neo4j | 5.x | Procedural memory and architectural AST mappings |
| **Cache & Queue** | Redis | 7.x | Token throttling, ephemeral state, distributed cache |
| **Container Engine** | Docker SDK for Python | 7.1.0 | Ephemeral sandbox execution environments |
| **Observability** | Sentry SDK & OpenTelemetry | Latest | Distributed error tracking, latency traces |
