# ASEP — Autonomous Software Engineering Platform

> **Phase 0.1 — Production Scaffold**
> The repository foundation is complete. Business logic begins in Phase 0.2.

---

## What is ASEP?

ASEP is a **Local-First AI Engineering Operating System** — a platform that runs autonomous software engineering agents on your own hardware, using local LLMs (via Ollama), with full observability, governance, and memory.

It is **not** a chatbot. It is **not** a demo. It is production-grade infrastructure for agentic software engineering.

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd ASEP

# 2. Bootstrap the dev environment
bash scripts/setup.sh

# 3. Start the full stack
make docker-up

# 4. Start the backend dev server
make dev

# 5. Open the API docs
open http://localhost:8000/docs
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

## Health Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness probe — process alive? |
| `GET /ready` | Readiness probe — all deps reachable? |
| `GET /docs` | Interactive API docs (dev only) |

---

## Roadmap

See [`docs/Roadmap.md`](docs/Roadmap.md) for the full phased plan.

---

## Contributing

See [`docs/Development.md`](docs/Development.md) for coding standards and contribution guidelines.

---

## License

Proprietary — All Rights Reserved.
