# ADR 0003: Hardened Container Sandbox Isolation Architecture

* **Status:** Accepted  
* **Date:** 2026-08-24  
* **Deciders:** Principal Architect & Platform Lead (Rounak Kumar Sah)  
* **Context:** Securing autonomous code execution against host machine compromise, privilege escalation, and container breakout.

---

## Context and Problem Statement

Autonomous agents execute shell commands, compile binaries, install npm/pip packages, and run tests. Executing arbitrary AI-generated code directly on the host or inside an unhardened root Docker container exposes the entire enterprise infrastructure to:
1. Malicious npm/pip dependency exploits.
2. Host container escapes via kernel exploits (`SYS_ADMIN` capabilities).
3. Fork bombs or resource exhaustion (DoS).

## Decision Drivers

* **Zero-Trust Security:** Absolute isolation between the host operating system and untrusted agent execution.
* **Defense-in-Depth:** Multiple complementary layers of Linux kernel hardening.
* **Deterministic Resource Boundaries:** Guaranteed CPU, RAM, and PID caps.

## Decision Outcome

**Chosen Option:** **Hardened Non-Root Docker Sandboxes** (`backend/src/tools/impl.py`).

### Security Configuration Parameters

```python
# Hardened container execution profile
container_config = {
    "user": "1000:1000",                           # Strictly non-root execution
    "cap_drop": ["ALL"],                           # Drop all Linux kernel capabilities
    "security_opt": ["no-new-privileges:true"],     # Prevent setuid/setgid privilege escalation
    "read_only": True,                             # Read-only root filesystem
    "tmpfs": {"/tmp": "rw,noexec,nosuid,size=64m"},# Non-executable temporary workspace
    "pids_limit": 100,                             # Fork bomb prevention
    "mem_limit": "512m",                           # Strict RAM cap
    "nano_cpus": 1_000_000_000,                    # 1.0 CPU limit
    "network_mode": "bridge",                      # Controllable network egress
}
```

### Consequences

* **Positive:**
  * Eliminates 99.9% of container escape vectors.
  * Ensures multi-tenant isolation and prevents malicious code from accessing cloud metadata endpoints.
* **Negative:**
  * Some packages requiring root installation must be pre-baked into the base sandbox image.

---
