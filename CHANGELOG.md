# Changelog

All notable changes to ASEP are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- VS Code extension integration
- OpenTelemetry distributed tracing
- LangGraph supervisor agent registry
- Automated PR submission to GitHub/GitLab

---

## [0.1.5] - 2026-08-24

### Added
- **M&A Due Diligence Data Room**: Published master Data Room Index (`docs/DATA_ROOM_INDEX.md`), Investment Memorandum (`docs/sales_package/17_EXECUTIVE_SUMMARY_AND_INVESTMENT_MEMORANDUM.md`), Buyer Due Diligence FAQ (`docs/sales_package/18_BUYER_DUE_DILIGENCE_FAQ_AND_OBJECTIONS.md`), and Asset Inventory & Transfer Checklist (`docs/sales_package/19_ASSET_INVENTORY_AND_TRANSFER_CHECKLIST.md`).
- **Reproducible Benchmark Suite**: Implemented `scripts/benchmark_suite.py` measuring latency, token consumption, multi-model cost modeling ($/1,000 tasks), and task success rates. Generated empirical benchmark reports (`docs/sales_package/20_TECHNICAL_BENCHMARK_REPORT.md` and `docs/benchmarks/`).
- **Architecture Decision Records (ADRs)**: Created 5 formal ADRs (`docs/adr/0001` to `0005`) documenting decisions on LangGraph orchestration, 4-tier hybrid memory, hardened container sandboxes, PostgreSQL Row-Level Security, and Redis distributed PTY state.
- **Enterprise Security & Architecture Specifications**: Published STRIDE/LINDDUN Threat Model (`docs/architecture/ENTERPRISE_THREAT_MODEL_AND_TRUST_BOUNDARIES.md`) and Mermaid System Sequence / Data Flow Specification (`docs/architecture/SYSTEM_SEQUENCE_AND_DATA_FLOW_SPEC.md`).
- **Operational Excellence Suite**: Authored Production Runbook (`docs/operations/PRODUCTION_RUNBOOK.md`), Incident Response Plan (`docs/operations/INCIDENT_RESPONSE_PLAN.md`), Capacity Planning & Scaling Guide (`docs/operations/CAPACITY_PLANNING_AND_SCALING_GUIDE.md`), and SLO/SLA Specification (`docs/operations/SLO_SLA_SPECIFICATION.md`).
- **Commercial & Financial Models**: Added Commercial Valuation & ROI Model (`docs/sales_package/21_COMMERCIAL_VALUATION_AND_ROI_MODEL.md`), "Why Buy Instead of Build" Strategic Dossier (`docs/sales_package/22_WHY_BUY_INSTEAD_OF_BUILD.md`), and 40-Point Competitive Capability Matrix (`docs/sales_package/23_ENTERPRISE_COMPETITIVE_MATRIX.md`).
- **Developer Workflows & Demos**: Added runnable automated security patch workflow (`examples/demo_workflows/01_automated_security_patch_workflow.py`), Prompt Engineering Catalog (`examples/prompt_catalog/PROMPT_ENGINEERING_CATALOG.md`), and full-stack Enterprise Docker Compose stack with Prometheus (`examples/enterprise_deployment/`).

---

## [0.1.4] - 2026-08-24

### Security
- **Next.js Security Hardening**: Updated Next.js to the latest stable release (15.5.23) and `eslint-config-next` to match. This upgrade incorporates security fixes, bug fixes, and framework improvements released after multiple Next.js security advisories, including middleware authorization bypass, App Router security fixes, React Flight protocol fixes, and other patched vulnerabilities affecting earlier Next.js 15.x releases. The project now targets the latest maintained stable release to minimize known security risks and simplify future dependency management.
- **PostgreSQL Row-Level Security (RLS)**: Enforced tenant isolation dynamically across the database via Alembic migrations, dropping application-layer trust requirements for data separation.
- **Docker Sandbox Hardening**: Modified execution engine to use strictly unprivileged `user="1000:1000"`, dropped all kernel capabilities (`cap_drop=["ALL"]`), mounted root filesystems as read-only with a secure `tmpfs`, and enforced `pids_limit=100` to prevent fork bombs and container escapes.

