# 02 — Feature Inventory: ASEP

This document details every feature implemented across the ASEP platform, backed by direct file path evidence, implementation depth, status, and layer-by-layer verification.

---

## 1. Authentication & Identity Management

- **Purpose**: Secure developer registration, password-hash management, JWT session cookies, email confirmation, password resets, and Cloudflare Turnstile anti-bot verification.
- **Current Status**: Production Ready (95% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(auth)/login/page.tsx`, `signup/page.tsx`, `forgot-password/page.tsx`, `reset-password/page.tsx`, `verify-email/page.tsx`, `frontend/src/components/auth/turnstile.tsx`, `frontend/src/lib/api/services/auth.ts`.
  - Backend: `backend/src/api/routers/auth.py`, `backend/src/auth/jwt.py`, `backend/src/auth/password.py`, `backend/src/db/models/user.py`.
  - Database: `users` table with bcrypt hash, email confirmation tokens, rate limit counters, active status.
- **AI Integration**: N/A (Standard security perimeter).

---

## 2. Multi-Agent Orchestration & Planning (DAG Engine)

- **Purpose**: Autonomous decomposition of high-level coding goals into Directed Acyclic Graphs (DAGs) of executable subtasks with parallel worker routing.
- **Current Status**: Working / Beta (88% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/sessions/page.tsx`, `frontend/src/app/(dashboard)/sessions/[id]/page.tsx`, `frontend/src/components/landing/architecture.tsx`.
  - Backend: `backend/src/agents/planner.py`, `backend/src/agents/supervisor.py`, `backend/src/agents/state.py`, `backend/src/agents/registry.py`, `backend/src/api/routers/agent_runs.py`, `backend/src/api/routers/tasks.py`.
  - Database: `agent_runs`, `tasks` tables recording execution state, error traces, and token costs.
- **AI Integration**: Multi-model routing (Gemini 1.5 Pro / GPT-4o / Ollama) via LangGraph stateful graph compilation.

---

## 3. Sandboxed Execution Engine (Isolated Container Workspaces)

- **Purpose**: Safe compilation, testing, and file editing in isolated Docker environments to prevent host filesystem pollution.
- **Current Status**: Working / Beta (85% Complete).
- **Files**:
  - Frontend: `frontend/src/components/landing/features.tsx` (Terminal execution stream).
  - Backend: `backend/src/executor/docker.py`, `backend/src/executor/sandbox.py`, `backend/src/tools/impl.py`, `backend/src/tools/router.py`.
  - Infrastructure: `docker-compose.yml`, Docker daemon integration via Python Docker SDK.
- **AI Integration**: Dynamic tool execution for shell commands, git operations, file writes, and test runners with automated timeout enforcement.

---

## 4. Multi-Layer Memory System (Working, Semantic, Procedural)

- **Purpose**: 3-tiered memory architecture:
  1. *Working Memory*: In-context active sliding window for session state.
  2. *Semantic Memory*: Vectorized RAG memory stored in Qdrant.
  3. *Procedural Memory*: Graph-structured execution workflows in Neo4j.
- **Current Status**: Working (82% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/memory/page.tsx`, `frontend/src/lib/api/services/memory.ts`.
  - Backend: `backend/src/memory/runtime.py`, `backend/src/memory/working.py`, `backend/src/memory/semantic.py`, `backend/src/memory/procedural.py`, `backend/src/api/routers/memory.py`, `backend/src/api/routers/rag.py`.
  - Database: Qdrant collection `asep_memory`, Neo4j graph nodes `MemoryNode`, PostgreSQL `memory_entries`.
- **AI Integration**: Embeddings generated via OpenAI `text-embedding-3-small` / Gemini embeddings with cosine similarity filtering.

---

## 5. Governance & Human-in-the-Loop (HITL) Gatekeeper

- **Purpose**: Enforce cryptographic verification and human approval checkpoints for high-risk operations (e.g., prod database migrations, destructive terminal commands, PR merges).
- **Current Status**: Working / Beta (90% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/governance/page.tsx`, `frontend/src/app/(dashboard)/approvals/page.tsx`, `frontend/src/lib/api/services/governance.ts`.
  - Backend: `backend/src/governance/hitl.py`, `backend/src/governance/policy_engine.py`, `backend/src/governance/guardrails.py`, `backend/src/api/routers/hitl.py`.
  - Database: `audit_logs` and pending approval state tables.
- **AI Integration**: Real-time intent classification to detect destructive shell scripts (`rm -rf`, `DROP TABLE`) and trigger approval interrupts.

---

## 6. Knowledge Hub & Codebase Ingestion (RAG)

- **Purpose**: Index repository documents, architecture markdown files, and codebase chunks to supply grounded context during agent planning.
- **Current Status**: Working (80% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/knowledge/page.tsx`, `frontend/src/lib/api/services/knowledge.ts`.
  - Backend: `backend/src/knowledge/service.py`, `backend/src/knowledge/sources.py`, `backend/src/knowledge/sync.py`, `backend/src/api/routers/knowledge.py`, `backend/src/api/routers/knowledge_sync.py`.
  - Database: `knowledge_documents` table in PostgreSQL, vector collections in Qdrant.
- **AI Integration**: Chunking, metadata tagging, and dense vector embeddings.

---

## 7. Model Context Protocol (MCP) Tool Registry

- **Purpose**: Standardized tool interface exposing filesystem, terminal, git, and custom enterprise tools via the Anthropic MCP standard.
- **Current Status**: Working (85% Complete).
- **Files**:
  - Backend: `backend/src/tools/registry.py`, `backend/src/tools/mcp_client.py`, `backend/src/tools/base.py`, `backend/src/tools/permissions.py`.
  - Frontend: `frontend/src/components/landing/integrations.tsx`.
- **AI Integration**: Standardized JSON Schema definition for LLM tool calling and automatic argument validation.

---

## 8. Continuous Evaluation & Quality Scoring

- **Purpose**: Autonomous validation scoring mechanisms measuring accuracy, security compliance, latency, and code coverage before committing PRs.
- **Current Status**: Working / Prototype (78% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/evaluation/page.tsx`, `frontend/src/lib/api/services/evaluation.ts`.
  - Backend: `backend/src/evaluation/evaluator.py`, `backend/src/evaluation/scoring.py`, `backend/src/evaluation/metrics.py`, `backend/src/api/routers/evaluation.py`.
- **AI Integration**: Automated LLM-as-a-judge scoring with rubrics for code quality, syntax correctness, and security.

---

## 9. API Key Management & Developer Access

- **Purpose**: Issue, revoke, and track scoped API keys with rate-limiting and usage quotas.
- **Current Status**: Production Ready (92% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/api-keys/page.tsx`.
  - Backend: `backend/src/api/routers/api_keys.py`, `backend/src/db/models/api_key.py`.
  - Database: `api_keys` table with SHA-256 hashed secret keys, permission scopes, and expiration timestamps.

---

## 10. Billing, Subscriptions & Stripe Payments

- **Purpose**: Subscription management, plan tier enforcement (Developer, Team, Enterprise), invoice generation, and Stripe webhook handling.
- **Current Status**: Working / Beta (85% Complete).
- **Files**:
  - Frontend: `frontend/src/app/(dashboard)/billing/page.tsx`, `frontend/src/app/pricing/page.tsx`, `frontend/src/lib/api/services/payments.ts`.
  - Backend: `backend/src/api/routers/payments.py`, `backend/src/db/models/payment.py`, `backend/src/db/models/subscription.py`.
  - Database: `payments`, `subscriptions` tables storing Stripe customer and subscription IDs.
