# M&A Security Evidence & Artifact Manifest

This document serves as the central index for all required security verification artifacts for the ASEP repository. 

## 1. Governance & Policies
* ✅ **Security Policy (`SECURITY.md`):** Located at [`SECURITY.md`](file:///C:/Users/sachi/ASEP/SECURITY.md) (Includes Responsible Disclosure Policy).
* ✅ **Threat Model Diagrams:** Located at [`docs/architecture/ENTERPRISE_THREAT_MODEL_AND_TRUST_BOUNDARIES.md`](file:///C:/Users/sachi/ASEP/docs/architecture/ENTERPRISE_THREAT_MODEL_AND_TRUST_BOUNDARIES.md) (Includes STRIDE/LINDDUN mapping).
* ✅ **Pen-Test/Adversarial Test Report:** Located at [`docs/security/PENETRATION_TESTING_REPORT.md`](file:///C:/Users/sachi/ASEP/docs/security/PENETRATION_TESTING_REPORT.md) (100% Pass Rate).

## 2. CI/CD & Static Analysis (GitHub Actions)
The following artifacts are generated dynamically during the `security-scan.yml` GitHub Actions pipeline and are attached to the official GitHub Release and Action Run:

* ✅ **GitHub Actions Successful Run:** Viewable in the `Actions` tab of the repository for the `main` branch.
* ✅ **CodeQL SARIF Report:** Uploaded to GitHub Security Center (Code Scanning Alerts) via `github/codeql-action/upload-sarif`.
* ✅ **Semgrep SARIF Report:** Generated during CI (`semgrep.sarif`) and uploaded to GitHub Security Center.
* ✅ **Trivy JSON/SARIF Report:** Generated via `aquasecurity/trivy-action` (`trivy-results.sarif`).
* ✅ **Gitleaks JSON Report:** Enforced via `gitleaks/gitleaks-action@v2`.
* ✅ **Dependency Review Report:** Generated via `actions/dependency-review-action@v4` on all Pull Requests.

## 3. SLSA Supply Chain & Cryptographic Provenance
* ✅ **SBOM Validation Output:** CycloneDX 1.5 JSON SBOMs are attached to all official GitHub Releases (`docs/sales_package/15_SBOM_AND_SCA_REPORT.md`).
* ✅ **Container Image Digest:** Pushed to `ghcr.io/rounakkumarsah/asep:latest`. Exact SHA-256 digest is generated via `docker/build-push-action@v5`.
* ✅ **Cosign Verify Output:** Images are signed keylessly. Verification command: `cosign verify --certificate-oidc-issuer=https://token.actions.githubusercontent.com --certificate-identity-regexp=https://github.com/rounakkumarsah/ASEP ghcr.io/rounakkumarsah/asep:latest`.
* ✅ **Provenance Attestation Verification:** Attached to the image digest via `actions/attest-build-provenance@v1`. Verified via: `gh attestation verify oci://ghcr.io/rounakkumarsah/asep:latest -o rounakkumarsah`.
* ✅ **Signed Git Tag:** Commits to `main` are GPG-signed. Release artifact hashes (`sha256sum`) are embedded in the `release.txt` asset.
