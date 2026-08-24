# ASEP — Enterprise Threat Model & Trust Boundaries Specification
**Document ID:** ASEP-ARCH-DOC-002  
**Framework:** STRIDE & LINDDUN Security Threat Modeling  
**Version:** 1.0 (Institutional Due Diligence)  
**Author:** Principal Security Architect & CTO (Rounak Kumar Sah)  
**Date:** August 24, 2026  

---

## 1. System Trust Boundaries & Data Flow Overview

```
                      [ UNTRUSTED INTERNET / CLIENTS ]
                                     │
                             (TLS 1.3 / HTTPS)
                                     ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║ TRUST BOUNDARY 1: Edge & Ingress Perimeter                                  ║
║ - Cloudflare DDoS / Turnstile Bot Mitigation                                ║
║ - CORS Strict Origin Whitelist & Secure HttpOnly SameSite=Strict Cookies    ║
║ - Sliding-Window Rate Limiting (Redis-backed)                               ║
╚═════════════════════════════════════════════════════════════════════════════╝
                                     │
                          (Authenticated Requests)
                                     ▼
╔═════════════════════════════════════════════════════════════════════════════╗
║ TRUST BOUNDARY 2: Application Control Plane (FastAPI / Next.js)              ║
║ - JWT HS256 Token Validation & Scoped API Key Verification                  ║
║ - RBAC & Tenant Context Injection (`app.current_tenant`)                    ║
║ - LangGraph StateGraph Supervisor & Policy Engine                           ║
╚═════════════════════════════════════════════════════════════════════════════╝
             │                                              │
     (State / Vectors)                             (Container Execution)
             ▼                                              ▼
╔═════════════════════════════════╗    ╔═══════════════════════════════════════╗
║ TRUST BOUNDARY 3: Core Stores   ║    ║ TRUST BOUNDARY 4: Execution Sandbox   ║
║ - PostgreSQL 16 (Engine RLS)    ║    ║ - Non-Root Docker (`1000:1000`)       ║
║ - Redis 7 (TTL + Token Cache)   ║    ║ - Dropped Linux Capabilities (`ALL`)  ║
║ - Qdrant (Vector Isolation)     ║    ║ - Read-Only RootFS + Memory Cap (512M)║
║ - Neo4j (AST Knowledge Graph)   ║    ║ - PID Cap (100) + TempFS NoExec       ║
╚═════════════════════════════════╝    ╚═══════════════════════════════════════╝
```

---

## 2. STRIDE Threat Analysis Matrix

| Threat Category | Potential Attack Vector | ASEP Mitigation Strategy | Implementation Location |
|---|---|---|---|
| **Spoofing (S)** | Forged JWT access tokens or impersonated user requests | Cryptographic HMAC-SHA256 token verification with expiration validation; short-lived access tokens (30 min) + rotating refresh tokens. | `backend/src/auth/jwt.py` |
| **Tampering (T)** | Modification of Human-in-the-Loop (HITL) approval states | Cryptographic HMAC signature over approval payload (session ID, action, timestamp, approver UUID). | `backend/src/governance/hitl.py` |
| **Repudiation (R)** | User denies authorizing destructive code deployment | Immutable append-only audit log table recording Actor UUID, IP, Action, Resource, Outcome, and Timestamp. | `backend/src/services/audit_service.py` |
| **Information Disclosure (I)** | Cross-tenant data leakage in multi-tenant SaaS deployment | PostgreSQL engine-level Row-Level Security (RLS) policies enforcing `app.current_tenant` parameter separation. | `backend/alembic/versions/37c46316c0a8_enable_rls_multi_tenancy.py` |
| **Denial of Service (D)** | Prompt injection causing infinite agent loops or terminal fork bombs | Deterministic LangGraph StateGraph (capped at 10 steps); Circuit breakers; Linux `pids_limit=100` in container sandbox. | `backend/src/production/reliability.py`, `backend/src/tools/impl.py` |
| **Elevation of Privilege (E)** | Container breakout gaining root host access from generated code | Non-root container (`1000:1000`), `cap_drop=["ALL"]`, `security_opt=["no-new-privileges:true"]`, and read-only rootfs. | `backend/src/tools/impl.py` |

---

## 3. LINDDUN Privacy & Data Protection Analysis

* **Linkability:** Minimized by anonymizing telemetry identifiers and hashing IP addresses in audit logs after 90-day retention periods.
* **Identifiability:** All sensitive customer credentials (API keys, DB connection strings) are stored using AES-256 GCM encryption at rest.
* **Non-Repudiation vs Privacy:** Audit logs preserve necessary operational traceability without storing sensitive plaintext payloads.
* **Detectability:** Local-first Ollama runtime ensures sensitive source code never leaves the enterprise boundary or transits third-party AI APIs.
* **Disclosure:** Strictly zero telemetry transmission to external cloud servers when configured in sovereign on-premise mode.

---
*Reviewed and verified for enterprise compliance.*
