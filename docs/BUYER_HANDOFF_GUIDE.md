# ASEP — Buyer Technical Handoff & Transition Guide
**Document ID:** ASEP-MA-DOC-025  
**Version:** 1.0 (Final M&A Release)  
**Target Asset:** Autonomous Software Engineering Platform (ASEP)  
**Author / Sole IP Owner:** Rounak Kumar Sah  
**Date:** August 24, 2026  

---

## 1. Executive Handover Overview

This guide provides the acquiring engineering team with a fast-track onboarding runbook for deploying, configuring, and maintaining the ASEP platform post-acquisition.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          30-DAY BUYER ONBOARDING PATH                       │
├─────────────────┬───────────────────────────────────────────────────────────┤
│ **Day 1–2**     │ Repository transfer, credential rotation & local sandbox  │
│ **Day 3–7**     │ Staging environment deployment on AWS / GCP / Azure       │
│ **Day 8–14**    │ Architecture walkthrough with Sole Author (Rounak Sah)    │
│ **Day 15–21**   │ Internal team integration, custom branding, and RBAC setup│
│ **Day 22–30**   │ Production launch and final escrow milestone sign-off     │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

---

## 2. Fast-Track Local Verification (10 Minutes)

To spin up and verify the entire ASEP platform locally:

```bash
# 1. Clone repository
git clone https://github.com/rounakkumarsah/ASEP.git
cd ASEP

# 2. Configure environment
cp .env.example .env

# 3. Launch full stack via Docker Compose
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify system readiness
curl -f http://localhost:8000/ready
# Output: {"status":"ready","database":"connected","redis":"connected","qdrant":"connected"}

# 5. Access UI
# Open browser to http://localhost:3000
```

---

## 3. Production Deployment Architecture Options

### Option A: Turnkey AWS EC2 / Docker via Terraform (Recommended)
Use the included Infrastructure as Code in `terraform/`:
```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```
*Provisions a secure Ubuntu 24.04 instance with Docker, UFW firewall, security groups, and automated HTTPS.*

### Option B: Kubernetes / Cloud-Native Deployment
* **Frontend:** Deploy Next.js 15.5.23 container to AWS ECS / EKS / Cloudflare Pages / Vercel.
* **Backend:** Deploy FastAPI 0.115 container to AWS ECS / EKS with auto-scaling policy (CPU > 70%).
* **Databases:** Connect to managed cloud services:
  * **PostgreSQL:** AWS RDS Aurora / Neon Serverless Postgres.
  * **Redis:** AWS ElastiCache / Upstash Redis.
  * **Vector DB:** Qdrant Cloud Cluster / Self-hosted Qdrant.
  * **AST Graph DB:** Neo4j AuraDB / Self-hosted Neo4j.

---

## 4. Key Configuration Parameters

All runtime configurations are driven by `.env`:

| Environment Variable | Description & Recommended Value |
|---|---|
| `APP_ENV` | `production` (Enables strict security, HTTPS cookies, JSON logs). |
| `JWT_SECRET_KEY` | High-entropy 256-bit random hex string. |
| `DATABASE_URL` | Async PostgreSQL connection string (`postgresql+asyncpg://...`). |
| `REDIS_URL` | Redis cluster connection string (`redis://...`). |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant vector database host and REST port. |
| `NEO4J_URI` / `NEO4J_AUTH` | Bolt protocol connection string and authentication credentials. |
| `LLM_PROVIDER` | `openai`, `anthropic`, `gemini`, or `ollama` (For sovereign air-gap). |
| `LLM_API_URL` | Local LLM endpoint (e.g. `http://localhost:11434` for Ollama). |
| `ENABLE_TURNSTILE` | `true` in production to enforce Cloudflare bot protection. |

---

## 5. Transition Support & Author Advisory

As part of the Asset Purchase Agreement, the author provides:
* **20 Hours of Direct Technical Consultation:** 1-on-1 architecture walkthroughs, code explanation, and migration assistance.
* **Private Communication Channel:** Dedicated Slack / Discord / Telegram channel for 30 days post-closing.
* **Emergency Hotfix SLA:** <24 hour response time for any critical deployment blockers during onboarding.

---
*Prepared and guaranteed by Rounak Kumar Sah.*
