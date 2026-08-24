# ASEP — API Documentation & Route Catalog
==========================================

The platform exposes **97+ secure REST and WebSocket endpoints** organized across 15 modular FastAPI routers:

## Core Router Overview

| Router Prefix | Tag | Description | Key Endpoints |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth` | Authentication | Identity, JWTs, MFA, Session Management | `POST /signup`, `POST /login`, `POST /mfa/setup`, `POST /mfa/enable`, `POST /logout` |
| `/api/v1/users` | Users | Profile, Quotas, Username Checks | `GET /me`, `PATCH /profile`, `GET /quota`, `GET /check-username` |
| `/api/v1/payments` | Payments | Razorpay Orders, Verification, Webhooks | `POST /create-order`, `POST /verify`, `POST /webhook`, `GET /history` |
| `/api/v1/conversations`| Conversations | Agent Sessions & Task Runs | `POST /run`, `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}` |
| `/api/v1/terminal` | Terminal | PTY Shell Session & WebSocket Streaming | `GET /sessions/{id}/ws`, `POST /sessions/{id}/resize`, `POST /sessions/{id}/kill` |
| `/api/v1/hitl` | Human-In-The-Loop | Review & Approval Gates | `GET /pending`, `POST /approve/{id}`, `POST /reject/{id}` |
| `/api/v1/knowledge` | Knowledge Base | Document Indexing & Crawlers | `POST /upload`, `POST /crawl`, `GET /documents`, `DELETE /documents/{id}` |
| `/api/v1/rag` | RAG Engine | Vector & Graph Search Queries | `POST /search/vector`, `POST /search/graph`, `POST /search/hybrid` |
| `/api/v1/organizations`| Organizations | Multi-Tenancy & Teams | `GET /`, `POST /`, `POST /members/invite`, `DELETE /members/{id}` |
| `/api/v1/api-keys` | API Keys | Programmatic Access Management | `GET /`, `POST /generate`, `DELETE /{id}` |
| `/api/v1/audit` | Audit Logs | Security & System Action Trails | `GET /events`, `GET /events/user/{id}`, `GET /events/export` |
| `/api/v1/health` | Health & Status | Service & Dependency Diagnostics | `GET /health`, `GET /ready`, `GET /metrics` |

## Interactive Documentation
When running the backend, visit:
* **Swagger UI**: `http://localhost:8000/docs`
* **ReDoc**: `http://localhost:8000/redoc`
* **OpenAPI JSON Schema**: `http://localhost:8000/openapi.json`
