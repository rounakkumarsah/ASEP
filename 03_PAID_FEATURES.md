# 03 — Paid & Managed Infrastructure Requirements: ASEP

**Focus**: Features that require cloud resources, managed enterprise services, or third-party paid subscriptions when deploying hosted SaaS environments.

---

## 1. Managed Infrastructure Cost Breakdown

| Feature | Third-Party Provider | Cost Type | Recommended Strategy for Open Source |
|---|---|---|---|
| **1. Multi-Tenant Hosted Sandboxes** | AWS ECS / E2B / Fly.io / Modal | Pay-per-second container execution ($0.0001/sec) | Keep default as **Local Docker Sandbox**; offer cloud sandboxes as an optional enterprise plugin. |
| **2. Production Managed Vector DB** | Qdrant Cloud / Pinecone | Managed cluster ($25–$70/mo) | Keep self-hosted Qdrant in `docker-compose.yml` for 100% free local usage. |
| **3. Production Managed Graph DB** | Neo4j AuraDB | Managed graph ($65/mo) | Keep self-hosted Neo4j in `docker-compose.yml` for free local usage. |
| **4. Cloudflare Enterprise Turnstile / WAF**| Cloudflare | $0 (Free tier) to $200/mo (Enterprise) | Use the standard Free Turnstile tier (already implemented). |
| **5. Email Dispatch Service** | Resend / SendGrid / AWS SES | $0 (Free 3,000 emails/mo on Resend) | Use Resend free tier for team invitations and password resets. |
| **6. Continuous SWE-bench CI Runners** | GitHub Actions Large Runners | ~$0.08/min for 8-core runners | Run local test suites on PRs; run full SWE-bench suites on release tags. |
