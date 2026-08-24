# ASEP Institutional Security Policies & Framework Mapping
**Classification:** Enterprise Security & Governance  
**Author:** Rounak Kumar Sah  
**Status:** Approved  

---

## 1. Vulnerability Disclosure Policy (VDP)
* **Scope:** All ASEP components, AI models, sandboxes, and APIs.
* **Reporting:** Security researchers must report vulnerabilities to `security@asep.local`.
* **SLA:** Initial response within 24 hours. Triage within 48 hours. Patch for Critical/High within 7 days.
* **Safe Harbor:** Good-faith research will not face legal retaliation.

## 2. Third-Party Dependency Policy
* **Approval:** All new dependencies require static analysis (pip-audit, npm audit).
* **Licensing:** Only MIT, Apache 2.0, and BSD licenses are permitted in production.
* **Pinning:** All dependencies must be strictly version-pinned.
* **Review:** Dependency trees must be audited monthly.

## 3. Secrets Management Policy
* **Storage:** Secrets must never be committed to source control (enforced via `gitleaks`).
* **Injection:** Secrets must be injected at runtime via `.env` or secure vault providers.
* **Rotation:** All API keys and JWT secrets must be rotated every 90 days.
* **Scope:** `pydantic-settings` handles all runtime validation of secrets.

## 4. CI/CD Security Policy (SLSA Level 2)
* **Automation:** All PRs must pass `security-scan.yml`.
* **SAST:** Bandit, pip-audit, eslint, and tsc are mandatory release gates.
* **Least Privilege:** GitHub Actions tokens require minimum scopes (`contents: read`).
* **Provenance:** Build artifacts must correspond exactly to committed source code.

---

## 5. NIST SSDF (SP 800-218) Mapping
| SSDF Practice | Implementation | Status |
|---|---|---|
| **PO.1** Define Security Requirements | Implemented via ASVS v4.0 / AISVS | **VERIFIED** |
| **PO.3** Secure Environments | Docker sandboxing, Cap Drop, Read-Only FS | **VERIFIED** |
| **PS.1** Protect Code | GitHub RBAC, PR Reviews, Gitleaks | **VERIFIED** |
| **PW.5** Track Dependencies | CycloneDX SBOM, pip-audit, npm audit | **VERIFIED** |
| **RV.1** Analyze Code | Bandit, ESLint, Semgrep CI Gate | **VERIFIED** |

## 6. OWASP ASVS v4.0 Checklist
| ASVS Category | Defense Implementation | Status |
|---|---|---|
| **V2: Auth** | Argon2id + JWT HS256 + Rate Limiting | **VERIFIED** |
| **V4: Access**| Row-Level Security (RLS) + Tenant ID Isolation | **VERIFIED** |
| **V5: Validation**| Pydantic v2 schemas + SQL parameterized queries | **VERIFIED** |
| **V12: Files** | `WORKSPACE_ROOT` confinement + Path Traversal Jails | **VERIFIED** |
| **V14: Config**| Docker non-root execution (`1000:1000`) | **VERIFIED** |

## 7. SLSA Level 2 Readiness Report
* **Source:** Version controlled in Git (GitHub). (SLSA Level 1)
* **Build:** Automated builds via GitHub Actions. (SLSA Level 2)
* **Provenance:** Build process is documented and automated. (SLSA Level 2)
* **Signatures:** Cosign container signing prepared for deployment phase.
