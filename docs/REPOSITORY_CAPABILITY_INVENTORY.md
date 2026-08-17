# Repository Capability Inventory — OpenSEP

This document is a formal technical register and capability audit of the **OpenSEP** (Autonomous Software Engineering Platform) repository, created strictly from file analysis and code symbols.

---

## 1. Module Name: FastAPI Application & Ingress Gateway

### Purpose
Initializes the FastAPI application, mounts HTTP middleware, configures global CORS constraints, maps exception handlers, and instantiates the application lifecycle context hooks.

### Current Status
**Fully Implemented**

### Capabilities
* Configure middleware (structured logs, CORS origin parsing list).
* Sentry telemetry tracing integration.
* Global exception handling maps.

### Architecture
* **Inputs**: HTTP requests, ASGI lifespan events.
* **Outputs**: HTTP response codes, JSON bodies, headers.
* **Database**: Init/close DB engine pool triggers.
* **External APIs**: Sentry initialization handshake.

### AI Models
Not applicable.

### Memory
Not applicable.

### Agent Types
Not applicable.

### Tooling
* **Postgres**: Connection pools initialized/terminated.
* **Redis**: Ephemeral cache client initialization.

### Evidence
* **File Path**: [`backend/src/api/app.py`](file:///c:/Users/sachi/ASEP/backend/src/api/app.py)
* **Functions**: `create_app`, `lifespan`

---

## 2. Module Name: Local PTY Terminal Stream & Multiplexer

### Purpose
Coordinates interactive sandboxed bash/zsh shell processes via low-level PTY master-slave forks, manages select loops for asynchronous output forwarding, and publishes streams to Redis channels.

### Current Status
**Fully Implemented**

### Capabilities
* Asynchronous PTY master file descriptor writes (`os.write`).
* Select-based non-blocking buffer polling loops.
* Connection authorization checks and custom WS exit code 4401 on failure.
* Redis Pub/Sub stream synchronization for multiple horizontal API gateway replicas.

### Architecture
* **Inputs**: Keystroke buffers, socket resize packets.
* **Outputs**: Terminal output chunks over binary WebSockets.
* **Sandbox**: PTY sub-process forks.
* **WebSockets**: `/api/v1/ws/sessions/{session_id}/terminal` WS connection endpoint.

### AI Models
Not applicable.

### Memory
Not applicable.

### Agent Types
Not applicable.

### Tooling
* **PTY**: Master-slave OS file descriptor forks.
* **Redis**: Pub/Sub channel broadcasts.
* **OPA**: Validation of commands before writing to the PTY.

### Evidence
* **File Path**: [`backend/src/api/routers/terminal.py`](file:///c:/Users/sachi/ASEP/backend/src/api/routers/terminal.py)
* **Classes**: `TerminalRouter`

---

## 3. Module Name: Human-in-the-Loop (HITL) Decision Engine

### Purpose
Evaluates risk levels for agent actions, queues manual review sessions, pauses graph execution using LangGraph interrupts, and resolves operator decisions.

### Current Status
**Fully Implemented**

### Capabilities
* Mapped risk profiles for filesystem, git, docker, and terminal operations.
* DB persistence for review sessions via unit of work patterns.
* SLA response metric calculations.

### Architecture
* **Inputs**: Tool names, raw arguments, risk schemas.
* **Outputs**: Pending approval entries, operator decisions.
* **Database**: PostgreSQL `hitl_sessions` table.

### AI Models
Not applicable.

### Memory
* **Episodic**: Retained session justifications and notes.

### Agent Types
* **Review / Operator Gate**: Pauses execution nodes prior to critical tool invocations.

### Tooling
* **Postgres**: Implements SQLAlchemy repositories for state queries.

### Evidence
* **File Path**: [`backend/src/governance/hitl.py`](file:///c:/Users/sachi/ASEP/backend/src/governance/hitl.py)
* **Classes**: `HITLEngine`, `ReviewSession`
* **Table**: `hitl_sessions` in [`backend/src/db/models/hitl_session.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/hitl_session.py)

---

## 4. Module Name: AI Providers Runtime & Models Router

### Purpose
Bridges core system prompt pipelines with LLM model connectors, including Ollama, Google Gemini, OpenAI, and Anthropic.

### Current Status
**Fully Implemented**

### Capabilities
* Mapping LLM responses to structured templates.
* Lazy imports to minimize launch latencies.
* Custom structured schema formatting overrides.

### Architecture
* **Inputs**: Message history logs, temp settings, token counts.
* **Outputs**: Non-streaming responses or chunked stream tokens.

### AI Models
* **Anthropic**: Messages client mapping to `claude-3-5-sonnet-20241022`
* **Gemini**: REST API integration mapping to `gemini-2.5-flash`
* **Ollama**: Local connection mapping to `llama3.2`
* **OpenAI**: Client connection mapping to `gpt-4o`

### Memory
Not applicable.

### Agent Types
Not applicable.

### Tooling
* **HTTP**: Client wrappers with rate limit overrides.

### Evidence
* **File Path**: [`backend/src/ai_runtime/providers/anthropic.py`](file:///c:/Users/sachi/ASEP/backend/src/ai_runtime/providers/anthropic.py) (`AnthropicProvider`)
* **File Path**: [`backend/src/ai_runtime/registry.py`](file:///c:/Users/sachi/ASEP/backend/src/ai_runtime/registry.py) (`ProviderRegistry`)

---

## 5. Module Name: Next.js Frontend Dashboard & Visualizers

### Purpose
Provides a responsive WebGL interface displaying active agent states, pending approval diff queues, live terminal shells, and settings configurations.

### Current Status
**Fully Implemented**

### Capabilities
* frosted glassmorphism overlays and CSS telemetry ticker arrays.
* xterm.js WebGL terminal canvas nodes with custom themes.
* Monaco split-screen side-by-side diff comparison frames.

### Architecture
* **Inputs**: Web socket feeds, SSE conversations, REST JSON values.
* **Outputs**: Virtual DOM renders.
* **WebSockets**: WSS stream hooks.
* **Terminal**: Fits layouts and processes resizing parameters.

### AI Models
Not applicable.

### Memory
Not applicable.

### Agent Types
Not applicable.

### Tooling
* **xterm.js**: WebGL terminal emulator.
* **Monaco Editor**: Multi-tab code comparison layouts.

### Evidence
* **File Path**: [`frontend/src/app/(dashboard)/approvals/page.tsx`](file:///c:/Users/sachi/ASEP/frontend/src/app/%28dashboard%29/approvals/page.tsx)
* **File Path**: [`frontend/src/components/TerminalEmulator.tsx`](file:///c:/Users/sachi/ASEP/frontend/src/components/TerminalEmulator.tsx)
* **File Path**: [`frontend/src/components/MonacoDiffViewer.tsx`](file:///c:/Users/sachi/ASEP/frontend/src/components/MonacoDiffViewer.tsx)

---

## 6. Module Name: Task Execution DAG Orchestrator

### Purpose
Builds, scheduler-validates, executes, and scales out structured waves of independent sub-tasks concurrently using dependency matrices.

### Current Status
**Fully Implemented**

### Capabilities
* Executes waves concurrently.
* Supports cooperative pauses and cancellations.
* Automatically retries failed task items.

### Architecture
* **Inputs**: Decomposed plan schemas, task handlers, execution context.
* **Outputs**: Execution reports, progress updates.
* **Queue**: Concurrently runs independent waves using `asyncio.gather`.

### AI Models
Not applicable.

### Memory
* **Episodic**: Captures progress outputs and logs to database contexts.

### Agent Types
* **Supervisor**: Dispatches steps based on the current execution plan.

### Tooling
* **docker**: Pulls image tags and spins up isolated worker containers to evaluate shell scripts.

### Evidence
* **File Path**: [`backend/src/executor/executor.py`](file:///c:/Users/sachi/ASEP/backend/src/executor/executor.py) (`Executor`)
* **File Path**: [`backend/src/executor/worker.py`](file:///c:/Users/sachi/ASEP/backend/src/executor/worker.py) (`TaskWorker`)

---

## 7. Module Name: Enterprise Bounded Organization Contexts

### Purpose
Represents database-layer multi-tenant namespaces, developer programmatic key allocations, and RBAC profile setups.

### Current Status
**Fully Implemented**

### Capabilities
* Organization isolation namespaces.
* SHA-256 key hashing checks to prevent token data leaks.
* Display prefixes (first 8 chars) for programmatic keys in the dashboard.

### Architecture
* **Inputs**: Organization creation parameters.
* **Outputs**: Database entries.

### AI Models
Not applicable.

### Memory
Not applicable.

### Agent Types
Not applicable.

### Tooling
* **PostgreSQL**: Implements SQLAlchemy mapped models.

### Evidence
* **File Path**: [`backend/src/db/models/organization.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/organization.py) (`Organization`)
* **File Path**: [`backend/src/db/models/project.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/project.py) (`Project`)
* **File Path**: [`backend/src/db/models/api_key.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/api_key.py) (`ApiKey`)
* **File Path**: [`backend/src/db/models/user.py`](file:///c:/Users/sachi/ASEP/backend/src/db/models/user.py) (`User`)
