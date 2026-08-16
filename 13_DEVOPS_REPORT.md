# 13 — DevOps, Infrastructure & CI/CD Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and `.github/workflows/`.

---

## 1. Container Infrastructure (`docker-compose.yml`)

The multi-service production stack defines 5 container services:

1. **`asep-backend`** (`backend/Dockerfile`):
   - Multi-stage Python 3.12 build with security non-root user.
   - Startup command: `python -m alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000`.
   - Healthcheck probe checking `/health`.
2. **`asep-frontend`** (`frontend/Dockerfile`):
   - Multi-stage standalone Next.js 15 build on port 3000.
3. **`asep-postgres`**:
   - Image: `postgres:16-alpine`.
   - Healthcheck: `pg_isready -U asep -d asep`.
4. **`asep-redis`**:
   - Image: `redis:7-alpine` with AOF persistence.
   - Healthcheck: `redis-cli ping`.
5. **`asep-qdrant`**:
   - Image: `qdrant/qdrant:latest` for vector storage.

---

## 2. CI/CD GitHub Actions Workflows

Located in `.github/workflows/`:

1. **`pull-request.yml`**:
   - Triggers on PRs to `main`.
   - Runs Ruff, Black, MyPy type checks, pytest with real PostgreSQL/Redis/Qdrant service containers, ESLint, TypeScript check, and Next.js build validation.
2. **`push-main.yml`**:
   - Triggers on merges to `main`.
   - Validates build sanity and docker image building.
3. **`release-validation.yml`**:
   - Triggers on published GitHub releases.
