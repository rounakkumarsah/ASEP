# 02 — Missing Features Forensic Audit: ASEP

**Audit Date**: August 2026  
**Methodology**: Strict Codebase Inspection (Features marked 🔴 Missing have zero functional code in the repository).

---

## 1. Catalog of Missing Capabilities

The following features do not exist in the current codebase:

### 1.1 Native Anthropic Claude Provider
- **Status**: 🔴 Missing / NOT FOUND IN REPOSITORY
- **Forensic Check**:
  - `backend/src/ai_runtime/providers/` contains `gemini.py`, `openai.py`, `ollama.py`, and `mock.py`.
  - There is no `anthropic.py` or `claude.py` provider implementing the `BaseProvider` abstract contract.
- **Impact**: Claude 3.5 Sonnet / Haiku cannot be invoked natively without going through an MCP proxy or Ollama bridge.

### 1.2 Direct GitHub Marketplace App Webhook Bot
- **Status**: 🔴 Missing / NOT FOUND IN REPOSITORY
- **Forensic Check**:
  - The repository has tools for executing git commands (`git_commit`, `git_create_branch` in `backend/src/tools/impl.py`), but there is no dedicated GitHub App webhook receiver (`github_webhook.py`) that processes incoming issue comments (`@asep fix #123`).
- **Impact**: Automation currently requires starting sessions via the REST API or Dashboard rather than natural GitHub PR comments.

### 1.3 Native Desktop / IDE Extensions (VS Code / JetBrains)
- **Status**: 🔴 Missing / NOT FOUND IN REPOSITORY
- **Forensic Check**:
  - No `vscode-extension/` or `plugins/` directory exists in the repository.
- **Impact**: Developers interact with ASEP through the web dashboard, CLI, or direct REST API calls.

### 1.4 Multi-Signature HITL Quorum Approvals
- **Status**: 🔴 Missing / NOT FOUND IN REPOSITORY
- **Forensic Check**:
  - `backend/src/governance/hitl.py` supports single-reviewer approval sessions (`ReviewerRole.ADMINISTRATOR`, `ReviewerRole.SECURITY_REVIEWER`).
  - It does not contain multi-party signature aggregation logic (e.g., "Require 2 out of 3 Team Leads to approve").
- **Impact**: Approval flows are currently single-approver gated.

### 1.5 Automated Regression Benchmark Harness
- **Status**: 🔴 Missing / NOT FOUND IN REPOSITORY
- **Forensic Check**:
  - `backend/src/evaluation/evaluator.py` exists for scoring individual agent runs, but there is no continuous SWE-bench automated benchmark regression pipeline.
