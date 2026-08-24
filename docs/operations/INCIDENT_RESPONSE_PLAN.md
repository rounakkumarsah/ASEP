# ASEP — Enterprise Incident Response Plan (IRP)
**Document ID:** ASEP-OPS-DOC-002  
**Version:** 1.0 (Enterprise Standard)  
**Classification:** OPERATIONAL RESILIENCE & SRE RUNBOOK  
**Date:** August 24, 2026  

---

## 1. Incident Severity Classification Matrix

| Severity Level | Definition & Business Impact | Response SLA | Escalation Target |
|---|---|---|---|
| **SEV-1 (Critical)** | Core API offline; agent execution halted; active security breach or data corruption. | **< 15 minutes** | Incident Commander, Lead Architect, Security Lead |
| **SEV-2 (High)** | Degradation of secondary services (Neo4j AST offline, vector RAG degraded); UI accessible but agent planning slow. | **< 1 hour** | Primary On-Call SRE, Senior Backend Engineer |
| **SEV-3 (Medium)** | Non-blocking feature bug (e.g. export report fails, minor latency spike); workarounds available. | **< 4 hours** | Platform Engineering Team |
| **SEV-4 (Low)** | Minor UI cosmetic issue, documentation discrepancy, or non-urgent maintenance request. | **Next Business Day**| Backlog / Sprint Planning |

---

## 2. Standard 6-Phase Incident Response Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 1. Detection│ -> │ 2. Triage   │ -> │ 3. Contain  │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
┌─────────────┐    ┌─────────────┐           ▼
│ 6. Post-    │ <- │ 5. Recovery │ <- ┌─────────────┐
│    Mortem   │    │    & Verify │    │4. Eradicate │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Phase 1: Detection & Alerting
* Automated Prometheus alerts trigger via Slack/PagerDuty webhook on:
  * Error rate > 1% over 5-minute window (`rate(http_requests_total{status=~"5.."}[5m])`).
  * P95 API latency > 500ms over 5-minute window.
  * Sandbox container crash rate > 5%.

### Phase 2: Triage & Role Assignment
* SRE On-Call establishes an Incident Command channel (`#incident-YYYYMMDD-sevX`).
* Roles designated:
  * **Incident Commander (IC):** Manages timeline, assigns investigation tasks.
  * **Technical Lead (TL):** Conducts code/infrastructure root cause analysis.
  * **Communications Lead:** Updates status page and enterprise stakeholders.

### Phase 3: Containment Protocols
* **Degraded Mode Failover:**
  * If Neo4j goes down: ASEP auto-falls back to 3-tier memory mode (Working + Episodic + Qdrant).
  * If Redis goes down: Terminal router reverts to local single-node memory sets.
* **Traffic Isolation:**
  * If rogue agent execution detected: Invoke `POST /api/v1/agent-runs/{id}/cancel` to immediately terminate child container sandboxes.

### Phase 4: Eradication & Hotfix Deployment
* Identify faulty commit, dependency vulnerability, or corrupted database state.
* Rollback via Docker Compose / ECS task revision or deploy tagged emergency patch.

### Phase 5: Recovery & Verification
* Run health checks: `curl -f http://localhost:8000/ready`.
* Execute automated smoke tests: `python scripts/smoke_test.py`.
* Verify Prometheus error rates return to baseline 0.00%.

### Phase 6: Post-Mortem & Blameless Review
* Within 48 hours of resolution, publish a formal Root Cause Analysis (RCA) document:
  * Timeline of events (Detection, Response, Recovery).
  * Root Cause (Why did it happen?).
  * Action Items (How do we prevent recurrence?).

---
*Maintained by ASEP Operational Resilience Team.*
