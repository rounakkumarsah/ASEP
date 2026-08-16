# 07 — 90-Day Strategic Roadmap: ASEP

**Objective**: Scale ASEP from a standalone local engineering operating system to a complete cloud-native, IDE-integrated ecosystem.

---

## 1. Phase-by-Phase Roadmap

### Month 1 (Days 1–30): UI/UX DevEx & Core AI Upgrades
- Complete Anthropic Claude 3.5 provider integration.
- Monaco interactive diff and file tree viewer.
- Live Web PTY terminal streaming (`xterm.js`).
- Multi-signature HITL quorum rules.

### Month 2 (Days 31–60): GitHub Ecosystem & Automated PR Bot
- Build official GitHub App webhook receiver (`backend/src/api/routers/github_webhooks.py`).
- Implement automated branch creation, containerized test execution, and GitHub PR creation with markdown diff summaries.
- Deploy automated SWE-bench benchmark regression tracking.

### Month 3 (Days 61–90): VS Code Extension & Enterprise Kubernetes
- Publish official ASEP VS Code companion extension on the Visual Studio Marketplace.
- Deliver Helm charts and Terraform templates for 1-click private VPC enterprise deployments (AWS EKS, GCP GKE, Azure AKS).
- Launch public v1.0 on Hacker News, Product Hunt, and GitHub Trending.
