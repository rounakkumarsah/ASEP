# 10 — Security & Compliance Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/auth/`, `backend/src/api/middleware/`, `backend/src/db/models/audit_log.py`, and `backend/src/executor/sandbox.py`.

---

## 1. Perimeter Security & HTTP Headers

Implemented in `backend/src/api/app.py` (Lines 202–234).

- **Content-Security-Policy (CSP)**: Restricts script, frame, and connect sources to self, Cloudflare Turnstile, and Razorpay endpoints.
- **HTTP Strict Transport Security (HSTS)**: `max-age=31536000; includeSubDomains; preload`.
- **Frame & Content Protection**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.
- **Permissions Policy**: `camera=(), microphone=(), geolocation=()`.

---

## 2. Authentication & Bot Protection

- **Password Hashing**: `backend/src/auth/password.py` using Argon2 / Bcrypt with unique salts.
- **Session Tokens**: JWT signed with secret keys, stored in httpOnly secure cookies.
- **Bot Mitigation**: Cloudflare Turnstile captcha validation on registration and login routes.

---

## 3. Sandboxed Execution Isolation

- **Docker Containers**: `backend/src/executor/docker.py` executes commands inside non-root, ephemeral Docker containers with strict memory/CPU limits and no access to host filesystem paths.

---

## 4. Immutable Structured Audit Logging

- **`AuditLog` Model**: `backend/src/db/models/audit_log.py` captures user UUID, IP address, user-agent, action type, resource UUID, and complete JSONB state snapshots.
- **Audit Router**: `backend/src/api/routers/audit.py` with timestamp pagination and security filters.
