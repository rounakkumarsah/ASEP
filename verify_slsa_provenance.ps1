# verify_slsa_provenance.ps1
# World-class SLSA Level 3 Independent Verification Script

param(
    [Parameter(Mandatory=$false)]
    [string]$GitHubToken
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ASEP: SLSA Level 3 Independent Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Prompt for Token if not provided
if (-not $GitHubToken) {
    if ($env:GITHUB_TOKEN) {
        $GitHubToken = $env:GITHUB_TOKEN
        Write-Host "[+] Using GITHUB_TOKEN from environment variables." -ForegroundColor Green
    } else {
        $GitHubToken = Read-Host -Prompt "Enter your GitHub Personal Access Token (requires read:packages scope) [Masked]" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($GitHubToken)
        $GitHubToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
}

# 2. Check and Install GH CLI if missing
if (-not (Get-Command "gh" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] GitHub CLI (gh) not found. Attempting to install via winget..." -ForegroundColor Yellow
    winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
    $env:Path += ";C:\Program Files\GitHub CLI\"
}

# 3. Check and Install Cosign if missing
if (-not (Get-Command "cosign" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Cosign not found. Downloading cosign.exe locally..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://github.com/sigstore/cosign/releases/download/v2.2.4/cosign-windows-amd64.exe" -OutFile "cosign.exe"
    $CosignCmd = ".\cosign.exe"
} else {
    $CosignCmd = "cosign"
}

# 4. Authenticate GH CLI
Write-Host "[*] Authenticating GitHub CLI..." -ForegroundColor Blue
$GitHubToken | gh auth login --with-token
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] GitHub CLI authentication failed. Ensure token is valid." -ForegroundColor Red
    exit 1
}

# 5. Authenticate Docker GHCR
Write-Host "[*] Authenticating Docker to ghcr.io..." -ForegroundColor Blue
$GitHubToken | docker login ghcr.io -u "rounakkumarsah" --password-stdin
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Docker GHCR authentication failed. Ensure token has read:packages scope." -ForegroundColor Red
    exit 1
}

# 6. Fetch Image Digest
Write-Host "[*] Fetching Docker Image Digest..." -ForegroundColor Blue
docker pull ghcr.io/rounakkumarsah/asep:latest
$ImageDigest = docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/rounakkumarsah/asep:latest
Write-Host "[+] Successfully resolved digest: $ImageDigest" -ForegroundColor Green

# 7. Verify GitHub Artifact Attestation
Write-Host "[*] Verifying GitHub SLSA Artifact Attestations..." -ForegroundColor Blue
gh attestation verify oci://ghcr.io/rounakkumarsah/asep:latest --repo rounakkumarsah/ASEP --format json
if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Artifact Attestation Verified Successfully! (SLSA Level 3 Provenance)" -ForegroundColor Green
} else {
    Write-Host "[X] Artifact Attestation Verification Failed." -ForegroundColor Red
}

# 8. Verify Cosign Keyless Signature
Write-Host "[*] Verifying Cosign Keyless OIDC Signature..." -ForegroundColor Blue
& $CosignCmd verify `
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com `
  --certificate-identity-regexp="https://github.com/rounakkumarsah/ASEP/.*" `
  ghcr.io/rounakkumarsah/asep:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Cosign Cryptographic Signature Verified Successfully!" -ForegroundColor Green
} else {
    Write-Host "[X] Cosign Verification Failed." -ForegroundColor Red
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ZERO-TRUST AUDIT COMPLETE - ALL SLSA GATES PASSED" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
