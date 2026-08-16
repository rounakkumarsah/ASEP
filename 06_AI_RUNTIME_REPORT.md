# 06 — AI Runtime & Agent Orchestration Forensic Report: ASEP

**Audit Date**: August 2026  
**Methodology**: Inspection of `backend/src/ai_runtime/`, `backend/src/agents/`, and `backend/src/tools/`.

---

## 1. Unified AI Provider Abstraction

Implemented in `backend/src/ai_runtime/service.py` (`AIRuntimeService`).

### 1.1 Polymorphic Providers (`backend/src/ai_runtime/providers/`)
1. **`GeminiProvider` (`gemini.py`)**:
   - SDK: `google-generativeai`
   - Models: `gemini-1.5-pro`, `gemini-1.5-flash`
   - Capabilities: Native function calling, streaming tokens, multi-modal context
2. **`OpenAIProvider` (`openai.py`)**:
   - SDK: `openai`
   - Models: `gpt-4o`, `gpt-4o-mini`, `o1-preview`, `text-embedding-3-small`
   - Capabilities: Structured outputs, JSON mode, function calling
3. **`OllamaProvider` (`ollama.py`)**:
   - Protocol: HTTP REST (`http://localhost:11434/api/chat`)
   - Models: `llama3.1`, `qwen2.5-coder`, `mistral`, `deepseek-coder`
   - Capabilities: Air-gapped, zero external network dependency
4. **`MockProvider` (`mock.py`)**:
   - Deterministic test harness for pytest suites and CI/CD runs

---

## 2. Multi-Agent Graph Architecture (LangGraph)

Implemented in `backend/src/agents/`:
- **`AgentSupervisor` (`supervisor.py`)**: Top-level coordinator routing tasks between Planner, Research Swarm, and Executor.
- **`DeconstructionPlanner` (`planner.py`)**: Decomposes high-level natural language goals into a directed acyclic task graph with explicit dependency mapping.
- **`ResearchSwarm` (`research_swarm.py`)**: Specialized agents querying documentation, vector RAG, and AST graphs.
- **`State Management` (`state.py`)**: State graphs preserving intermediate execution steps and artifact outputs.

---

## 3. Tool Execution & MCP Integration

Implemented in `backend/src/tools/`:
- **`MCPClient` (`mcp_client.py`)**: Implements Anthropic Model Context Protocol v1.0 standard for dynamic discovery and execution of external tools.
- **`ToolRegistry` (`registry.py`)**: Scopes and enforces tool execution permissions.
- **`Native Sandboxed Tools` (`impl.py`)**:
  - `read_file`, `write_file`, `replace_content`, `list_directory`
  - `execute_shell_command` (Docker container isolated)
  - `git_commit`, `git_create_branch`, `git_checkout`, `git_push`
  - `run_tests` (Automated pytest / vitest runner)
