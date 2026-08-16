# 04 — API Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Exhaustive inspection of `backend/src/api/routers/` and `backend/src/api/app.py`.

---

## 1. Registered Routers & Endpoint Inventory

The FastAPI backend registers **21 distinct API Routers** (`backend/src/api/app.py` Lines 243–267).

### 1.1 Authentication & User Access (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Register user with bcrypt password hash & Turnstile check.
- `POST /api/v1/auth/login`: Authenticate and issue JWT access cookie.
- `POST /api/v1/auth/logout`: Invalidate session and clear auth cookies.
- `GET /api/v1/auth/me`: Retrieve current authenticated user record.
- `POST /api/v1/auth/forgot-password`: Dispatch password reset request.
- `POST /api/v1/auth/reset-password`: Reset password using verified token.
- `POST /api/v1/auth/verify-email`: Verify email confirmation token.

### 1.2 Observability & Health Probes (`/health`, `/ready`, `/metrics`, `/diagnostics`)
- `GET /health`: Liveness probe for Docker/K8s (returns 200 OK).
- `GET /ready`: Readiness probe checking PostgreSQL, Redis, and Qdrant connections.
- `GET /metrics`: Application and cluster performance telemetry.
- `GET /diagnostics`: System diagnostics and dependency latency.
- `GET /api/v1/monitoring/dashboard`: Queue depth, active agent count, error rate, and captured cost in USD.

### 1.3 Agent Runs & Tasks (`/api/v1/agent-runs`, `/api/v1/tasks`)
- `POST /api/v1/agent-runs`: Trigger new multi-agent autonomous execution.
- `GET /api/v1/agent-runs`: List agent sessions with status/project filters.
- `GET /api/v1/agent-runs/{id}`: Detailed run timeline, steps, and subtasks.
- `POST /api/v1/agent-runs/{id}/cancel`: Cancel active agent session.
- `GET /api/v1/tasks`: List active execution tasks.

### 1.4 Governance & Human-in-the-Loop (`/api/v1/governance/hitl`)
- `GET /api/v1/governance/hitl/queue`: List pending and resolved review sessions.
- `GET /api/v1/governance/hitl/statistics`: Approval SLA latency and escalation statistics.
- `POST /api/v1/governance/hitl/review`: Submit human approval/rejection decision.

### 1.5 Memory & RAG Retrieval (`/api/v1/memory`, `/api/v1/rag`)
- `GET /api/v1/memory`: Retrieve working and semantic memory entries.
- `POST /api/v1/memory/consolidate`: Compact context into vector storage.
- `POST /api/v1/rag/query`: Dense vector similarity query over Qdrant collections.

### 1.6 Knowledge Documents & Sync (`/api/v1/knowledge`, `/api/v1/knowledge/sync`)
- `GET /api/v1/knowledge/documents`: List indexed documentation files.
- `POST /api/v1/knowledge/upload`: Upload, chunk, and embed documents.
- `POST /api/v1/knowledge/sync`: Trigger asynchronous knowledge sync.

### 1.7 Developer API Keys (`/api/v1/api-keys`)
- `GET /api/v1/api-keys`: List active API keys and scopes.
- `POST /api/v1/api-keys`: Generate SHA-256 hashed API key.
- `DELETE /api/v1/api-keys/{id}`: Revoke developer API key.

### 1.8 Monetization & Payments (`/api/v1/payments`)
- `POST /api/v1/payments/create-order`: Create Razorpay payment order.
- `POST /api/v1/payments/verify`: Server-side HMAC-SHA256 signature verification.
- `POST /api/v1/payments/webhook`: Process Razorpay webhook events.
- `GET /api/v1/payments/subscription`: Retrieve active user subscription status.

### 1.9 Multi-Tenant Organizations & Projects (`/api/v1/organizations`, `/api/v1/projects`)
- `GET /api/v1/organizations`: List user organizations.
- `POST /api/v1/organizations`: Create new organization workspace.
- `GET /api/v1/projects`: List workspace projects.
- `POST /api/v1/projects`: Create project with repository URL binding.

### 1.10 Evaluation & Benchmarks (`/api/v1/evaluation`)
- `GET /api/v1/evaluation/runs`: List past evaluation runs.
- `POST /api/v1/evaluation/evaluate`: Trigger automated code scoring.
