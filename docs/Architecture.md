# ASEP — Architecture Diagrams

**Version:** 0.1.3  
**Date:** 2026-08-23

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

```mermaid
graph TB
    subgraph Client["Client Layer"]
        B["Browser / IDE"]
    end

    subgraph CDN["Edge / CDN"]
        CF["Cloudflare\n(DDoS, TLS, Turnstile)"]
    end

    subgraph Frontend["Frontend — Next.js 15 (App Router)"]
        UI["Dashboard UI\n38 Routes"]
        WS_FE["WebSocket Client\n(xterm.js PTY)"]
    end

    subgraph Backend["Backend — FastAPI (Python 3.12)"]
        MW["Middleware Stack\n(CORS · Rate Limit · JWT · Logging)"]
        API["API Routers\n97 endpoints · 111 HTTP ops"]
        AgentRuntime["Agent Runtime\n(LangGraph State Machine)"]
        subgraph Agents["Multi-Agent DAG"]
            Planner["Planner Agent\n(Goal Decomposition)"]
            Supervisor["Supervisor Agent\n(DAG Orchestration)"]
            Coder["Coder Agent\n(Code Generation)"]
            Evaluator["Evaluator Agent\n(Test + Verify)"]
        end
        Governance["Policy Governance Engine\n(RBAC · Budget · HITL)"]
        Memory["Memory Service\n(3-Tier)"]
        Terminal["PTY Terminal Service\n(xterm.js ↔ pty)"]
        SandboxMgr["Sandbox Manager\n(Docker SDK)"]
    end

    subgraph Storage["Storage Layer"]
        PG["PostgreSQL / Neon\n(Users · Runs · Audit)"]
        Redis["Redis / Upstash\n(Sessions · Rate Limits · Queue)"]
        Qdrant["Qdrant\n(Vector Embeddings)"]
        Neo4j["Neo4j\n(Code Knowledge Graph)"]
    end

    subgraph Sandbox["Execution Sandboxes"]
        D1["Docker Container 1\n(Ephemeral · CPU/RAM limited)"]
        D2["Docker Container 2"]
        Dn["Docker Container N"]
    end

    subgraph External["External Services"]
        Gemini["Google Gemini API\n(Primary LLM)"]
        Anthropic["Anthropic Claude\n(Secondary LLM)"]
        Ollama["Ollama\n(Local LLM — self-hosted)"]
        Razorpay["Razorpay\n(Payments)"]
        Resend["Resend\n(Email)"]
        Sentry["Sentry\n(Error Tracking)"]
        PostHog["PostHog\n(Analytics)"]
        Cloudinary["Cloudinary\n(File Storage)"]
    end

    B --> CF --> Frontend
    Frontend --> Backend
    WS_FE -->|"WebSocket"| Terminal
    MW --> API --> AgentRuntime
    Planner --> Supervisor --> Coder --> Evaluator
    AgentRuntime --> Governance
    AgentRuntime --> Memory
    SandboxMgr --> D1 & D2 & Dn
    Coder --> SandboxMgr
    Memory --> Qdrant & Neo4j & Redis
    API --> PG
    API --> Razorpay & Resend
    AgentRuntime --> Gemini & Anthropic & Ollama
    Backend --> Sentry & PostHog
    API --> Cloudinary
```

---

## 2. DATA FLOW — AGENT RUN (End-to-End)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend (Next.js)
    participant API as FastAPI API Layer
    participant Gov as Governance Engine
    participant LG as LangGraph Orchestrator
    participant Plan as Planner Agent
    participant Code as Coder Agent
    participant Eval as Evaluator Agent
    participant Sand as Docker Sandbox
    participant Mem as Memory System
    participant DB as PostgreSQL

    User->>FE: Submit goal ("Refactor auth module")
    FE->>API: POST /api/v1/tasks {goal, project_id}
    API->>Gov: check_policy(user, action=CREATE_TASK)
    Gov-->>API: ALLOW
    API->>DB: INSERT agent_run (status=PENDING)
    API-->>FE: 202 Accepted {run_id}

    API->>LG: submit_goal(run_id, goal)
    LG->>Mem: query_semantic_memory(goal)
    Mem-->>LG: relevant code context (Qdrant + Neo4j)

    LG->>Plan: decompose(goal, context)
    Plan->>Plan: LLM call → structured plan[]
    Plan-->>LG: [Task1: read files, Task2: refactor, Task3: test]

    loop For each task in plan
        LG->>Gov: check_budget(run_id, token_count)
        Gov-->>LG: ALLOW / DENY
        LG->>Code: execute(task, context)
        Code->>Sand: spawn_container(image, limits)
        Sand-->>Code: container_id
        Code->>Sand: run(code_changes)
        Sand-->>Code: stdout, stderr, exit_code
        Code->>Gov: request_hitl_approval(diff)
        Gov->>DB: INSERT hitl_request (status=PENDING)
        Gov-->>Code: AWAITING_APPROVAL

        Note over User,Gov: User reviews diff in dashboard
        User->>API: POST /api/v1/hitl/{id}/approve
        API->>Gov: approve(hitl_id)
        Gov->>DB: UPDATE hitl_request (status=APPROVED)

        Code->>Sand: apply_approved_changes()
        Code->>Eval: test(changes)
        Eval->>Sand: run_tests()
        Sand-->>Eval: test_results (pass/fail)
        Eval-->>LG: {success: true, coverage: 87%}
        LG->>Mem: store_episodic_memory(task_result)
    end

    LG->>DB: UPDATE agent_run (status=COMPLETED)
    LG-->>FE: stream_event(type=COMPLETED, summary)
    FE-->>User: Show completion report
