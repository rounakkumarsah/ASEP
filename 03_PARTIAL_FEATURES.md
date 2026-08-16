# 03 — Partially Implemented Features Forensic Audit: ASEP

**Audit Date**: August 2026  
**Methodology**: Features marked 🟡 Partially Implemented have active scaffolds, backend services, or UI components, but lack complete end-to-end integration or enterprise features.

---

## 1. Catalog of Partially Implemented Capabilities

### 1.1 Team Member RBAC Invites
- **Status**: 🟡 Partially Implemented
- **Forensic Check**:
  - `Organization` table (`backend/src/db/models/organization.py`) and `/organizations` routes allow creating and managing organizations by owner.
  - Granular invitation emails and per-project member permission grids are scaffolded in the schema but not fully wired to a team invitation mailer.
- **Evidence**: `backend/src/api/routers/organizations.py` (Lines 1–205).

### 1.2 OpenTelemetry Distributed Tracing Exporter
- **Status**: 🟡 Partially Implemented
- **Forensic Check**:
  - `backend/src/production/opentelemetry_tracing.py` and `observability_tracer.py` contain OpenTelemetry tracer initialization hooks and span wrappers.
  - However, in `backend/src/api/app.py`, Sentry SDK is active as the primary error reporting engine, while the OTel gRPC collector exporter is configured for optional local daemon export.
- **Evidence**: `backend/src/production/opentelemetry_tracing.py`, `backend/src/api/app.py`.

### 1.3 Knowledge Hub Automatic Git Synchronization
- **Status**: 🟡 Partially Implemented
- **Forensic Check**:
  - Document upload, text chunking, and vector embedding in Qdrant are fully implemented (`backend/src/knowledge/service.py`, `sync.py`).
  - Automated continuous polling of external GitHub repository trees requires manual trigger via `/api/v1/knowledge/sync` rather than continuous webhook listeners.
- **Evidence**: `backend/src/api/routers/knowledge_sync.py`, `backend/src/knowledge/sync.py`.

### 1.4 Interactive Playground Model Comparator
- **Status**: 🟡 Partially Implemented
- **Forensic Check**:
  - `/playground` route (`frontend/src/app/(dashboard)/playground/page.tsx`) allows interactive task execution with streaming outputs.
  - Side-by-side simultaneous comparison of two different LLMs (e.g., Gemini vs. Ollama) running the exact same prompt is currently sequential rather than split-screen concurrent.
- **Evidence**: `frontend/src/app/(dashboard)/playground/page.tsx`, `backend/src/ai_runtime/service.py`.
