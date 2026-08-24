# ASEP — System Sequence & Data Flow Specification
**Document ID:** ASEP-ARCH-DOC-003  
**Version:** 1.0 (Institutional Due Diligence)  
**Author:** Principal Software Architect (Rounak Kumar Sah)  
**Date:** August 24, 2026  

---

## 1. Goal Ingestion, Planning & Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Developer as Enterprise Developer / CI Trigger
    participant API as FastAPI Control Plane
    participant Supervisor as LangGraph Supervisor Node
    participant Planner as LLM Planner Node
    participant Memory as 4-Tier Memory Manager
    participant Sandbox as Hardened Docker Sandbox
    participant HITL as Governance HITL Gate

    Developer->>API: POST /api/v1/agent-runs (Goal, Project ID)
    API->>Supervisor: Initialize StateGraph with AgentState
    Supervisor->>Planner: Invoke planner_node(state)
    Planner->>Planner: Decompose Goal into DAG Tasks (3-10 steps)
    Planner-->>Supervisor: Return plan: list[str]
    
    loop For each task in plan
        Supervisor->>Memory: retrieve_context(task_query, session_id)
        Memory->>Memory: Hybrid Fusion (Redis + Postgres Decay + Qdrant + Neo4j)
        Memory-->>Supervisor: Merged Context Snapshot
        
        alt Critical Mutation / Deploy Action
            Supervisor->>HITL: Create ReviewSession (PENDING)
            HITL-->>Developer: WebSocket Alert (Approval Required)
            Developer->>HITL: POST /hitl/sessions/{id}/decision (APPROVE, Signature)
            HITL-->>Supervisor: Resume Graph Execution
        end

        Supervisor->>Sandbox: Execute Tool / Code (user 1000, cap_drop ALL)
        Sandbox-->>Supervisor: Execution Output / Test Results
        Supervisor->>Memory: add_episode(run_id, task_result)
    end

    Supervisor-->>API: StateGraph COMPLETED (Final Artifacts)
    API-->>Developer: Stream Final PR / Commit / Report
```

---

## 2. 4-Tier Memory Retrieval & Decay Fusion Flow

```mermaid
sequenceDiagram
    autonumber
    participant Agent as Agent Execution Node
    participant Fusion as MemoryRetrieval Engine
    participant Working as Redis Working Memory
    participant Episodic as PostgreSQL Episodic Store
    participant Vector as Qdrant Semantic DB
    participant Graph as Neo4j AST Knowledge Graph

    Agent->>Fusion: retrieve_context(query, session_id, limit=5)
    
    par Query Working Cache
        Fusion->>Working: GET asep:session:{id}:context
        Working-->>Fusion: In-flight session variables
    and Query Episodic Timeline
        Fusion->>Episodic: SELECT episodes WHERE project_id = :id
        Episodic-->>Fusion: Chronological episodes with timestamp
    and Query Vector Embeddings
        Fusion->>Vector: Dense Cosine Similarity Search(query_vector)
        Vector-->>Fusion: Top-K Documentation & Code Chunks
    and Query AST Graph
        Fusion->>Graph: MATCH (c:Class)-[:CALLS]->(m:Method) WHERE ...
        Graph-->>Fusion: Symbol Dependency Subgraph
    end

    Fusion->>Fusion: Calculate Time-Decay Score: S = Sim * exp(-lambda * delta_t)
    Fusion->>Fusion: Reciprocal Rank Fusion (RRF) & Context Window Packing
    Fusion-->>Agent: Formatted Context Snapshot (Bounded Tokens)
```

---

## 3. Interactive WebSocket PTY Terminal Streaming

```mermaid
sequenceDiagram
    autonumber
    actor Client as Web Dashboard (Xterm.js)
    participant WS as FastAPI WebSocket Router (/ws/sessions/{id}/terminal)
    participant Redis as Redis Cluster (State & PubSub)
    participant PTY as Linux Master/Slave PTY (os.fork)
    participant Container as Docker Sandbox Process

    Client->>WS: WebSocket Handshake (Bearer Token / Cookie)
    WS->>WS: Authenticate Token & Check Rate Limits
    WS->>Redis: SCARD asep:terminal:sessions (Check Concurrency Cap)
    Redis-->>WS: Active Session Count < MAX_CONCURRENT_SESSIONS
    WS->>Redis: SADD asep:terminal:sessions (Register Session)
    
    WS->>PTY: pty.fork() -> Setup Slave & Exec Shell (/bin/bash)
    PTY->>Container: Spawn Isolated Sandbox Shell Process
    
    par Client Stdin Loop
        Client->>WS: JSON Frame: {"type": "stdin", "data": "pytest tests/\n"}
        WS->>PTY: os.write(fd, data)
    and PTY Stdout Loop
        PTY->>WS: os.read(fd) -> raw stdout chunk
        WS->>Redis: PUBLISH asep:terminal:{id} (data)
        WS->>Client: Send WebSocket Text Chunk -> Xterm.js renders
    end

    Client->>WS: WebSocket Close / Disconnect
    WS->>PTY: killpg(SIGKILL) & os.close(fd)
    WS->>Redis: SREM asep:terminal:sessions (Unregister Session)
```

---
*Verified architectural specification.*
