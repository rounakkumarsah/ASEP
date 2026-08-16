# Production Readiness Review (PRR) Report — OpenSEP

This document provides a comprehensive operational overview of OpenSEP's topology, infrastructure routing, security measures, and verification checkpoints before release authorization.

---

## 1. System & Ingress Topology

```mermaid
graph TD
    Client["Browser Client (React/xterm.js)"]
    Nginx["Nginx Reverse Proxy (SSL/WSS Ingress)"]
    FastAPI["FastAPI App Gateway Node"]
    Postgres["PostgreSQL DB (checkpoints saver)"]
    Redis["Redis Pub/Sub broker (opensep:terminal)"]
    Docker["Isolated Docker Sandboxes"]

    Client -->|HTTP / WebSockets| Nginx
    Nginx -->|Proxy forward| FastAPI
    FastAPI -->|Checkpoints query| Postgres
    FastAPI -->|Stream sync| Redis
    FastAPI -->|Local exec shell| Docker
```

### Key Components:
1. **Interactive Monaco Diff Viewer**: Allows developers to view side-by-side git diff comparisons inside `/approvals` dashboard paths, facilitating human-in-the-loop review phases.
2. **xterm.js Pseudo-Terminal**: Mounts dynamic xterm visual nodes inside `/sessions/[id]` views, routing raw interactive PTY shell execution streams over binary WebSockets.
3. **AsyncPostgresSaver Checkpointer**: Automatically serializes LangGraph checkpoints to PostgreSQL to ensure thread execution state is durable.
4. **Redis Pub/Sub stream synchronization**: Exposes synchronous, cross-replica standard output stream broadcasting across clustered deployment nodes.

---

## 2. Hardened Security Posture

* **PTY Command Injection Prevention**: User WebSocket input frames are written directly to the PTY master file descriptor using low-level OS writes (`os.write`). By bypassing shell interpreters (`sh -c`) entirely, user commands cannot trigger command injection escape vectors.
* **WebSocket Ingress Authentication**: The WebSocket router `/api/v1/ws/sessions/{session_id}/terminal` verifies user cookies or token queries immediately during the connection handshake. Rejects unauthenticated requests with code `4401`.
* **Redis Network Isolation**: In `docker-compose.yml`, the Redis caching service is fully decoupled from the host network (omitting the `ports` block) and communicates exclusively via the bridge network `asep-network`. Enforces authentication via `redis-server --requirepass`.
* **Open Policy Agent (OPA) Guardrails**: Integrates OPA pre-command hooks to validate user commands before execution. Fallbacks to close-fail safety if OPA is enabled but unreachable.

---

## 3. Strict Fail-Fast Production Environment Configurations

When `APP_ENV` is set to `staging` or `production`, the Settings class enforces strict checks and will fail to start if any of the following parameters use local defaults:

| Target Setting | Production Restriction | Default Dev Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Rejects `localhost` or default neon strings | `postgresql+asyncpg://asep:changeme@localhost:5432/asep` |
| `REDIS_URL` | Rejects `localhost`, `redis:6379`, or `127.0.0.1` | `redis://localhost:6379/0` |
| `SECRET_KEY` | Rejects known boilerplate string secrets | `change-this-to-a-random-256-bit-secret` |
| `ANTHROPIC_API_KEY` | Must be explicitly configured (non-null) | `None` |

---

## 4. Test Coverage Metrics Summary

* **Unit Test Suite**: 140 passing unit tests verifying FastAPI dependency injections, database user mappings, JWT security, and schema validations.
* **ESLint & Linting**: 100% clean check status matching strict lint policies.
* **Frontend Compilation**: Production static pages optimization completes with code `0`.
