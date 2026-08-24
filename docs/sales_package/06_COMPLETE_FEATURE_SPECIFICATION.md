# ASEP — Complete Feature Specification & Capabilities Catalog
==============================================================

## 1. Developer Control Plane & Workspace
* **Real-Time Interactive Terminal**: In-browser xterm.js terminal connected to live PTY session over WebSockets.
* **Monaco Diff Viewer**: Side-by-side git visual diff viewer for reviewing agent code modifications.
* **Session Manager**: Track concurrent agent sessions, active memory contexts, and command histories.
* **Developer Onboarding Checklist**: Guided onboarding modal for fresh workspace creation.

## 2. Autonomous Multi-Agent Engine
* **Goal Decomposer**: LangGraph node breaking high-level user requests into actionable subtasks.
* **Parallel DAG Scheduler**: Concurrent task execution engine mapping dependency trees across worker agents.
* **Specialized Agent Roles**: Planner, Executor, Testing, Reviewer, Memory, and Governance agents.
* **Human-In-The-Loop (HITL) Gatekeeper**: Interactive approval modal halting agent cycles before critical edits.

## 3. Sovereign Multi-Layer Memory
* **Semantic Code Memory**: Qdrant vector index embedding code chunks for semantic similarity lookup.
* **Knowledge Graph RAG**: Neo4j property graph mapping repository symbols, classes, and dependencies.
* **Working & Episodic Memory**: Redis and PostgreSQL storing execution states, session histories, and threads.

## 4. SaaS & Monetization Infrastructure
* **Subscription Management**: Free, Pro, Team, and Enterprise tier provisioning.
* **Daily Quota Limiter**: Dynamic freemium quota tracker allocating queries per day.
* **Razorpay Payment Flow**: Integrated order creation, checkout modal, HMAC verification, and webhook sync.
* **Organization & Team Workspaces**: Multi-tenant organizations with member invitations and RBAC roles.
