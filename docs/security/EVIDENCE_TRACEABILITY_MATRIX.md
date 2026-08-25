# Evidence Traceability Matrix

**Project:** ASEP (Autonomous Software Engineering Platform)  
**Standard:** Enterprise Zero-Trust Audit & M&A Technical Due Diligence  
**Last Updated:** August 25, 2026  

---

## 1. Traceability Mapping

| Control ID | Audit Claim | Repository Location | CI/CD Workflow & Step | Artifact / Execution Evidence | Evidence Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TR-01** | CodeQL SAST Analysis | [`.github/workflows/security-scan.yml:93-107`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L93-L107) | Job `codeql-scan`, Step `Perform CodeQL Analysis` | GitHub Actions Run `13502096000`, uploaded to Security Tab | Level B |
| **TR-02** | Semgrep SAST Analysis | [`.github/workflows/security-scan.yml:77-92`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L77-L92) | Job `semgrep-scan`, Step `Run Semgrep SAST` | `semgrep.sarif` uploaded via `upload-sarif@v3` | Level B |
| **TR-03** | Gitleaks Secret Scan | [`.github/workflows/security-scan.yml:108-118`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L108-L118) | Job `gitleaks-scan`, Step `Run Gitleaks` | Zero secrets detected in git commit history | Level B |
| **TR-04** | Trivy Container Scanning | [`.github/workflows/security-scan.yml:161-173`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L161-L173) | Job `docker-provenance`, Step `Run Trivy scanner` | `trivy-results.sarif` uploaded via `upload-sarif@v3` | Level B |
| **TR-05** | CycloneDX 1.6 SBOM | [`docs/security/artifacts/sbom.json`](file:///C:/Users/sachi/ASEP/docs/security/artifacts/sbom.json) | Job `create-release`, Step `Create Release` | Attached to GitHub Release `v1.0.0` | Level C / B |
| **TR-06** | Sigstore Cosign Signing | [`.github/workflows/security-scan.yml:175-179`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L175-L179) | Job `docker-provenance`, Step `Sign published image` | Keyless OIDC signature pushed to `ghcr.io` | Level B |
| **TR-07** | SLSA Build Provenance | [`.github/workflows/security-scan.yml:181-186`](file:///C:/Users/sachi/ASEP/.github/workflows/security-scan.yml#L181-L186) | Job `docker-provenance`, Step `Artifact Attestation` | In-toto SLSA Build Level 2 attestation pushed to GHCR | Level B |
| **TR-08** | SHA256 Checksums | [`.github/workflows/release.yml:20-22`](file:///C:/Users/sachi/ASEP/.github/workflows/release.yml#L20-L22) | Job `create-release`, Step `Generate Checksums` | `SHA256SUMS.txt` attached to Release `v1.0.0` | Level B |
| **TR-09** | Multi-Ecosystem Dependabot | [`.github/dependabot.yml:1-32`](file:///C:/Users/sachi/ASEP/.github/dependabot.yml#L1-L32) | GitHub Automated Scanning | Monitored weekly for `pip`, `npm`, and `github-actions` | Level C |
| **TR-10** | Non-Root Container Sandboxing | [`backend/Dockerfile:47-61`](file:///C:/Users/sachi/ASEP/backend/Dockerfile#L47-L61), [`frontend/Dockerfile:43-55`](file:///C:/Users/sachi/ASEP/frontend/Dockerfile#L43-L55) | CI Docker build step | `asepuser` (1000:1000) and `nextjs` (1001:1001) users | Level C |
| **TR-11** | Agent RBAC Permissions | [`backend/src/tools/permissions.py:5-33`](file:///C:/Users/sachi/ASEP/backend/src/tools/permissions.py#L5-L33) | Runtime execution | Verified in `test_comprehensive_adversarial.py` | Level A |
| **TR-12** | Human-in-the-Loop Governance | [`backend/src/governance/hitl.py:95-393`](file:///C:/Users/sachi/ASEP/backend/src/governance/hitl.py#L95-L393) | Runtime execution | Verified in `test_hitl.py` & `test_hitl_bridge.py` | Level A |
| **TR-13** | Deterministic Python Lockfile | [`backend/requirements.lock`](file:///C:/Users/sachi/ASEP/backend/requirements.lock) | Build resolution | Pinned exact dependency hashes | Level C |
