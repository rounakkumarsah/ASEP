# 17 — Priority Next Steps & Execution Plan: ASEP

**Audit Date**: August 2026  
**Objective**: Clear, prioritized engineering roadmap to scale from current Tier-1 production baseline to full ecosystem maturity without modifying existing functionality.

---

## 1. Actionable Engineering Priorities

### Priority 1: Native Anthropic Claude Provider
- **Action**: Add `backend/src/ai_runtime/providers/anthropic.py` implementing `BaseProvider` for native Claude 3.5 Sonnet / Haiku support.
- **Estimated Effort**: Low (2–3 days).

### Priority 2: Direct GitHub App Webhook Bot Receiver
- **Action**: Implement `backend/src/api/routers/github_webhooks.py` to listen for issue comments (`@asep-bot fix #123`) and dispatch them to `AgentSupervisor`.
- **Estimated Effort**: Medium (1 week).

### Priority 3: Kubernetes Helm Charts & VPC Deployment
- **Action**: Create `/deploy/helm/` templates for enterprise VPC installations on AWS EKS, GCP GKE, and Azure AKS.
- **Estimated Effort**: Medium (1 week).

### Priority 4: Multi-Signature Quorum HITL Approvals
- **Action**: Extend `backend/src/governance/hitl.py` with multi-approver consensus rules for critical production database operations.
- **Estimated Effort**: Low (3–4 days).
