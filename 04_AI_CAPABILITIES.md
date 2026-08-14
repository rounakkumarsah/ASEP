# 04 — AI Capabilities & Agent Architecture: ASEP

This document catalogs all AI components, agent models, prompt systems, tool schemas, and runtime pipelines implemented in the ASEP platform.

---

## 1. LLM Provider Infrastructure

The AI runtime (`backend/src/ai_runtime/service.py`) dynamically routes requests to 4 distinct backend providers:

1. **Google Gemini Provider** (`backend/src/ai_runtime/providers/gemini.py`):
   - Supports `gemini-1.5-pro` and `gemini-1.5-flash`.
   - Streaming token responses and structured JSON tool-call support.
   - Long-context window ingestion for repository-scale context.
2. **OpenAI Provider** (`backend/src/ai_runtime/providers/openai.py`):
   - Supports `gpt-4o`, `gpt-4o-mini`, and `o1-preview`.
   - Native OpenAI function calling and embedding models (`text-embedding-3-small`).
3. **Ollama Provider (Local LLMs)** (`backend/src/ai_runtime/providers/ollama.py`):
   - Enables air-gapped, zero-data-retention enterprise deployments.
   - Connects to local endpoints (`http://localhost:11434`) running `llama3.1`, `qwen2.5-coder`, `mistral`, or `deepseek-coder`.
4. **Mock Provider** (`backend/src/ai_runtime/providers/mock.py`):
   - Deterministic test harness for CI/CD test automation without API expenses.

---

## 2. Multi-Agent Graph Architecture (LangGraph)

Implemented under `backend/src/agents/`:

```
                    ┌─────────────────────────┐
                    │    User Prompt / Goal   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Deconstruction        │
                    │   Planner (DAG Node)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
         ┌─────────────────────┐   ┌─────────────────────┐
         │   Research Swarm    │   │  Executor Agent     │
         │  (Context & Docs)   │   │  (Docker Sandbox)   │
         └──────────┬──────────┘   └──────────┬──────────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Governance Guardrail   │◄── [HITL Approval if Destructive]
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Evaluation & Scorer   │
                    └─────────────────────────┘
```

- **Supervisor Agent** (`supervisor.py`): Top-level state machine assigning tasks to specialized subagents.
- **Deconstruction Planner** (`planner.py`): Analyzes repository structure, identifies file dependencies, and constructs sequential/parallel subtasks.
- **Research Swarm** (`research_swarm.py`): Specialized workers that execute vector similarity searches, inspect API documentation, and retrieve context.

---

## 3. Tool Execution & MCP Integration

Implemented under `backend/src/tools/`:
- **Model Context Protocol (MCP)**: Standard client integration (`mcp_client.py`) discovering and executing tools exposed by external MCP servers.
- **Native Implemented Tools** (`impl.py`):
  - `read_file`, `write_file`, `replace_content`, `list_directory`.
  - `execute_shell_command`: Sandboxed command runner with stdout/stderr capture and exit code validation.
  - `git_commit`, `git_create_branch`, `git_checkout`, `git_push`.
  - `run_tests`: Automated pytest / npm test execution.

---

## 4. Multi-Layer Memory & RAG Retrieval

- **Episodic Memory**: Captures historical user interactions, past error resolutions, and debug traces.
- **Semantic Memory**: Cosine similarity vector search in Qdrant with score thresholds &ge;0.75.
- **Procedural Memory**: Rule sets, coding standards, and repository AST relationships mapped into Neo4j graph nodes.
