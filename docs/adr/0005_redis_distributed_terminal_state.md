# ADR 0005: Redis Distributed Terminal State & PubSub Streaming

* **Status:** Accepted  
* **Date:** 2026-08-24  
* **Deciders:** Principal Architect & Platform Lead (Rounak Kumar Sah)  
* **Context:** Horizontal scaling of interactive WebSocket PTY terminal sessions.

---

## Context and Problem Statement

ASEP provides real-time interactive terminal access to sandboxed execution environments via WebSocket and Python's `pty` module (`backend/src/api/routers/terminal.py`).
In a multi-pod, horizontally scaled Kubernetes or ECS deployment:
1. In-memory session tracking (`CONCURRENT_SESSIONS = set()`) cannot enforce global concurrency limits across nodes.
2. Terminal output streams cannot be broadcast or audited across multiple consumer instances.

## Decision Drivers

* **Cluster-Wide State:** Global concurrency caps must be enforced cluster-wide to protect infrastructure from abuse.
* **Low Latency:** Terminal stdout/stdin streaming must introduce <5ms latency.
* **Graceful Degradation:** The router must continue operating locally in single-node development mode if Redis is temporarily unreachable.

## Decision Outcome

**Chosen Option:** **Redis Distributed Sets (`sadd`/`srem`/`scard`) and PubSub Streaming** (`backend/src/api/routers/terminal.py`).

### Implementation Strategy

1. **Distributed Concurrency Tracking:**
   * Node checks `await redis_client.scard("asep:terminal:sessions")` before spawning a new PTY shell.
   * On session start: `await redis_client.sadd("asep:terminal:sessions", session_id)`.
   * On session cleanup / disconnect: `await redis_client.srem("asep:terminal:sessions", session_id)`.
2. **PubSub Multiplexing:**
   * PTY stdout chunks are published to `asep:terminal:channel:{session_id}` allowing multi-pod WebSocket routing and centralized audit recording.

### Consequences

* **Positive:**
  * Clean horizontal scaling across arbitrarily large container fleets.
  * Zero session leakage or zombie terminal processes.
* **Negative:**
  * Introduces an asynchronous dependency on Redis for full cluster features (with local fallback if offline).

---
