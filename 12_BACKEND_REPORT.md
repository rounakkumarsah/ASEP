# 12 — Backend Architecture & Service Layer Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/api/`, `backend/src/services/`, `backend/src/repositories/`, and `backend/src/unit_of_work/`.

---

## 1. Application Factory & Lifecycle Architecture

Implemented in `backend/src/api/app.py` (`create_app()`).

- **Lifespan Manager**: Handles non-blocking asynchronous startup of PostgreSQL pool, Redis client, Neo4j driver, and Qdrant vector client with graceful degradation if auxiliary vector/graph stores are offline during initial boot.
- **Error Tracking**: Sentry SDK integration with FastAPI middleware (`sentry_sdk.init()`).
- **Structured Logging**: `StructuredLoggingMiddleware` converting request/response traces into structured JSON logs.

---

## 2. Layered Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    API Routers (21 Routers)                 │
├─────────────────────────────────────────────────────────────┤
│                 Business Services & Runtimes                │
├─────────────────────────────────────────────────────────────┤
│                 Unit of Work & Repositories                 │
├─────────────────────────────────────────────────────────────┤
│             SQLAlchemy 2.0 Async ORM / Databases            │
└─────────────────────────────────────────────────────────────┘
```

1. **Repositories** (`backend/src/repositories/`):
   - `user.py`, `agent_run.py`, `task.py`, `knowledge_document.py`, `memory_entry.py`, `audit_log.py`.
2. **Unit of Work** (`backend/src/unit_of_work/`):
   - `sqlalchemy.py` managing atomic transactions and rollback safety.
3. **Services** (`backend/src/services/`):
   - Decoupled business logic for auth, agents, knowledge synchronization, memory compaction, and Razorpay payments.
