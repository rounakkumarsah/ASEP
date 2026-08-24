# ADR 0001: LangGraph Multi-Agent Orchestration Architecture

* **Status:** Accepted  
* **Date:** 2026-08-24  
* **Deciders:** Principal Architect & Platform Lead (Rounak Kumar Sah)  
* **Context:** Choosing an orchestration framework for multi-agent autonomous software engineering.

---

## Context and Problem Statement

Autonomous software engineering requires coordinating multiple specialized agents (Planner, Research Swarm, Code Writer, Code Reviewer, Test Runner) across multi-step execution graphs. Unstructured agent loops (such as ReAct loops in AutoGen or CrewAI) often suffer from non-deterministic execution, infinite loops, lack of checkpoint durability, and high failure rates on complex engineering goals.

## Decision Drivers

* **Determinism:** Execution transitions must follow explicit, bounded StateGraph edges.
* **Durability:** Every state mutation must be serializable and persistable to PostgreSQL/Redis for checkpointing, time-travel debugging, and Human-in-the-Loop interruptions.
* **Observability:** Granular node-level tracing with token consumption and latency metrics.

## Considered Options

1. **Custom ReAct Loop:** Basic Python `while True` loop calling LLMs.
2. **CrewAI / AutoGen:** Process-driven role-play agent frameworks.
3. **LangGraph StateGraph DAG:** Graph-based deterministic execution with compiled states and interrupt primitives.

## Decision Outcome

**Chosen Option:** **LangGraph StateGraph DAG** (`backend/src/agents/supervisor.py`, `backend/src/runtime/graph.py`).

### Consequences

* **Positive:**
  * Native support for Human-in-the-Loop pause and resume (`interrupt()`).
  * Checkpoint persistence to PostgreSQL (`PostgresSaver`) allowing server restarts without losing agent state.
  * Graph compilation prevents uncontrolled execution loops.
* **Negative:**
  * Requires strict typed state schemas (`TypedDict` with `operator.add` reducers).

---
