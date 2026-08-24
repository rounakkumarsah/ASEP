# ASEP — Security Audit Checklist & Hardening Report
===================================================

## 1. Authentication & Session Security
- [x] **Argon2id Password Hashing**: Passwords hashed with high-memory parameters; raw passwords never persisted.
- [x] **JWT Token Separation**: Short-lived Access Tokens (30m) paired with long-lived Refresh Tokens (7d).
- [x] **HttpOnly & SameSite=Strict Cookies**: Session tokens stored in protected cookies inaccessible to JavaScript (XSS mitigation).
- [x] **Multi-Factor Authentication (MFA)**: RFC 6238 TOTP authenticator integration with encrypted recovery codes.
- [x] **Sliding-Window Rate Limiter**: Redis-backed atomic limiter enforcing IP and account-level brute force limits (HTTP 429).
- [x] **Email Normalization**: RFC-compliant sanitization and Gmail alias normalization preventing multi-account exploits.

## 2. API & Injection Defense
- [x] **PTY Low-Level OS Execution**: Terminal processes use `os.write` to master file descriptors, bypassing shell interpreter command injection vulnerabilities.
- [x] **Open Policy Agent (OPA) Guardrails**: Intercepts and denies unauthorized terminal command patterns before execution.
- [x] **SQL Injection Defense**: 100% parameterized queries via SQLAlchemy 2.0 async ORM and asyncpg driver.
- [x] **Razorpay Webhook Verification**: Constant-time `hmac.compare_digest` HMAC-SHA256 signature verification.
- [x] **Bot Defense**: Cloudflare Turnstile token validation on registration endpoints.

## 3. Data Protection & Privacy
- [x] **Zero Code Leakage**: Sovereign execution model allows air-gapped local model (Ollama) routing.
- [x] **Fail-Fast Cloud Storage**: Mock URL fallbacks removed; file uploads require verified storage keys.
- [x] **Audit Trail**: Security-critical actions logged to an append-only `audit_logs` database table.
