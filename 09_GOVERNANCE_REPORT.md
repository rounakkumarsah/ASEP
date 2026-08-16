# 09 — Governance & Human-in-the-Loop Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/governance/` and `backend/src/api/routers/hitl.py`.

---

## 1. Human-in-the-Loop (HITL) Engine

Implemented in `backend/src/governance/hitl.py` (`HITLEngine`).

### 1.1 Risk Levels & Action Enums
- **`RiskLevel`**: `Low`, `Medium`, `High`, `Critical`.
- **`ApprovalAction`**: `Approve`, `Reject`, `Modify`, `Retry`, `Escalate`, `Cancel`, `Expire`.
- **`ReviewerRole`**: `Operator`, `Team Lead`, `Administrator`, `Security Reviewer`, `Compliance Reviewer`.

### 1.2 Review Session Lifecycle (`ReviewSession`)
- High-risk operations (e.g., destructive terminal commands, production DB migrations) trigger execution pause and generate a resume token: `resume_tok_{uuid}`.
- Tracks SLA approval latency, execution timestamps, requesting agent ID, requesting tool, and audit trails.

---

## 2. Policy Engine & Safety Guardrails

Implemented in `backend/src/governance/policy_engine.py` and `guardrails.py`.
- **Regex & AST Guardrails**: Detects command injections (`rm -rf /`, `DROP DATABASE`, unverified state transitions).
- **Execution Pause/Resume**: Seamlessly pauses the LangGraph execution thread, waits for human decision, and resumes with modified arguments if requested.

---

## 3. Governance APIs

- `GET /api/v1/governance/hitl/queue`: List pending review sessions.
- `GET /api/v1/governance/hitl/statistics`: Approval SLA latency and escalation rates.
- `POST /api/v1/governance/hitl/review`: Submit human approval/rejection decision.