```

---

## 3. DEPLOYMENT ARCHITECTURE (Production)

```mermaid
graph LR
    subgraph Internet
        User["🌐 Users"]
    end

    subgraph CF_Edge["Cloudflare Edge"]
        CF_DNS["DNS + TLS\nTermination"]
        CF_WAF["WAF + DDoS\nProtection"]
        CF_Turn["Turnstile\nBot Protection"]
    end

    subgraph VPS["Production VPS / Cloud VM\n(Ubuntu 22.04 LTS, 4 vCPU, 8GB RAM)"]
        Traefik["Traefik Reverse Proxy\n:80 → :443 HTTPS redirect\n:443 → frontend:3000\n:443/api → backend:8000"]

        subgraph Compose["docker compose -f docker-compose.prod.yml up"]
            FE_C["frontend:3000\nNext.js standalone"]
            BE_C["backend:8000\nFastAPI + uvicorn"]
            PG_C["postgres:5432\n(or Neon serverless)"]
            Redis_C["redis:6379\n(or Upstash)"]
            Neo4j_C["neo4j:7687"]
            Qdrant_C["qdrant:6333"]
        end

        Docker_D["Docker Daemon\n(Sandbox Orchestration)"]
        Sandboxes["Ephemeral Containers\n(ASEP Agent Sandboxes)"]
    end

    subgraph Managed["Managed Cloud Services"]
        Neon["Neon PostgreSQL\n(Recommended for prod)"]
        Upstash["Upstash Redis\n(Recommended for prod)"]
        QdrantCloud["Qdrant Cloud\n(Optional)"]
    end

    subgraph SaaS["SaaS APIs"]
        Gemini_P["Google Gemini"]
        Razorpay_P["Razorpay"]
        Resend_P["Resend Email"]
        Sentry_P["Sentry"]
    end

    User --> CF_Edge --> Traefik
    Traefik --> FE_C & BE_C
    BE_C --> PG_C & Redis_C & Neo4j_C & Qdrant_C
    BE_C --> Docker_D --> Sandboxes
    BE_C -.->|"Optional: use managed"| Neon & Upstash & QdrantCloud
    BE_C --> Gemini_P & Razorpay_P & Resend_P & Sentry_P
```

---

## 4. AUTHENTICATION FLOW

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Redis as Redis (Rate Limiter)
    participant Email as Resend (Email)

    User->>FE: POST /register {email, password}
    FE->>API: POST /api/v1/auth/register
    API->>Redis: incr(rate_limit:register:{ip})
    Redis-->>API: count=1 (under limit)
    API->>Auth: hash_password(argon2id)
    Auth->>DB: INSERT users (email, hashed_pw, status=UNVERIFIED)
    Auth->>Email: send_verification_email(token)
    API-->>FE: 201 {message: "Check email"}

    User->>FE: Click verification link
    FE->>API: GET /api/v1/auth/verify?token=...
    API->>Auth: verify_token(token)
    Auth->>DB: UPDATE users SET status=ACTIVE
    API-->>FE: 200 {message: "Verified"}

    User->>FE: POST /login {email, password}
    FE->>API: POST /api/v1/auth/login
    API->>Redis: incr(rate_limit:login:{ip})
    Redis-->>API: count=3 (under limit of 5)
    API->>Auth: verify_password(argon2id)
    Auth->>DB: SELECT user WHERE email=...
    Auth-->>API: user (verified)
    API->>Auth: create_jwt(user_id, role)
    Auth-->>API: access_token (HS256, 60min)
    API-->>FE: 200 {access_token, token_type}

    FE->>API: GET /api/v1/users/me\nAuthorization: Bearer <token>
    API->>Auth: decode_jwt(token)
    Auth-->>API: {user_id, role, exp}
    API->>DB: SELECT user WHERE id=...
    API-->>FE: 200 {user object}
```