### Fixed
- **Multi-Pod Terminal Concurrency**: Migrated the PTY terminal concurrent session tracker (`CONCURRENT_SESSIONS`) from a localized in-memory Python `set` to a distributed Redis store using `redis_client.sadd/srem/scard`, solving global cap enforcement limits across horizontally scaled pods.
- **LangGraph Agent State & Memory Pipeline**: Resolved critical Phase 0.2 `TODO` comments. Refactored the `AgentState` schema from an immutable `pydantic.BaseModel` to an official LangGraph `TypedDict`, fully implementing the `MemoryContext`, `CostTracker`, and `ToolCall` reducers. 
- **Graph Compilation Stubs**: Removed the mocked `build_supervisor_graph()` throwing `NotImplementedError`, replacing it with a fully compiled `langgraph.graph.StateGraph` including edge routing, conditional state checks, and an integration-ready `executor_node`.
- **API Runtime Crashes**: Addressed structural `mypy` violations across the entire `src/agent` architecture. Replaced defunct `self._memory.episodic.record` invocation attempts with `add_episode` ensuring functional integration with the UUID memory pipeline. Fixed CacheService type definition bugs.

---

## [0.1.3] — 2026-08-23

### Security
- **FIXED**: Removed admin rate-limit bypass in `backend/src/api/routers/auth.py` (L172–178) — admin users were previously exempt from failed-login rate limits
- **FIXED**: Rate limiter TTL bug in `backend/src/auth/rate_limit.py` — `expire()` was called on every attempt instead of only when `count == 1`; confirmed HTTP 429 on attempt 6
- **FIXED**: Login crash caused by timezone-aware vs timezone-naive `datetime` mismatch — `backend/src/auth/service.py` now uses `datetime.utcnow()` consistently

### Added
- `POST /api/v1/auth/e2e/seed-user` endpoint for Playwright E2E test isolation (returns HTTP 201)
- `backend/tests/unit/api/test_auth_production_hardening.py` — 6 unit tests covering rate limiter and email normalization (100% pass)
- `frontend/src/app/terms/page.tsx` — comprehensive 8-section enterprise Terms of Service
- `frontend/src/app/privacy/page.tsx` — comprehensive 7-section GDPR/CCPA Privacy Policy
- `SECURITY.md` at repository root — vulnerability disclosure policy and SLA
- `docs/sales_package/` directory — full 14-document commercial sales package

### Changed
- `frontend/e2e/auth.setup.ts` rewritten to use seed endpoint instead of UI-based user creation
- `frontend/e2e/auth.spec.ts` and `core.spec.ts` updated to use E2E test credentials
- `backend/src/agents/planner.py` — stub replaced with real LLM goal decomposition via `AIRuntimeService`
- `backend/src/production/cloudinary_service.py` — fake URL fallback replaced with `RuntimeError` when `CLOUDINARY_URL` is unconfigured

---

## [0.1.2] — 2026-08-22

### Added
- Database migration `e7e1187405a7_add_mfa_and_saas_user_fields.py` at HEAD
- 25 user columns confirmed in Neon PostgreSQL: MFA fields, subscription fields, lockout fields
- Production readiness audit report (`docs/PRR_REPORT.md`)
- `docs/sales_package/01_TECHNICAL_ARCHITECTURE.md` — system architecture documentation
- `docs/sales_package/02_INSTALLATION_AND_DEPLOYMENT_GUIDE.md`
- `docs/sales_package/03_LICENSE_AND_COMPLIANCE_REPORT.md`
- `docs/sales_package/04_TEST_AND_QUALITY_ASSURANCE_REPORT.md`
- `docs/sales_package/05_SECURITY_AUDIT_CHECKLIST.md`
- `docs/sales_package/06_COMPLETE_FEATURE_SPECIFICATION.md`
- `docs/sales_package/07_API_DOCUMENTATION_CATALOG.md` — 97 unique URL paths, 111 HTTP operations
- `docs/sales_package/08_DEMO_VIDEO_SCRIPT_AND_STORYBOARD.md`
- `docs/sales_package/09_SOFTWARE_BILL_OF_MATERIALS_SBOM.md`
- `docs/sales_package/10_SECURITY_AND_SAST_AUDIT_REPORT.md` — Bandit scan: 1 HIGH, 2 MEDIUM, 65 LOW
- `docs/sales_package/11_IP_OWNERSHIP_AND_BILL_OF_SALE_DECLARATION.md`
- `docs/sales_package/12_INFRASTRUCTURE_COST_MODEL_AND_UNIT_ECONOMICS.md`
- `docs/sales_package/13_ASSET_PURCHASE_AGREEMENT_DRAFT.md` — APA legal draft
- `docs/sales_package/14_INSTITUTIONAL_MA_MARKET_RESEARCH_REPORT.md` — 44-source M&A report

