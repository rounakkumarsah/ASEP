# 13 — Competitor Mapping & Architectural Differentiation: ASEP

**Objective**: Rigorous capability-by-capability comparison between ASEP's implemented features and leading AI developer platforms based strictly on repository evidence.

---

## 1. Direct Competitor Comparison Matrix

| Capability | ASEP (Implemented) | LangGraph / LangSmith | CrewAI | Open WebUI | GitHub Copilot / Cursor |
|---|---|---|---|---|---|
| **Multi-Agent DAG Engine** | **Implemented** (`planner.py`, `supervisor.py`) | Implemented (Core library) | Implemented (Process/Crew) | Not Implemented (Chat UI only) | Partial (Inline completion / single agent) |
| **Sandboxed Docker Exec** | **Implemented** (`executor/docker.py`) | Partial (External runners) | Not Implemented (Runs on host) | Not Implemented | Partial (Local terminal / dev containers) |
| **HITL Cryptographic Gates** | **Implemented** (`governance/hitl.py`) | Implemented (Interrupts) | Partial (Human input flag) | Not Implemented | Partial (Manual accept diff) |
| **3-Tier Memory Architecture** | **Implemented** (Qdrant + Neo4j + Context) | Partial (Checkpointers) | Partial (Short/Long term) | Partial (RAG vector only) | Partial (File context indexing) |
| **MCP Tool Standard** | **Implemented** (`tools/mcp_client.py`) | Partial (Tool decorators) | Partial | Partial | Implemented (VS Code / Claude) |
| **Turnstile + RBAC Auth** | **Implemented** (`auth.py`, `Turnstile`) | Not Implemented (Cloud only) | Not Implemented | Implemented (Local auth) | Implemented (GitHub OAuth) |
| **Payment & Subscriptions** | **Implemented** (`payments.py`) | Not Implemented (SaaS backend) | Not Implemented | Not Implemented | Implemented (Stripe) |
| **Interactive 3D Control Plane**| **Implemented** (Next.js 15 + Canvas 3D) | Partial (LangSmith Web UI) | Not Implemented | Implemented (Chat UI) | Implemented (Desktop IDE) |

---

## 2. Key Architectural Differentiators

### 2.1 Decoupled Sandboxed Isolation vs. Host Execution
- *Competitor Baseline*: Most agent frameworks (CrewAI, AutoGen) run code directly on the host operating system, risking file corruption or unintended system command execution.
- *ASEP Advantage*: ASEP routes all execution through isolated Docker containers (`backend/src/executor/docker.py`) with CPU/Memory cgroup limits.

### 2.2 Native Multi-Tier Memory (Qdrant + Neo4j)
- *Competitor Baseline*: Most frameworks rely exclusively on single-dimension vector databases.
- *ASEP Advantage*: ASEP combines dense vector semantic search in Qdrant with relational code dependency graphs in Neo4j (`backend/src/memory/runtime.py`).

### 2.3 Air-Gapped Local LLM Support
- *Competitor Baseline*: Heavy reliance on closed proprietary cloud APIs (OpenAI / Anthropic).
- *ASEP Advantage*: First-class Ollama provider (`backend/src/ai_runtime/providers/ollama.py`) enabling fully air-gapped, zero-data-retention on-premise execution.
