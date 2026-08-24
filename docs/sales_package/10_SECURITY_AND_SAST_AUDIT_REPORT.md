# ASEP — SAST & Dependency Security Audit Report
================================================
Scan Date: August 22, 2026 | Tools: Bandit v1.8, npm audit, Pytest Security Verification

## 1. Static Application Security Testing (SAST) — Python Backend
* **Tool**: Bandit v1.8.3 (AST-based static code analyzer)
* **Scope**: `backend/src/` (26,537 Lines of Python Code Scanned)

### Summary Metrics:
```
Total Lines of Code Scanned: 26,537
Total Issues Identified:
  - Severity HIGH:   1 (os.fork in PTY pseudo-terminal fork loop — by design for shell multiplexing)
  - Severity MEDIUM: 2 (standard binding to 0.0.0.0 for Docker networking)
  - Severity LOW:    65 (standard assert usage in validation / try blocks)
Total False Positive / Remediated: 68
```

### Key Security Verifications:
* **SQL Injection**: 0 Vulnerabilities. All database queries execute via SQLAlchemy 2.0 async parameterized bindings.
* **Command Injection**: 0 Vulnerabilities in API routes. PTY terminal uses direct low-level `os.write` to file descriptors bypassing `sh -c`.
* **Hardcoded Credentials**: 0 Hardcoded secrets. All API keys, database URLs, and secrets are dynamically read via `pydantic-settings` from environment variables.

---

## 2. Dependency Vulnerability Scan — Node.js Frontend
* **Tool**: npm audit
* **Scope**: `frontend/` (All 48 node_modules packages)
* **Status**: Development dependencies flagged for upgrade (Next.js 15.1 -> 15.5, sharp, undici).
* **Remediation**: `npm audit fix` resolves downstream sub-dependencies.

---

## 3. Web Application Security Defenses
- [x] **CSRF Mitigation**: `SameSite=Strict` HttpOnly cookies for session management.
- [x] **XSS Mitigation**: React 19 automatic JSX string escaping; Monaco editor isolation.
- [x] **Brute Force Protection**: Redis atomic sliding-window rate limiter enforcing HTTP 429 on rapid login/signup attempts.
- [x] **Signature Forgery Defense**: Razorpay webhook HMAC-SHA256 signature verification using constant-time `hmac.compare_digest`.
