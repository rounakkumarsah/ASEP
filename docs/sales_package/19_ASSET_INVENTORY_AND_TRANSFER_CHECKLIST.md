# ASEP — Asset Inventory & Acquisition Transfer Checklist
**Document ID:** ASEP-MA-DOC-019  
**Version:** 1.0 (Final Acquisition Release)  
**Target Asset:** Autonomous Software Engineering Platform (ASEP)  
**Sole Equity & IP Owner:** Rounak Kumar Sah  
**Classification:** M&A CLOSING & CLOSURE PROTOCOL  
**Date:** August 24, 2026  

---

## 1. Complete Asset Inventory Register

The transaction covers the full, outright assignment of all tangible and intangible digital assets comprising the ASEP platform:

### 1.1 Source Code Repositories & Git History
* **Repository:** `rounakkumarsah/ASEP` (Full Git history from inception to Release 0.1.4).
* **Backend Runtime:** ~306 Python source files (FastAPI, LangGraph StateGraph, 4-Tier Memory, Docker Execution Engine, Redis PubSub PTY, Alembic Migrations, Prometheus instrumentation).
* **Frontend Application:** ~85 TypeScript/React source files (Next.js 15.5.23, Tailwind CSS, Framer Motion 3D telemetry matrix, Radix UI, Xterm.js PTY console, Razorpay billing integration).
* **Infrastructure as Code:** Terraform AWS modules (`terraform/main.tf`, `variables.tf`, `outputs.tf`), Production Docker Compose stack (`docker-compose.prod.yml`, `docker-compose.enterprise.yml`).
* **Test Suites:** 150+ Unit, Integration, and Regression test cases (`backend/tests/`).

### 1.2 Documentation & IP Dossier
* **Due Diligence Package:** 24 comprehensive M&A documents in `docs/sales_package/` and `docs/`.
* **Architecture Specifications:** Complete system diagrams, Threat Models, STRIDE analysis, and 5 Architecture Decision Records (ADRs).
* **Compliance Artifacts:** CycloneDX SBOMs, Bandit SAST reports, pip-audit and npm audit vulnerability scan outputs, license compliance matrices.
* **Operational Runbooks:** Production operations runbook, incident response guide, disaster recovery procedures, and capacity scaling models.

---

## 2. Step-by-Step Acquisition Transfer Runbook

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ASEP 5-STAGE TRANSFER RUNBOOK                         │
├─────────────────┬───────────────────────────────────────────────────────────┤
│ Stage 1: Legal  │ Execute Asset Purchase Agreement & IP Assignment Deed     │
│ Stage 2: Escrow │ Buyer deposits funds in escrow (Escrow.com / Bank Wire)   │
│ Stage 3: Code   │ Transfer GitHub Organization / Repo ownership to Buyer   │
│ Stage 4: Cloud  │ Handover domain DNS, container registries & cloud configs │
│ Stage 5: Close  │ 30-Day Transition Support & Final Escrow Release          │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

### Stage 1: Legal & IP Assignment (Days 1–2)
1. Both parties execute the finalized **Asset Purchase Agreement (APA)** (`docs/sales_package/13_ASSET_PURCHASE_AGREEMENT_DRAFT.md`).
2. Seller executes the notarized **Sole IP Ownership & Bill of Sale Affidavit** (`docs/sales_package/11_IP_OWNERSHIP_AND_BILL_OF_SALE_DECLARATION.md`).
3. Seller delivers legal warranty confirming absence of any encumbrances, liens, contractor claims, or litigation.

### Stage 2: Escrow Funding (Days 2–3)
1. Parties initialize an escrow transaction via Escrow.com or buyer's designated escrow agent.
2. Buyer funds the full purchase price into the escrow account.
3. Escrow agent notifies Seller of verified funds receipt.

### Stage 3: Code Repository & Account Handover (Days 3–4)
1. **GitHub Repository Transfer:**
   * Seller invites Buyer's GitHub administrative account as Owner of `rounakkumarsah/ASEP`.
   * Repository ownership transferred completely; Seller retains no fork or mirror.
2. **Package & Container Registries:**
   * Transfer ownership of Docker Hub / GHCR image repositories.
3. **Domain & DNS Records:**
   * Push domain authorization codes (EPP) to Buyer's registrar (Cloudflare / Namecheap).

### Stage 4: Secrets & Infrastructure Rotation (Days 4–5)
1. Seller securely transmits master credentials and salt keys via 1Password / Bitwarden secure link:
   * `JWT_SECRET_KEY` master key generation script.
   * Encryption salt for Human-in-the-Loop cryptographic approval tokens.
   * Terraform AWS state backend access.
2. Buyer rotates all cloud API keys (PostgreSQL Neon, Upstash Redis, Qdrant Cloud, Neo4j Aura, Razorpay Merchant Keys).

### Stage 5: Technical Advisory & Final Escrow Release (Days 5–30)
1. **30-Day Advisory Period:** Seller provides up to 20 hours of senior architectural advisory:
   * 1-on-1 code walkthrough with buyer's engineering team.
   * Assistance with custom enterprise deployment or cloud migration.
   * Guidance on local LLM air-gap configurations (Ollama / vLLM).
2. Upon Buyer verification of all assets, Escrow agent releases funds to Seller.

---
*Verified and ready for transaction execution by Rounak Kumar Sah.*
