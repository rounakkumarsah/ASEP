# Release Notes — OpenSEP v0.1.0-RC1
**Release Date:** August 17, 2026  
**Rolling Update Target:** v0.1.0  

We are excited to announce the release of **OpenSEP v0.1.0-RC1 (Release Candidate 1)**. This release marks the transition of OpenSEP into an enterprise-scale, production-ready Sovereign Autonomous Software Engineering Platform.

## 🚀 Key Achievements

- **Durable Persisted Orchestration**: LangGraph StateGraph agent execution state is fully persisted synchronously to Postgres Saver checkpoints.
- **Multi-Service Staging Stack**: Unified multi-container environment configurations with Postgres, Redis, Qdrant, and Next.js compiled in standalone builds.
- **Production Readiness & PRR**: Automated startup checking, database migrations via Alembic, and graceful degradations for Neo4j and Qdrant.
- **E2E Browser Test Verification**: 35/35 Playwright automated E2E browser tests passing cleanly across desktop and pixel-5 viewports.

## 🔒 Security & Governance

- **Human-in-the-Loop (HITL) Gateways**: Interactive diff comparisons and reviewer commentary inputs enforce manual authorization prior to execution.
- **Air-Gapped Operation Capable**: Bypasses external dependencies, utilizing Turnstile mock-tokens and decoupled runtime options.
