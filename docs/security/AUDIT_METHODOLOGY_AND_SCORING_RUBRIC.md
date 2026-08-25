# Audit Methodology & Scoring Rubric

**Document ID:** ASEP-SEC-METHODOLOGY-001  
**Classification:** Enterprise Security Governance & TDD Standards  
**Evaluation Standard:** Zero-Trust Evidence-Based Technical Due Diligence  

---

## 1. Verification Modalities & Evidence Tiers

To eliminate ambiguity regarding the scope of verification, every evaluated control declares an explicit verification modality:

| Modality Code | Verification Modality | Scope & Description | Required Proof |
| :--- | :--- | :--- | :--- |
| **MOD-SRC** | **Source & Configuration Inspection** | Static inspection of application source code, Dockerfiles, YAML manifests, and lockfiles. | Exact file path and line numbers. |
| **MOD-CI** | **CI/CD Execution Evidence** | Direct evidence of automated pipeline execution on GitHub Actions runners. | GitHub Actions Run ID, step status `success`, and SARIF/Attestation payload. |
| **MOD-TEST** | **Adversarial & Unit Test Execution** | Local or CI automated test suite execution validating defensive runtime invariants. | Pytest/Vitest execution logs, assertion trace, coverage reports. |
| **MOD-AUTH** | **Owner-Authenticated Verification** | Cryptographic verification requiring authenticated repository or registry tokens. | Terminal execution log from owner identity. |

---

## 2. Objective Scoring Rubric (100-Point Scale)

Scores are derived deterministically across 5 core security pillars. To maintain strict technical due diligence standards, conservative deductions are applied where live production infrastructure or isolated reusable workflow patterns are not yet deployed:

### Pillar 1: Application & API Security (Weight: 25% — Verified: 24/25)
* **Auth & Session Integrity (5/5 pts):** Argon2id hashing + JWT validation with audience/issuer checks (`MOD-SRC`, `MOD-TEST`).
* **Granular RBAC Authorization (5/5 pts):** Tool execution permission scopes enforced (`MOD-SRC`, `MOD-TEST`).
* **Database Multi-Tenancy (5/5 pts):** PostgreSQL Row-Level Security (RLS) policies deployed (`MOD-SRC`).
* **Security Headers & CORS (5/5 pts):** HSTS, CSP, X-Frame-Options, strict CORS configured (`MOD-SRC`).
* **Input Validation & Sanitization (4/5 pts):** Pydantic v2 schemas on all incoming payloads; minus 1 point for live production WAF verification boundary (`MOD-SRC`).

### Pillar 2: Supply Chain Security (Weight: 25% — Verified: 23/25)
* **Build Provenance Attestations (5/7 pts):** Demonstrates SLSA v1 Build Level 2 build provenance via GitHub Actions (`MOD-CI`). Minus 2 points for not utilizing an isolated reusable workflow for Level 3.
* **Container Image Signing (6/6 pts):** Keyless Cosign signatures pushed to registry (`MOD-CI`).
* **Deterministic Locking (6/6 pts):** Lockfiles present for both frontend (`package-lock.json`) and backend (`requirements.lock`) (`MOD-SRC`).
* **Automated Dependency Updates (6/6 pts):** Dependabot configured across all package ecosystems (`MOD-SRC`).

### Pillar 3: DevSecOps & CI/CD Hardening (Weight: 20% — Verified: 19/20)
* **Multi-Engine Static Analysis (7/7 pts):** CodeQL and Semgrep integrated with SARIF uploads (`MOD-CI`).
* **Secret Detection (5/5 pts):** Gitleaks integrated with full commit history scanning (`MOD-CI`).
* **Container Scanning (4/4 pts):** Trivy container vulnerability scanner active with severity gates (`MOD-CI`).
* **Action Pinning (3/4 pts):** GitHub Actions pinned to release tags; minus 1 point because anonymous signature verification requires owner authentication (`MOD-SRC`).

### Pillar 4: AI & Agentic Governance (Weight: 15% — Verified: 14/15)
* **Human-in-the-Loop Gate (5/5 pts):** Approval engine for high-risk actions (`terminal`, `fs.delete`) (`MOD-SRC`, `MOD-TEST`).
* **Execution Boundedness (5/5 pts):** Bounded DAG execution steps preventing infinite loops/DoS (`MOD-TEST`).
* **Container Sandboxing (4/5 pts):** Non-root user, `cap_drop=["ALL"]`, read-only rootfs, memory/PID caps (`MOD-SRC`). Minus 1 point for continuous red-teaming operational pipeline boundary.

### Pillar 5: Release Engineering & Documentation (Weight: 15% — Verified: 13/15)
* **Automated Release Packaging (5/5 pts):** Tag-driven releases attaching `SHA256SUMS.txt` and SBOM (`MOD-CI`).
* **Cryptographic Manifest Indexing (5/5 pts):** Structured hash index of all verification artifacts (`MOD-SRC`).
* **Defensible Claims (3/5 pts):** Zero unsubstantiated marketing absolutes; minus 2 points for initial documentation sanitization overhead (`MOD-SRC`).

---

## 3. Qualitative Conversion Scale

| Numeric Score | Qualitative Rating | Technical Due Diligence Assessment |
| :---: | :---: | :--- |
| **90 – 100** | **HIGH (Tier 1)** | Suitable for enterprise technical due diligence based on the documented evidence contained in this repository. |
| **75 – 89** | **MEDIUM (Tier 2)** | Functional security controls present, but lacks deterministic lockfiles, action pinning, or complete provenance. Requires remediation prior to technical due diligence. |
| **< 75** | **LOW (Tier 3)** | Significant architectural or supply chain gaps detected. Not suitable for enterprise deployment without overhaul. |