---

## 5. MEMORY SYSTEM ARCHITECTURE (3-Tier)

```mermaid
graph TB
    subgraph Input["Agent Input"]
        Goal["User Goal / Task"]
        CodeCtx["Repository Context"]
    end

    subgraph MemSys["3-Tier Memory System"]
        subgraph Tier1["Tier 1: Working Memory (Redis)"]
            WM["Ephemeral Session State\n• Current agent step\n• Token budget\n• Active tool calls\nTTL: session lifetime"]
        end

        subgraph Tier2["Tier 2: Episodic Memory (Qdrant)"]
            EM["Agent History Embeddings\n• Past runs (vector)\n• Tool call results\n• Error patterns\nRetrieval: cosine similarity"]
        end

        subgraph Tier3["Tier 3: Semantic Memory (Qdrant + Neo4j)"]
            VM["Code Embeddings (Qdrant)\n• Function-level vectors\n• Doc embeddings\n• Test case vectors"]
            KG["Code Knowledge Graph (Neo4j)\n• File → Module → Class → Function\n• Import dependencies\n• Call graph\n• AST relationships"]
        end
    end

    subgraph Retrieval["Retrieval Pipeline (GraphRAG)"]
        VSearch["Vector Search\n(Qdrant nearest neighbors)"]
        GTraversal["Graph Traversal\n(Neo4j Cypher)"]
        Fusion["Rank Fusion\n(RRF Algorithm)"]
        Context["Final Context Window\n(sent to LLM)"]
    end

    Goal --> WM
    CodeCtx --> VM & KG
    WM --> VSearch
    EM --> VSearch
    VM --> VSearch
    KG --> GTraversal
    VSearch --> Fusion
    GTraversal --> Fusion
    Fusion --> Context
```

---

## 6. NETWORK & PORT MAP (Local Development)

| Service | Internal Port | External Port | Protocol |
|---|---|---|---|
| Next.js Frontend | 3000 | 3000 | HTTP |
| FastAPI Backend | 8000 | 8000 | HTTP + WebSocket |
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6379 | TCP |
| Neo4j Browser | 7474 | 7474 | HTTP |
| Neo4j Bolt | 7687 | 7687 | Bolt/TCP |
| Qdrant REST | 6333 | 6333 | HTTP |
| Qdrant gRPC | 6334 | 6334 | gRPC |
| Ollama | 11434 | 11434 | HTTP |

---

## 7. TECHNOLOGY STACK SUMMARY

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend Framework** | Next.js (App Router) | 15.1.0 | SSR, routing, React 19 |
| **UI Components** | Radix UI + Tailwind CSS + shadcn/ui | Latest | Accessible component system |
| **Terminal** | xterm.js + WebSocket | 6.x | Browser PTY terminal |
| **3D Visualization** | WebGL / Three.js (via cobe) | 2.x | Neural matrix visualization |
| **State Management** | TanStack Query | 5.x | Server state + caching |
| **Backend Framework** | FastAPI | 0.115.x | Async REST API + WebSocket |
| **Agent Orchestration** | LangGraph | 0.2.x | Multi-agent state machines |
| **LLM Providers** | Gemini, Claude, Ollama | Latest | Code generation and reasoning |
| **Primary Database** | PostgreSQL (async via asyncpg) | 14+ | Persistent application data |
| **Cache / Queue** | Redis | 7.x | Rate limits, sessions, events |
| **Vector Database** | Qdrant | 1.x | Semantic memory embeddings |
| **Graph Database** | Neo4j | 5.x | Code knowledge graph |
| **ORM** | SQLAlchemy 2.0 (async) | 2.x | Database abstraction |
| **Migrations** | Alembic | 1.14.x | Schema version control |
| **Authentication** | JWT (HS256) + Argon2id | — | Auth + password hashing |
| **Payments** | Razorpay | 2.x | Subscription billing |
| **Email** | Resend | 2.x | Transactional email |
| **Error Tracking** | Sentry | 2.x | Runtime error monitoring |
| **Analytics** | PostHog | 1.x | Product analytics |
| **Bot Protection** | Cloudflare Turnstile | — | CAPTCHA on auth endpoints |
| **Sandbox Execution** | Docker SDK (Python) | 7.x | Ephemeral code execution |
| **Testing (Backend)** | pytest + pytest-asyncio | 9.x | 199 tests, 63% coverage |
| **Testing (Frontend)** | Vitest + Playwright | 4.x / 1.x | Unit + E2E tests |
