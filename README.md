# ASEP — Autonomous Software Engineering Platform

<div align="center">

```
   █████╗ ███████╗███████╗██████╗ 
  ██╔══██╗██╔════╝██╔════╝██╔══██╗
  ███████║███████╗█████╗  ██████╔╝
  ██╔══██║╚════██║██╔══╝  ██╔═══╝ 
  ██║  ██║███████║███████╗██║     
  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     
```

### **Enterprise-Grade Local-First AI Engineering Operating System**

*Orchestrate autonomous agent swarms, compile deterministic task graphs, enforce cryptographic human-in-the-loop policies, and execute code in isolated container sandboxes.*

---

[![CI/CD Pipeline](https://github.com/rounakkumarsah/ASEP/actions/workflows/push-main.yml/badge.svg)](https://github.com/rounakkumarsah/ASEP/actions)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.1.0-black?style=flat&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=flat)](https://github.com/langchain-ai/langgraph)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-336791?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_RAG-DC2626?style=flat)](https://qdrant.tech/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_AST-008CC1?style=flat&logo=neo4j)](https://neo4j.com/)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed_Exec-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Live Landing Page](http://localhost:3000) • [API Documentation](http://localhost:8000/docs) • [Architecture Report](01_REPOSITORY_OVERVIEW.md) • [Enterprise Due Diligence](11_ENTERPRISE_FEATURES.md)

</div>

---

## 1. Executive Summary & Core Value

**ASEP (Autonomous Software Engineering Platform)** is an enterprise control plane that transforms high-level engineering objectives into verified, compiled code. Unlike standard chat-based copilots or single-prompt scripts, ASEP deploys specialized multi-agent graphs that deconstruct goals, query 3-tier memory stores, execute operations inside isolated Docker sandboxes, and submit critical state mutations to Human-in-the-Loop (HITL) approval gates.

```
                  ┌──────────────────────────────────────────────┐
                  │           User Goal / Issue Trigger          │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    LangGraph Deconstruction Planner (DAG)    │
                  └──────────────┬────────────────┬──────────────┘
                                 │                │
                    ┌────────────┴───┐        ┌───┴────────────┐
                    ▼                ▼        ▼                ▼
             ┌─────────────┐  ┌─────────────┐ ┌─────────────┐  ┌─────────────┐
             │ Research    │  │ Memory Graph│ │ Codebase    │  │ Sandboxed   │
             │ Swarm       │  │ (Neo4j RAG) │ │ Vector DB   │  │ Docker Exec │
             └──────┬──────┘  └──────┬──────┘ └──────┬──────┘  └──────┬──────┘
                    │                │               │                │
                    └────────────────┴───────┬───────┴────────────────┘
                                             │
                                             ▼
                  ┌──────────────────────────────────────────────┐
                  │       Governance Guardrail & HITL Gate       │
                  └──────────────────────┬───────────────────────┘
                                         │ Cryptographic Signature
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    Autonomous Evaluation & PR Verification   │
                  └──────────────────────────────────────────────┘
```

---

## 2. Visual Previews & Showcase

### 2.1 3D Neural Matrix & Marketing Control Plane
![ASEP Landing Page Preview](docs/images/landing.png)
> *Figure 1: High-FPS 3D Neural Matrix Canvas with orbital inertia and live node telemetry.*

### 2.2 Live Product Dashboard & Task Stream
![ASEP Dashboard Preview](docs/images/dashboard.png)
> *Figure 2: Real-time telemetry, agent task queues, governance gates, and stdout streaming.*

---

## 3. Key Differentiators: Why ASEP?

| Dimension | Generic AI Copilots | AutoGen / CrewAI Scripts | ASEP Enterprise Platform |
|---|---|---|---|
| **Execution Isolation** | Host machine / Local IDE | Direct host execution (Risky) | **Isolated Docker Sandboxes (`backend/src/executor/docker.py`)** |
| **Governance & Safety** | Manual diff review | Uncontrolled loops | **Cryptographic HITL Gates (`backend/src/governance/hitl.py`)** |
| **Memory Architecture** | In-context sliding window | Flat JSON or single Vector DB | **3-Tier: Working + Qdrant Vector + Neo4j Graph AST** |
| **Tool Protocol** | Proprietary wrappers | Ad-hoc Python functions | **Model Context Protocol (MCP v1.0) Standard Client** |
| **Air-Gap Readiness** | Cloud API only | Cloud API only | **Native Ollama Local LLM Runtime (`providers/ollama.py`)** |
| **SaaS & Monetization** | N/A | N/A | **Razorpay Orders, JWT Auth, Turnstile, Scoped API Keys** |

---

## 4. Comprehensive Feature Matrix

<details open>
<summary><b>Core Subsystems & Enterprise Capabilities</b></summary>
<br>

- **Autonomous Planning**: LangGraph supervisor decomposing complex engineering goals into Directed Acyclic Graphs (`backend/src/agents/planner.py`).
- **Human-in-the-Loop (HITL)**: Interactive pause/resume state machine with resume tokens, risk assessment (`Low`, `Medium`, `High`, `Critical`), and SLA latency metrics (`backend/src/governance/hitl.py`).
- **Model Context Protocol (MCP)**: Standardized dynamic client discovery and tool dispatching (`backend/src/tools/mcp_client.py`).
- **3-Layer Memory & Codebase Ingestion**:
  - *Working Memory*: In-context session sliding window (`backend/src/memory/working.py`).
  - *Semantic Memory*: Qdrant dense vector store with cosine similarity (`backend/src/memory/semantic.py`).
  - *Procedural Memory*: Neo4j code AST and execution relationship graph (`backend/src/graph/neo4j.py`).
- **Multi-Model AI Runtime**: Polymorphic router dynamically load-balancing across Google Gemini, OpenAI GPT-4o, and local Ollama (`backend/src/ai_runtime/service.py`).
- **Enterprise Security**: Cloudflare Turnstile bot verification, bcrypt salted password hashing, httpOnly JWT cookies, and strict CSP headers (`backend/src/api/app.py`).
- **Observability & Health Probes**: Live cluster metrics, Prometheus endpoints, and Sentry distributed error tracking (`backend/src/api/routers/health.py`).

</details>

---

## 5. System Architecture

```mermaid
graph TD
    subgraph Client Layer [Next.js 15 App Router Frontend]
        Landing[Showcase & 3D Matrix]
        Dashboard[Sessions & Overview]
        GovUI[HITL Approvals]
        MemUI[Memory Inspector]
    end

    subgraph Backend API [FastAPI Async Application Factory]
        RouterAuth[Auth & Turnstile]
        RouterAgents[Agent Runs & Tasks]
        RouterHITL[Governance & Policy]
        RouterMemory[Memory & RAG]
        RouterPay[Razorpay Payments]
    end

    subgraph AI Runtime [LangGraph Agent Core]
        Supervisor[Agent Supervisor]
        Planner[DAG Deconstruction]
        Swarm[Research Swarm]
        MCPClient[MCP Tool Registry]
    end

    subgraph Storage & Infrastructure [Persistent Layer]
        PG[(PostgreSQL 16)]
        Redis[(Redis 7 Streams)]
        Qdrant[(Qdrant Vector DB)]
        Neo4j[(Neo4j Graph DB)]
        DockerEngine[Docker Container Sandboxes]
    end

    ClientLayer -->|REST / SSE JSON| BackendAPI
    BackendAPI --> AIRuntime
    BackendAPI --> Storage&Infrastructure
    AIRuntime --> DockerEngine
    AIRuntime --> Qdrant
    AIRuntime --> Neo4j
```

---

## 6. Repository Layout

```
ASEP/
├── backend/                         # FastAPI & Python Agent Runtime
│   ├── alembic/                     # 7 Database migration scripts
│   ├── src/
│   │   ├── agents/                  # LangGraph planner, supervisor, swarm
│   │   ├── ai_runtime/              # Gemini, OpenAI, Ollama providers
│   │   ├── api/                     # 21 REST routers & middleware
│   │   ├── auth/                    # JWT, bcrypt, Turnstile validation
│   │   ├── db/                      # SQLAlchemy models & DB pool drivers
│   │   ├── executor/                # Docker sandbox execution engine
│   │   ├── governance/              # HITL state machine & policy engine
│   │   ├── memory/                  # Working, semantic, procedural memory
│   │   └── tools/                   # MCP client & sandboxed tool suite
│   ├── tests/                       # Unit & integration test suites
│   ├── Dockerfile                   # Multi-stage production container build
│   └── pyproject.toml               # Python 3.12 dependencies
├── frontend/                        # Next.js 15 Control Plane Dashboard
│   ├── src/
│   │   ├── app/                     # 38 static/dynamic routes (App Router)
│   │   ├── components/              # 3D Matrix Canvas, Bento, ThemeToggle
│   │   └── lib/                     # API client services & react-query
│   ├── Dockerfile                   # Standalone Next.js container build
│   └── package.json                 # React 19, TailwindCSS, Framer Motion
├── docker/                          # Infrastructure provisioning configs
├── docs/                            # Whitepapers & Architecture reports
├── .github/workflows/               # CI/CD: pull-request, push-main, release
└── docker-compose.yml               # Multi-service production stack
```

---

## 7. Quick Start Guide

### Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose v2.20+
- [Node.js](https://nodejs.org/) v20+ & [Python](https://www.python.org/) 3.12+ (for local native development)

### 7.1 Single-Command Docker Deployment (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP

# 2. Configure Environment Variables
cp backend/.env.example backend/.env
cp .env.example frontend/.env.local

# 3. Start the entire container stack
docker compose up -d --build

# 4. Verify deployment health
curl http://localhost:8000/health
```

- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`
- **PostgreSQL**: `localhost:5432` | **Redis**: `localhost:6379` | **Qdrant**: `localhost:6333`

---

### 7.2 Native Development Setup

<details>
<summary><b>Backend Setup (FastAPI)</b></summary>

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run database migrations
python -m alembic upgrade head

# Start FastAPI development server
uvicorn src.main:app --reload --port 8000
```
</details>

<details>
<summary><b>Frontend Setup (Next.js 15)</b></summary>

```bash
cd frontend
npm install

# Verify type safety and code quality
npm run typecheck
npm run lint

# Start Next.js development server
npm run dev
```
</details>

---

## 8. Environment Variables Reference

| Variable | Scope | Description | Default |
|---|---|---|---|
| `POSTGRES_DB_URI` | Backend | Async PostgreSQL connection string | `postgresql+asyncpg://asep:changeme@localhost:5432/asep` |
| `REDIS_URL` | Backend | Redis host URI for streams and cache | `redis://localhost:6379/0` |
| `QDRANT_HOST` | Backend | Qdrant vector database host | `localhost` |
| `NEO4J_URI` | Backend | Neo4j graph database URI | `bolt://localhost:7687` |
| `GEMINI_API_KEY` | Backend | Google Gemini LLM API key | `""` (Fallback to Ollama) |
| `OPENAI_API_KEY` | Backend | OpenAI GPT-4o API key | `""` (Fallback to Ollama) |
| `OLLAMA_BASE_URL`| Backend | Local Ollama endpoint | `http://localhost:11434` |
| `JWT_SECRET_KEY` | Backend | Cryptographic secret for auth tokens | Auto-generated in production |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend API endpoint | `http://localhost:8000` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Frontend | Cloudflare Turnstile Captcha key | `1x00000000000000000000AA` (Test) |

---

## 9. Automated Testing & Verification Gates

```bash
# Run Backend Test Suite (Pytest + Asyncio)
cd backend
pytest -v --cov=src

# Run Frontend Quality Checks
cd frontend
npm run typecheck       # 0 errors
npm run lint            # 0 warnings
npm run build           # 38/38 static pages generated cleanly
```

---

## 10. Phased Engineering Roadmap

- [x] **Phase 1: Foundation & Core Stack** — Polyglot Next.js/FastAPI scaffold, PostgreSQL pool, Redis cache, JWT auth.
- [x] **Phase 2: Agent Execution & Sandboxing** — LangGraph DAG Planner, Docker isolation, Model Context Protocol (MCP).
- [x] **Phase 3: Multi-Tier Memory & Knowledge RAG** — Qdrant vector retrieval, Neo4j code AST graph persistence.
- [x] **Phase 4: Governance & Enterprise SaaS** — HITL resume-token approval engine, Razorpay checkout, 3D WebGL UI.
- [ ] **Phase 5: Cloud Ecosystem Integration** — GitHub Marketplace App bot, Helm charts for Kubernetes VPC deployment.

---

## 11. Contributing & Code of Conduct

Contributions are welcome! Please review [`docs/Development.md`](docs/Development.md) for coding standards, pull request protocols, and formatting guidelines.

```bash
# Verify all pre-commit hooks before opening a PR
pre-commit run --all-files
```

---

## 12. License & Authorship

- **Author**: Rounak Kumar Sah ([@rounakkumarsah](https://github.com/rounakkumarsah))
- **License**: [MIT License](LICENSE) — Free for open-source research, developer tooling, and enterprise modification.
