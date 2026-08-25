# Audit Methodology & Scoring Rubric

**Document ID:** ASEP-SEC-METHODOLOGY-001  
**Classification:** Enterprise Security Governance & TDD Standards  
**Evaluation Standard:** Zero-Trust Evidence-Based Technical Due Diligence  

---

## 1. Verification Modalities & Evidence Tiers

To eliminate ambiguity regarding the scope of verification, every evaluated control must declare an explicit verification modality:

| Modality Code | Verification Modality | Scope & Description | Required Proof |
| :--- | :--- | :--- | :--- |
| **MOD-SRC** | **Source & Configuration Inspection** | Static inspection of application source code, Dockerfiles, YAML manifests, and lockfiles. | Exact file path and line numbers. |
| **MOD-CI** | **CI/CD Execution Evidence** | Direct evidence of automated pipeline execution on GitHub Actions runners. | GitHub Actions Run ID, step status `success`, and SARIF/Attestation payload. |
| **MOD-TEST** | **Adversarial & Unit Test Execution** | Local or CI automated test suite execution validating defensive runtime invariants. | Pytest/Vitest execution logs, assertion trace, coverage reports. |
| **MOD-AUTH** | **Owner-Authenticated Verification** | Cryptographic verification requiring authenticated repository or registry tokens. | Terminal execution log from owner identity. |

---

## 2. Objective Scoring Rubric (100-Point Scale)

Scores are derived deterministically across 5 core security pillars. Each pillar consists of weighted, binary/tiered criteria:

### Pillar 1: Application & API Security (Weight: 25%)
* **Auth & Session Integrity (5 pts):** Argon2id hashing + JWT validation with audience/issuer checks (`MOD-SRC`, `MOD-TEST`).
* **Granular RBAC Authorization (5 pts):** Tool execution permission scopes enforced (`MOD-SRC`, `MOD-TEST`).
* **Database Multi-Tenancy (5 pts):** PostgreSQL Row-Level Security (RLS) policies deployed (`MOD-SRC`).
* **Security Headers & CORS (5 pts):** HSTS, CSP, X-Frame-Options, strict CORS configured (`MOD-SRC`).
* **Input Validation & Sanitization (5 pts):** Pydantic v2 schemas on all incoming payloads (`MOD-SRC`).

### Pillar 2: Supply Chain Security (Weight: 25%)
* **Cryptographic Attestations (7 pts):** SLSA Build Level 2 provenance generated via Sigstore OIDC (`MOD-CI`).
* **Container Image Signing (6 pts):** Keyless Cosign signatures pushed to registry (`MOD-CI`).
* **Deterministic Locking (6 pts):** Lockfiles present for both frontend (`package-lock.json`) and backend (`requirements.lock`) (`MOD-SRC`).
* **Automated Dependency Updates (6 pts):** Dependabot configured across all package ecosystems (`MOD-SRC`).

### Pillar 3: DevSecOps & CI/CD Hardening (Weight: 20%)
* **Multi-Engine Static Analysis (7 pts):** CodeQL and Semgrep integrated with SARIF uploads (`MOD-CI`).
* **Secret Detection (5 pts):** Gitleaks integrated with full commit history scanning (`MOD-CI`).
* **Container Scanning (4 pts):** Trivy container vulnerability scanner active with severity gates (`MOD-CI`).
* **Action Pinning (4 pts):** GitHub Actions pinned to release tags/SHAs with zero floating `@master` tags (`MOD-SRC`).

### Pillar 4: AI & Agentic Governance (Weight: 15%)
* **Human-in-the-Loop Gate (5 pts):** Approval engine for high-risk actions (`terminal`, `fs.delete`) (`MOD-SRC`, `MOD-TEST`).
* **Execution Boundedness (5 pts):** Bounded DAG execution steps preventing infinite loops/DoS (`MOD-TEST`).
* **Container Sandboxing (5 pts):** Non-root user, `cap_drop=["ALL"]`, read-only rootfs, memory/PID caps (`MOD-SRC`).

### Pillar 5: Release Engineering & Documentation (Weight: 15%)
* **Automated Release Packaging (5 pts):** Tag-driven releases attaching `SHA256SUMS.txt` and SBOM (`MOD-CI`).
* **Cryptographic Manifest Indexing (5 pts):** Structured hash index of all verification artifacts (`MOD-SRC`).
* **Defensible Claims (5 pts):** Zero unsubstantiated marketing absolutes in technical docs (`MOD-SRC`).

---

## 3. Qualitative Conversion Scale

| Numeric Score | Qualitative Rating | Technical Due Diligence Assessment |
| :---: | :---: | :--- |
| **90 – 100** | **HIGH (Tier 1)** | Architecture exhibits mature DevSecOps, automated provenance, strong sandboxing, and complete evidence traceability. Suitable for enterprise M&A closing. |
| **75 – 89** | **MEDIUM (Tier 2)** | Functional security controls present, but lacks deterministic lockfiles, action pinning, or complete provenance. Requires remediation prior to acquisition. |
| **< 75** | **LOW (Tier 3)** | Significant architectural or supply chain gaps detected. Not suitable for enterprise deployment without overhaul. |