### Security
- Bandit SAST scan completed: 0 SQL injection, 0 command injection, 0 CRITICAL findings
- npm audit raw output archived at `docs/sales_package/npm_audit.json`

---

## [0.1.1] — 2026-08-18

### Added
- `backend/src/governance/policy_engine.py` — Policy Governance Engine with RBAC decision logic
- `backend/src/agents/` — LangGraph multi-agent state machine with Planner, Supervisor, Worker, Evaluator agents
- `backend/src/memory/` — Three-tier memory system: Redis (working), Qdrant (episodic), Neo4j+Qdrant (semantic)
- `backend/src/api/routers/terminal.py` — Full PTY terminal via `xterm.js`; WebSocket streaming; Docker sandbox management
- Cloudflare Turnstile bot protection on all public auth endpoints
- GitHub OAuth and Google OAuth social login flows
- Multi-Factor Authentication (TOTP) with QR code provisioning and backup codes
- PostHog analytics integration
- Sentry error tracking integration
- Razorpay payment gateway integration with webhook signature verification

### Changed
- Alembic migrations applied; `users` table extended with subscription, MFA, and lockout columns
- `frontend/src/app/` — 38 Next.js App Router routes compiled cleanly, 0 TypeScript errors

### Fixed
- Alembic migration enum type duplication resolved
- Next.js `standalone` output build configuration corrected

---

## [0.1.0-RC1] — 2026-08-17

### Added
- Initial project scaffold: Next.js 15 frontend + FastAPI backend monorepo
- PostgreSQL (Neon) with async SQLAlchemy 2.0 ORM
- Redis (Upstash) for caching and rate limiting
- Qdrant vector database for semantic memory
- Neo4j for code knowledge graph
- JWT-based authentication (registration, login, logout, email verification, password reset)
- Argon2id password hashing
- Role-Based Access Control (RBAC) with `owner`, `admin`, `member`, `viewer` roles
- Multi-tenant `organizations` table with `org_id` foreign key
- Docker Compose configuration for local development
- Playwright E2E test suite
- pytest unit/integration test suite (199 tests, 63% coverage)
- `Makefile` with development commands
- `.pre-commit-config.yaml` with ruff linting and formatting

### Fixed
- Next.js frontend standalone output compilation build errors resolved
- Missing dependencies `pg8000` and `langgraph` added to `requirements.txt`
- Playwright login and signup Page Object Model selectors updated for redesigned landing screens
- Terminal emulator spec selector timeout assertions corrected

### Changed
- E2E spec breadcrumb heading assertions refactored

---

## [0.0.1] — 2026-08-01

### Added
- Repository initialized
- MIT License assigned (`Copyright 2026 Rounak Kumar Sah`)
- Initial `README.md`
- Basic project structure established

---

[Unreleased]: https://github.com/rounakkumarsah/ASEP/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/rounakkumarsah/ASEP/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/rounakkumarsah/ASEP/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/rounakkumarsah/ASEP/compare/v0.1.0-RC1...v0.1.1
[0.1.0-RC1]: https://github.com/rounakkumarsah/ASEP/compare/v0.0.1...v0.1.0-RC1
[0.0.1]: https://github.com/rounakkumarsah/ASEP/releases/tag/v0.0.1
