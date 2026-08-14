# 12 — Platform Capabilities & Architectural Grouping: ASEP

This document structures every implemented capability into standard Enterprise Platform Pillars based strictly on repository evidence.

---

## 1. Enterprise Platform Pillars

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ASEP PLATFORM PILLARS                                │
├─────────────────────────┬──────────────────────────┬───────────────────────────────────┤
│ 1. AI Execution Core    │ 2. Security & Governance │ 3. Data & Memory Subsystems       │
│ • LangGraph State Graph │ • HITL Approval Machine  │ • Qdrant Vector Semantic RAG      │
│ • Multi-Provider Router │ • Cryptographic Signers  │ • Neo4j Code AST Graph Store      │
│ • Sandboxed Docker Exec │ • Turnstile Captcha Auth │ • PostgreSQL Transactional Store  │
│ • MCP Standard Registry │ • Structured Audit Logs  │ • Redis Sliding Window Rate-Limit │
├─────────────────────────┼──────────────────────────┼───────────────────────────────────┤
│ 4. Developer Experience │ 5. Enterprise SaaS Layer │ 6. Observability & Telemetry      │
│ • 3D Neural Matrix UI   │ • Organization Scopes    │ • Real-time Node Telemetry Stream │
│ • Interactive DAG Graph │ • Razorpay Subscriptions │ • Sentry Error Ingestion          │
│ • Copilot & Playground  │ • Scoped API Key Engine  │ • Cluster Health Diagnostic Probe │
│ • OpenAPI Specs (/docs) │ • Billing Portal Webhook │ • Microsecond Latency Counters    │
└─────────────────────────┴──────────────────────────┴───────────────────────────────────┘
```

---

## 2. Pillar-by-Pillar Implementation Analysis

### Pillar 1: AI Execution Core
- **Multi-Model Routing**: `backend/src/ai_runtime/service.py` connects to Gemini 1.5 Pro, GPT-4o, and Ollama with dynamic fallback.
- **Agent Orchestration**: `backend/src/agents/planner.py` compiles goal strings into deterministic DAGs.
- **Model Context Protocol (MCP)**: `backend/src/tools/mcp_client.py` standardizes dynamic external tool connections.

### Pillar 2: Security & Governance
- **HITL Gatekeeper**: `backend/src/governance/hitl.py` implements an interactive resume-token pause/resume approval engine.
- **Perimeter Defense**: `backend/src/api/app.py` enforces strict CSP headers, HSTS, X-Frame-Options, and Turnstile bot protection.
- **Audit Compliance**: `backend/src/api/routers/audit.py` records every action with IP, user-agent, and payload snapshots.

### Pillar 3: Data & Memory Subsystems
- **Relational Integrity**: PostgreSQL 16 via SQLAlchemy 2.0 Async with Alembic schema versioning.
- **Vector Retrieval**: Qdrant client (`backend/src/db/qdrant.py`) with cosine similarity collections.
- **Graph AST Persistence**: Neo4j driver (`backend/src/graph/neo4j.py`) tracking code entity dependencies.

### Pillar 4: Developer Experience & UI Control Plane
- **Next.js 15 App Router Suite**: 38 static and dynamic routes.
- **Visual Canvases**: 3D Neural Matrix canvas (`src/components/ui/neural-network-viz.tsx`) and dynamic DAG beam architecture diagram (`src/components/landing/architecture.tsx`).
- **Dark/Light Theme**: 100% semantic CSS tokens with zero hydration mismatch.

### Pillar 5: Enterprise SaaS & Monetization
- **Organization Management**: Multi-tenant team slug creation and ownership bindings (`backend/src/api/routers/organizations.py`).
- **Payments**: Razorpay order generation, signature verification, and webhook handling (`backend/src/api/routers/payments.py`).

### Pillar 6: Observability & Telemetry
- **Diagnostics**: `/api/v1/diagnostics/system` checks connectivity to Postgres, Redis, and Qdrant.
- **Live Metrics**: Cluster CPU/Memory gauges and real-time terminal stdout streams.
