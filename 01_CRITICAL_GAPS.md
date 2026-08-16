# 01 — Critical Gaps & Missing Capabilities: ASEP

**Audit Objective**: Identify ONLY the functional, architectural, and developer experience gaps preventing ASEP from reaching tier-1 parity with Devin, OpenHands, and Claude Code.

---

## 1. Top 7 Critical Architectural Gaps

### 1. Natural Language Interactive Terminal & Chat Loop
- **Current Limitation**: Sessions are triggered primarily via discrete goal dispatching (`POST /api/v1/agent-runs`) or playground tasks.
- **The Gap**: Lack of a continuous interactive conversation loop where a developer can interrupt an active agent, provide real-time clarifying feedback, and guide execution mid-flight.

### 2. Direct GitHub App Bot & PR Automation
- **Current Limitation**: Git operations (`git_commit`, `git_create_branch`) run inside the Docker sandbox.
- **The Gap**: No official GitHub App webhook receiver (`@asep-bot fix #issue`) that clones external forks, runs the agent, creates branches, and opens verified Pull Requests with automated markdown diff summaries.

### 3. Native Anthropic Claude 3.5 Sonnet Provider
- **Current Limitation**: Runtime supports Gemini, OpenAI, and Ollama.
- **The Gap**: Missing native `anthropic.py` provider module implementing the `BaseProvider` contract for Claude 3.5 Sonnet (the industry benchmark for autonomous coding reasoning).

### 4. Interactive In-Browser Code Diff & File Tree Viewer
- **Current Limitation**: Dashboard shows task timelines, statuses, and stdout logs.
- **The Gap**: No integrated Monaco editor / Git Diff viewer in `app/(dashboard)/sessions/[id]` to visually inspect proposed file diffs side-by-side before approval.

### 5. VS Code Companion Extension (LSP / Bridge)
- **Current Limitation**: Web dashboard and CLI only.
- **The Gap**: No native VS Code extension connecting directly to the ASEP Docker daemon / REST API to trigger agent workflows from within the developer's primary IDE.

### 6. Multi-Party HITL Quorum Approvals
- **Current Limitation**: HITL supports single-operator approval sessions.
- **The Gap**: Enterprise compliance requirement for multi-signature quorum rules (e.g., "Require 2 Senior Reviewers before executing production schema migrations").

### 7. Continuous Automated Coding Benchmarks (SWE-bench Harness)
- **Current Limitation**: Evaluator scores individual runs against heuristics.
- **The Gap**: Automated regression pipeline benchmarking ASEP against standard SWE-bench / HumanEval test cases on every release.
