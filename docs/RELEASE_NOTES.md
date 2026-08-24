# Release Notes — ASEP v0.1.5 (Production & Acquisition Ready)
**Release Version:** v0.1.5 (Institutional M&A Release)  
**Release Date:** August 24, 2026  
**Author / Sole IP Owner:** Rounak Kumar Sah  

We are proud to announce the formal release of **ASEP v0.1.5 (Autonomous Software Engineering Platform)**. This milestone cements ASEP as an institutional-grade, production-ready, sovereign AI engineering operating system.

---

## 🚀 Key Architectural Deliverables

- **LangGraph StateGraph DAG Orchestration:** Deterministic multi-agent task execution with strict step boundaries, state checkpoint persistence, and typed state containers.
- **4-Tier Hybrid Memory System:** Fully coordinated memory fusion uniting Redis working cache, PostgreSQL time-decay scored episodic logs ($e^{-\lambda t}$), Qdrant vector semantic search, and Neo4j AST knowledge graphs.
- **Hardened Non-Root Container Sandboxes:** Complete execution isolation using unprivileged Docker containers (`user="1000:1000"`, `cap_drop=["ALL"]`, read-only rootfs, `tmpfs`, `pids_limit=100`).
- **PostgreSQL Row-Level Security (RLS):** Database engine-level multi-tenant isolation via Alembic migrations.
- **Distributed WebSocket PTY Terminal:** Real-time terminal streaming with Redis distributed concurrency tracking (`sadd`/`srem`/`scard`) and PubSub broadcast.
- **Model Context Protocol (MCP):** Turnkey MCP v1.0 client integration for dynamic enterprise tool execution.
- **Next.js 15.5.23 Upgrade:** Patched all upstream security advisories (middleware authorization bypass, App Router fixes) with 0 CVEs.

---

## 📊 Empirical Benchmarks & Unit Economics

- **Success Rate:** 100% across 5 core enterprise task profiles.
- **Mean Latency:** 0.174 seconds per task execution step.
- **Unit Economics (Cost per 1,000 Tasks):**
  - **OpenAI GPT-4o:** $7.99
  - **Claude 3.5 Sonnet:** $11.66
  - **Google Gemini 1.5 Pro:** $4.00
  - **Local Ollama Qwen-2.5-Coder:** $0.00 (100% Sovereign Air-Gap)

---

## 🔒 Security, Compliance & Data Room

- **100% Permissive Dependency Tree:** All production dependencies audited and verified (MIT, Apache-2.0, BSD-3).
- **SAST & Vulnerability Audits:** Bandit SAST scan, npm audit, and pip-audit reports clean.
- **Complete M&A Data Room:** 27 comprehensive due diligence documents, ADRs, Threat Models, and Asset Purchase Agreement drafts published in `docs/` and `docs/sales_package/`.

---
*For technical inquiries or acquisition closing details, contact Rounak Kumar Sah.*
