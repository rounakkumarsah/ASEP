# ASEP — Autonomous Software Engineering Platform

> **Phase 0.1 — Production Scaffold**
> The repository foundation is complete. Business logic begins in Phase 0.2.

---

## What is ASEP?

ASEP is a **Local-First AI Engineering Operating System** — a platform that runs autonomous software engineering agents on your own hardware, using local LLMs (via Ollama), with full observability, governance, and memory.

It is **not** a chatbot. It is **not** a demo. It is production-grade infrastructure for agentic software engineering.

---

## Quick Start

### Production Topology (Docker)
ASEP uses a multi-stage Docker build for both backend and frontend, optimized for production security and footprint.

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd ASEP

# 2. Ensure environment variables are set
# (e.g., configure backend/.env and frontend/.env.local)

# 3. Build and Start the full production stack
docker compose up -d --build

# 4. Access the applications
# Frontend: http://localhost:3000
# Backend API Docs: http://localhost:8000/docs
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.12 · FastAPI · Uvicorn |
| Agent Runtime | LangGraph · LangChain |
| Data Validation | Pydantic v2 |
| ORM | SQLAlchemy 2 (async) |
| Primary DB | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Vector Store | Qdrant |
| Knowledge Graph | Neo4j 5 |
| Local LLM | Ollama |
| Frontend | Next.js · TypeScript · Tailwind · shadcn/ui |
| Infrastructure | Docker Compose |
| CI | GitHub Actions |
| Linting | Black · Ruff · MyPy · pre-commit |

---

## Repository Layout

```
ASEP/
├── backend/          Python API + Agent Runtime
├── frontend/         Next.js Dashboard
├── docker/           Infrastructure config files
├── docs/             Architecture & developer docs
├── scripts/          Developer utility scripts
├── benchmarks/       Performance benchmarks
└── .github/          CI/CD workflows
```

See [`docs/FolderStructure.md`](docs/FolderStructure.md) for the complete tree.

---

## Development Commands

```bash
make install      # Install all dependencies
make dev          # Start dev server with hot-reload
make test         # Run test suite
make lint         # Ruff linter
make format       # Black formatter
make typecheck    # MyPy type check
make check        # lint + typecheck + test (all-in-one)
make docker-up    # Start all Docker services
make docker-logs  # Tail backend logs
```

---

## CI/CD Pipeline

ASEP uses **GitHub Actions** for automated build validation, testing, code quality audits, and container checks. The pipeline is split into modular workflows under `.github/workflows/`:

1. **Pull Request Verification (`pull-request.yml`)**: Runs on PRs to `main`. Validates backend (Ruff, Black, MyPy, Pytest with PostgreSQL/Redis/Qdrant service containers) and frontend (ESLint, TypeScript, Vitest, Playwright E2E tests, Next.js build) alongside Docker builds.
2. **Push to Main Validation (`push-main.yml`)**: Runs on direct pushes or merges to `main`, validating code sanity.
3. **Release Validation (`release-validation.yml`)**: Runs automatically when a GitHub release is published.

### Pipeline Features

- **Caching**: Leverages actions caching for `pip` packages, `npm` node modules, and Playwright Chromium binaries to accelerate runtime validation.
- **Service Containers**: Bootstraps real Docker services (PostgreSQL 16, Redis 7, Qdrant) in the GitHub runner sandbox to run backend repository integration tests.
- **Fail-Safe Artifacts**: Automatically archives Playwright E2E test HTML reports and screenshots if integration tests fail.
- **Repository Secrets**:
  - `CODECOV_TOKEN` (optional): Upload coverage profiles safely without leakage.

---

## Health & Telemetry Endpoints

| Endpoint | Method | Description | Response Code |
|---|---|---|---|
| `/health` | `GET` | **Liveness Probe**: Confirms the service process is active. | `200 OK` |
| `/ready` | `GET` | **Readiness Probe**: Asynchronously queries database (PostgreSQL), cache (Redis), and vector store (Qdrant) latency. | `200 OK` / `503 Service Unavailable` |
| `/metrics` | `GET` | **Application Metrics**: Returns JSON telemetry. Returns Prometheus format if Accept header matches `text/plain`. | `200 OK` |
| `/diagnostics` | `GET` | **Diagnostics**: Exposes version, environment, runtime metadata, and system uptime. | `200 OK` |
| `/docs` | `GET` | **FastAPI Documentation**: Interactive endpoints overview (Development mode only). | `200 OK` |
| `/api/v1/ai/health` | `GET` | **AI Providers Health**: Exposes liveness, active model, latency, and circuit breaker status across AI engines. | `200 OK` |
| `/api/v1/ai/capabilities` | `GET` | **AI Capabilities Matrix**: Exposes support matrices for vision, tools, JSON mode, streaming, context limits. | `200 OK` |

---

## AI Runtime Abstraction Layer

ASEP features a unified, vendor-agnostic AI Runtime layer preventing business layers from importing vendor SDKs. It provides:
1. **Model Registry**: Dynamic priority-driven model mapping (Ollama -> Gemini -> OpenAI -> Mock).
2. **Circuit Breakers**: Individual CLOSED/OPEN/HALF-OPEN breaker state tracking protecting against repeated provider timeout failures.
3. **Context Management**: Token budgeting, message history trimming, system prompt injection, and context compression hooks.
4. **Normalized Usage**: Consistent cost, prompt/completion/reasoning token counts, and execution latency tracking.

## Human-in-the-Loop (HITL) Framework

ASEP integrates an enterprise-grade Human-in-the-Loop (HITL) system to govern critical, sensitive, or high-risk tool operations.
1. **Configurable Policies**: Defines granular risk assessments mapping tool execution to risk levels (`Low`, `Medium`, `High`, `Critical`).
2. **Review Sessions**: Pauses high-risk operations (e.g., executing commands, modifying configurations, writing filesystem blocks) to spawn an audit-ready `ReviewSession` containing full execution context.
3. **Escalations & Timeouts**: Implements SLA alerts tracking approval latency, automatic session expiration, and reviewer escalation paths.
4. **Dashboard Queue Integration**: Exposes REST interfaces at `/api/v1/governance/hitl` allowing real-time dashboard reviews, decision overrides, argument modification, and secure resumed execution.

---

## Roadmap

See [`docs/Roadmap.md`](docs/Roadmap.md) for the full phased plan.

---

## Contributing

See [`docs/Development.md`](docs/Development.md) for coding standards and contribution guidelines.

---

## License

Proprietary — All Rights Reserved.
