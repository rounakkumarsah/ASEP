# 05 — API Inventory: ASEP

This document catalogs every API endpoint implemented in the FastAPI backend, detailing HTTP methods, URL routes, authentication requirements, and current operational status.

---

## 1. Authentication (`/api/v1/auth`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user with password hash & Turnstile check | No | Production Ready |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue JWT cookie & token | No | Production Ready |
| `POST` | `/api/v1/auth/logout` | Clear auth cookies and invalidate token | Yes (JWT) | Production Ready |
| `GET` | `/api/v1/auth/me` | Retrieve current authenticated user profile | Yes (JWT) | Production Ready |
| `POST` | `/api/v1/auth/forgot-password` | Request password reset token via email | No | Production Ready |
| `POST` | `/api/v1/auth/reset-password` | Reset password using verified token | No | Production Ready |
| `POST` | `/api/v1/auth/verify-email` | Confirm email address token | No | Production Ready |

---

## 2. Health & Telemetry (`/health`, `/api/v1/metrics`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `GET` | `/health` | Liveness and readiness probe for Docker / K8s | No | Production Ready |
| `GET` | `/api/v1/metrics/cluster` | Real-time cluster stats (CPU, Memory, Sandboxes) | Yes (JWT / API Key) | Production Ready |
| `GET` | `/api/v1/diagnostics/system` | Detailed diagnostic trace of Postgres, Redis, Qdrant | Yes (Admin) | Beta |

---

## 3. Agent Runs & Tasks (`/api/v1/agent-runs`, `/api/v1/tasks`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `POST` | `/api/v1/agent-runs` | Trigger a new autonomous agent execution session | Yes (JWT / API Key) | Beta |
| `GET` | `/api/v1/agent-runs` | List all agent sessions with status filters | Yes (JWT / API Key) | Beta |
| `GET` | `/api/v1/agent-runs/{id}` | Get detailed run traces, steps, and subagent trees | Yes (JWT / API Key) | Beta |
| `POST` | `/api/v1/agent-runs/{id}/cancel` | Terminate an active agent execution session | Yes (JWT / API Key) | Beta |
| `GET` | `/api/v1/tasks` | List active tasks in the orchestration queue | Yes (JWT / API Key) | Beta |

---

## 4. Governance & Approvals (`/api/v1/hitl`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `GET` | `/api/v1/hitl/pending` | List pending HITL approval gates | Yes (JWT) | Beta |
| `POST` | `/api/v1/hitl/{gate_id}/approve` | Cryptographically sign and release pending action | Yes (JWT) | Beta |
| `POST` | `/api/v1/hitl/{gate_id}/reject` | Reject and abort proposed action | Yes (JWT) | Beta |

---

## 5. Knowledge & RAG (`/api/v1/knowledge`, `/api/v1/rag`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `GET` | `/api/v1/knowledge/documents` | List indexed repository documentation files | Yes (JWT / API Key) | Working |
| `POST` | `/api/v1/knowledge/upload` | Upload & chunk markdown / codebase document | Yes (JWT / API Key) | Working |
| `POST` | `/api/v1/knowledge/sync` | Trigger asynchronous repository re-indexing | Yes (JWT / API Key) | Working |
| `POST` | `/api/v1/rag/query` | Semantic vector search query over indexed corpus | Yes (JWT / API Key) | Working |

---

## 6. Memory System (`/api/v1/memory`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `GET` | `/api/v1/memory` | Retrieve episodic and working memory entries | Yes (JWT / API Key) | Working |
| `POST` | `/api/v1/memory/consolidate` | Trigger memory compaction and semantic storage | Yes (JWT / API Key) | Working |

---

## 7. API Keys & Developers (`/api/v1/api-keys`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `GET` | `/api/v1/api-keys` | List user's active API keys and scopes | Yes (JWT) | Production Ready |
| `POST` | `/api/v1/api-keys` | Generate new API key with name and scopes | Yes (JWT) | Production Ready |
| `DELETE` | `/api/v1/api-keys/{id}` | Revoke and deactivate an API key | Yes (JWT) | Production Ready |

---

## 8. Billing & Payments (`/api/v1/payments`)

| Method | Endpoint | Purpose | Auth Required | Status |
|---|---|---|---|---|
| `POST` | `/api/v1/payments/checkout-session` | Create Stripe checkout session for Team/Pro tier | Yes (JWT) | Beta |
| `POST` | `/api/v1/payments/customer-portal` | Generate Stripe Customer Billing Portal link | Yes (JWT) | Beta |
| `POST` | `/api/v1/payments/webhook` | Process Stripe subscription and invoice webhooks | Signature Verified | Production Ready |
