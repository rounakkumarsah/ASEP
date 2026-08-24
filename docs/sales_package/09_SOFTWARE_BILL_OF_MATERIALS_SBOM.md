# ASEP — Software Bill of Materials (SBOM)
=========================================
Standard: SPDX / CycloneDX Comprehensive Component Inventory
Version: 1.0.0 | Date: August 2026

## 1. Top-Level Application Metadata
* **Package Name**: `asep-platform`
* **Version**: `0.1.0`
* **Supplier**: Rounak Kumar Sah
* **Primary License**: `MIT`
* **Repository**: `https://github.com/rounakkumarsah/ASEP.git`

---

## 2. Backend Component Inventory (Python 3.12)

| Component Name | Version | License | Ecosystem | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `fastapi` | `>=0.115.0` | MIT | PyPI | Async ASGI Web Framework |
| `uvicorn` | `>=0.32.0` | BSD-3-Clause | PyPI | High-performance ASGI Web Server |
| `sqlalchemy` | `>=2.0.36` | MIT | PyPI | SQL Database ORM & Connection Pool |
| `asyncpg` | `>=0.30.0` | Apache-2.0 | PyPI | PostgreSQL Async Native Driver |
| `alembic` | `>=1.14.0` | MIT | PyPI | Database Schema Migrations |
| `pydantic` | `>=2.10.0` | MIT | PyPI | Data Validation & Settings Parsing |
| `redis` | `>=5.2.0` | MIT | PyPI | In-Memory Cache, Pub/Sub, Rate Limiting |
| `structlog` | `>=24.4.0` | MIT / Apache-2.0 | PyPI | Structured JSON Application Logging |
| `PyJWT` | `>=2.8.0` | MIT | PyPI | JSON Web Token Encoding / Decoding |
| `argon2-cffi` | `>=23.1.0` | MIT | PyPI | Password Hashing (Argon2id) |
| `razorpay` | `>=2.0.1` | MIT | PyPI | Payment Gateway Client & HMAC Verification |
| `sentry-sdk` | `>=2.0.0` | MIT / BSD | PyPI | Application Error Tracing |
| `resend` | `>=2.0.0` | MIT | PyPI | Transactional Email Dispatcher |
| `cloudinary` | `>=1.41.0` | MIT | PyPI | Media & Cloud Storage Management |
| `langgraph` | `>=0.2.0` | MIT | PyPI | Multi-Agent Execution StateGraph DAGs |
| `tenacity` | `>=9.0.0` | Apache-2.0 | PyPI | Retry & Backoff Resilience |
| `orjson` | `>=3.10.0` | Apache-2.0 / MIT | PyPI | Fast JSON Serialization |

---

## 3. Frontend Component Inventory (Node.js / React 19)

| Component Name | Version | License | Ecosystem | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `next` | `15.1.0` | MIT | npm | React App Router Framework |
| `react` | `^19.0.0` | MIT | npm | UI Library |
| `react-dom` | `^19.0.0` | MIT | npm | DOM Renderer |
| `@xterm/xterm` | `^6.0.0` | MIT | npm | Interactive Web Terminal Emulator |
| `@monaco-editor/react` | `^4.7.0` | MIT | npm | Monaco Code & Diff Editor |
| `tailwindcss` | `^3.4.17` | MIT | npm | Utility-First CSS Engine |
| `framer-motion` | `^12.42.2` | MIT | npm | Fluid UI Animations |
| `lucide-react` | `^0.469.0` | ISC | npm | Vector Icon Library |
| `@tanstack/react-query` | `^5.101.2` | MIT | npm | Server State Caching & Synchronization |
| `zod` | `^4.4.3` | MIT | npm | Client-Side Schema Validation |
| `react-hook-form` | `^7.81.0` | MIT | npm | Form State Management |
| `posthog-js` | `^1.110.0` | MIT | npm | Product Analytics & Telemetry |

---

## 4. License Compliance Summary
* **Total Audited Components**: 29 Direct Dependencies.
* **Permissive Licenses**: 100% (MIT, Apache-2.0, BSD, ISC).
* **Copyleft (GPL / AGPL / SSPL)**: 0%.
