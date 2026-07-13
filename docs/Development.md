# ASEP — Development Guide

---

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Python | 3.12 | [python.org](https://python.org) |
| Docker | 24.0 | [docker.com](https://docker.com) |
| Docker Compose | v2 | (included with Docker Desktop) |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |
| Git | 2.40 | system package |
| Make | any | system package |

---

## First-Time Setup

```bash
git clone <repo-url>
cd ASEP
bash scripts/setup.sh
```

This script:
1. Copies `.env.example` → `.env`
2. Installs backend Python deps in editable mode
3. Installs pre-commit hooks
4. Installs frontend npm packages
5. Pulls all Docker images

---

## Daily Development Loop

```bash
# Start all backing services
make docker-up

# Start backend with hot-reload (in a separate terminal)
make dev

# Run tests on every change
make test

# Check everything before committing
make check
```

---

## Code Standards

### Python

- **Formatter**: `black` (line length 100)
- **Linter**: `ruff` (E, W, F, I, B, C4, UP, N, SIM rules)
- **Type checker**: `mypy --strict`
- **Docstrings**: Google style
- **Imports**: absolute paths only (`from src.config.settings import ...`)

### TypeScript (Frontend)

- **Formatter**: Prettier
- **Linter**: ESLint (Next.js ruleset)
- **Strict mode**: enabled in `tsconfig.json`

### General

- No `print()` in production code — use `logging` / `structlog`
- Every public function must have a docstring
- Every module must have a module-level docstring
- Every new module must include `TODO` markers for future implementation

---

## Adding a New API Route

1. Create `backend/src/api/routers/<domain>.py`
2. Define a `router = APIRouter(prefix="/api/v1/<domain>")`
3. Register it in `backend/src/api/app.py` under `# Routers`
4. Add tests in `backend/tests/test_<domain>.py`

---

## Adding a New Database Model

1. Create the model in `backend/src/db/models/<name>.py` (inherit from `Base`)
2. Import it in `backend/src/db/models/__init__.py`
3. Generate a migration: `make migrate-create name=<description>`
4. Apply: `make migrate`

---

## Adding a New Agent

1. Implement the agent class in `backend/src/agents/<name>.py`
2. Register it with `@register_agent("<name>")` from `src/agents/registry.py`
3. Add it to the supervisor routing logic
4. Write tests in `backend/tests/agents/test_<name>.py`

---

## Git Workflow

```
main          ← production-ready (protected)
└── dev       ← integration branch
    └── feat/<ticket>-<description>   ← feature branches
    └── fix/<ticket>-<description>    ← bug fix branches
    └── chore/<description>           ← maintenance branches
```

- All PRs target `dev`
- `dev` → `main` merges require passing CI + code review
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)

### Commit Format

```
<type>(<scope>): <description>

feat(agents): add code writer agent
fix(health): correct uptime calculation
chore(deps): bump fastapi to 0.115.0
docs(readme): update quick start instructions
```

---

## Environment Variables

All variables are documented in [`.env.example`](../.env.example).

> ⚠️ Never commit a real `.env` file. It is in `.gitignore`.

---

## Running Tests

```bash
# All tests
make test

# Single file
cd backend && pytest tests/test_health.py -v

# With coverage report
cd backend && pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Docker Services

| Service | URL | Credentials |
|---|---|---|
| FastAPI | http://localhost:8000 | — |
| API Docs | http://localhost:8000/docs | — |
| Frontend | http://localhost:3000 | — |
| PostgreSQL | localhost:5432 | asep / changeme |
| Redis | localhost:6379 | no auth (dev) |
| Neo4j Browser | http://localhost:7474 | neo4j / changeme |
| Qdrant | http://localhost:6333 | — |
| Ollama | http://localhost:11434 | — |
