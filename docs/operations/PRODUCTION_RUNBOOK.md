# ASEP — Production Operations Runbook
**Document ID:** ASEP-OPS-DOC-001  
**Version:** 1.0 (Enterprise Standard)  
**Target Audience:** Site Reliability Engineers (SRE), Cloud Operations, Platform Engineers  
**Date:** August 24, 2026  

---

## 1. System Architecture & Component Ports

| Component | Container / Service | Port | Health Check Probe |
|---|---|---|---|
| **Frontend Web** | `asep-frontend` (Next.js) | `3000` | `GET http://localhost:3000/api/health` |
| **Backend API** | `asep-backend` (FastAPI) | `8000` | `GET http://localhost:8000/health` |
| **Readiness Probe** | `asep-backend` | `8000` | `GET http://localhost:8000/ready` |
| **Prometheus Metrics**| `asep-backend` | `8000` | `GET http://localhost:8000/metrics` |
| **PostgreSQL** | `asep-postgres` (Postgres 16) | `5432` | `pg_isready -U asep_user` |
| **Redis** | `asep-redis` (Redis 7) | `6379` | `redis-cli ping` |
| **Qdrant Vector DB** | `asep-qdrant` | `6333` | `GET http://localhost:6333/healthz` |
| **Neo4j Graph DB** | `asep-neo4j` | `7474` / `7687` | `GET http://localhost:7474` |

---

## 2. Day-1 Deployment & Initialization

### 2.1 One-Command Startup
```bash
# 1. Clone repository
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP

# 2. Configure environment variables
cp .env.example .env
# Edit .env with production credentials (JWT_SECRET_KEY, DATABASE_URL, etc.)

# 3. Launch full stack via Docker Compose
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify system readiness
curl -f http://localhost:8000/ready
```

### 2.2 Database Migrations Execution
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 3. Day-2 Routine Operations & Maintenance

### 3.1 Secret & JWT Key Rotation
1. Generate a new high-entropy 256-bit secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `JWT_SECRET_KEY` in production `.env` / AWS Secrets Manager.
3. Perform a zero-downtime rolling restart of backend worker containers:
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

### 3.2 Database Backup & Snapshot Automation
Nightly automated snapshot script:
```bash
# PostgreSQL Backup
docker exec asep-postgres pg_dump -U asep_user asep_db | gzip > /backups/postgres_$(date +%Y%m%d_%H%M%S).sql.gz

# Redis RDB Snapshot
docker exec asep-redis redis-cli BGSAVE

# Qdrant Snapshot
curl -X POST "http://localhost:6333/collections/asep_knowledge_base/snapshots"
```

---

## 4. Alert Triage & Troubleshooting Matrix

| Symptom / Alert | Probable Root Cause | Resolution Steps |
|---|---|---|
| `GET /ready` returns `503 Service Unavailable` | PostgreSQL, Redis, Qdrant, or Neo4j unreachable | Inspect container logs: `docker compose logs backend`. Check DB pool metrics and host firewalls. |
| Agent runs timing out at step execution | Container sandbox resource exhaustion or network block | Check `docker stats`. Verify Docker socket permissions and host CPU/RAM allocation. |
| Terminal WebSocket fails with code `4401` | Rate limit exceeded or invalid JWT token | Check client token expiry in cookies. Verify IP rate limit window in Redis (`rate_limit:terminal:<ip>`). |
| Database connection pool exhausted | High concurrent agent count (>100 active runs) | Increase `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW` in `.env`. Verify connections in Postgres: `SELECT count(*) FROM pg_stat_activity;`. |

---
*Maintained by ASEP Site Reliability Engineering.*
