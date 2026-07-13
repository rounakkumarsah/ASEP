# ASEP — Folder Structure

> Complete annotated directory tree for ASEP v0.1.0

```
ASEP/
│
├── .github/
│   └── workflows/
│       └── ci.yml              ← GitHub Actions: lint + test + docker build
│
├── backend/                    ← Python 3.12 service (FastAPI + LangGraph)
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py             ← Uvicorn entry point
│   │   │
│   │   ├── api/                ← HTTP interface layer
│   │   │   ├── app.py          ← FastAPI application factory + lifespan
│   │   │   └── routers/
│   │   │       └── health.py   ← GET /health, GET /ready
│   │   │
│   │   ├── agents/             ← LangGraph agent runtime
│   │   │   ├── state.py        ← Shared AgentState schema (Pydantic)
│   │   │   ├── planner.py      ← Planner node (goal → plan[])
│   │   │   ├── supervisor.py   ← Supervisor node + graph builder
│   │   │   ├── registry.py     ← Agent factory registry
│   │   │   └── checkpoint.py   ← LangGraph checkpointer manager
│   │   │
│   │   ├── runtime/
│   │   │   └── execution/
│   │   │       └── engine.py   ← Run lifecycle (submit / cancel / status)
│   │   │
│   │   ├── memory/
│   │   │   └── service.py      ← Memory read/write/search facade
│   │   │
│   │   ├── knowledge/
│   │   │   └── service.py      ← Code graph ingestion + search
│   │   │
│   │   ├── governance/
│   │   │   └── service.py      ← Policy enforcement + audit logging
│   │   │
│   │   ├── db/                 ← Database connection managers
│   │   │   ├── postgres.py     ← SQLAlchemy async engine + session DI
│   │   │   ├── redis.py        ← Redis async client DI
│   │   │   ├── neo4j.py        ← Neo4j async driver DI
│   │   │   ├── qdrant.py       ← Qdrant async client DI
│   │   │   ├── models/         ← SQLAlchemy ORM model definitions (TODO)
│   │   │   └── services/       ← DB-layer service classes (TODO)
│   │   │
│   │   ├── tools/              ← Agent tool definitions (TODO)
│   │   ├── evaluation/         ← Eval harness (TODO)
│   │   ├── replay/             ← Trace replay engine (TODO)
│   │   │
│   │   ├── config/
│   │   │   └── settings.py     ← Pydantic v2 Settings + env loading
│   │   │
│   │   └── utils/
│   │       └── logging.py      ← structlog configuration
│   │
│   ├── tests/
│   │   ├── conftest.py         ← Pytest fixtures (app, client, async_client)
│   │   └── test_health.py      ← Passing sample tests (health + ready)
│   │
│   ├── Dockerfile              ← Multi-stage production Docker image
│   └── pyproject.toml          ← Dependencies + Black/Ruff/MyPy/Pytest config
│
├── frontend/                   ← Next.js dashboard (scaffold only)
│   ├── src/app/                ← App Router pages
│   ├── public/                 ← Static assets
│   ├── Dockerfile              ← Frontend Docker image
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.ts
│
├── docker/
│   └── postgres/
│       └── init.sql            ← PostgreSQL init script (extensions)
│
├── docs/
│   ├── Architecture.md         ← System architecture + data flow
│   ├── FolderStructure.md      ← This file
│   ├── Roadmap.md              ← Phased delivery plan
│   └── Development.md          ← Dev standards + contribution guide
│
├── scripts/
│   └── setup.sh                ← Bootstrap dev environment
│
├── benchmarks/
│   └── __init__.py             ← Performance benchmark placeholder
│
├── docker-compose.yml          ← Full local stack (6 services)
├── .env.example                ← Environment variable template
├── .gitignore
├── .pre-commit-config.yaml     ← Black + Ruff + MyPy + secret detection
├── Makefile                    ← Developer shortcuts
└── README.md                   ← Project overview + quick start
```

---

## Package Responsibility Matrix

| Package | Responsibility | Can Import |
|---|---|---|
| `api/` | HTTP interface, request/response schemas | `agents/`, `config/`, `utils/` |
| `agents/` | LangGraph nodes, state, registry | `config/`, `utils/`, `db/` |
| `runtime/` | Run lifecycle management | `agents/`, `db/`, `config/` |
| `memory/` | Memory read/write/search | `db/`, `config/` |
| `knowledge/` | Code graph ingestion + search | `db/`, `config/` |
| `governance/` | Policy evaluation + audit | `db/`, `config/` |
| `tools/` | Agent tool implementations | `config/`, `utils/` |
| `evaluation/` | Benchmark harness | `agents/`, `runtime/` |
| `replay/` | Trace serialisation + replay | `agents/`, `db/` |
| `db/` | Database connection managers | `config/` only |
| `config/` | Settings loading | nothing |
| `utils/` | Shared utilities (logging etc.) | `config/` |
