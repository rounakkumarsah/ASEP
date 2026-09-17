"""
ASEP — Typed LangGraph State
"""

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    """The central state schema for the agent execution graph."""

    # Core input
    goal: str

    # Message history list, accumulated on each state transition
    messages: Annotated[list[dict[str, Any]], operator.add]

    # Decomposed subtasks / plan
    plan: list[str]

    # Current status of the runner (e.g. "started", "planning", "researching", "rag", "coding", "paused", "completed")
    status: str

    # Next node or routing instruction
    next_action: str | None

    # Execution ID linking to AgentRun/Task
    run_id: str

    # Model choice
    model: str

    # Transient variables and outputs (MCP results, RAG chunks, code artifacts)
    variables: dict[str, Any]

    # Human input / interrupt response payload
    human_input: str | None

    # --- Core Multi-Agent Architecture Schema ---
    product_type: str
    phase_map: list[str]
    current_phase: str
    artifacts: dict[str, Any]
    test_results: dict[str, Any]
    error_log: list[str]
    security_report: dict[str, Any]
    # Token Efficiency & Per-Phase Budgeting
    token_usage_per_phase: dict[str, int]
    token_budget_per_phase: dict[str, int]
    file_history: dict[str, str]
    budget_approvals: list[str]
    budget_exceeded_info: dict[str, Any]
    token_savings: dict[str, int]

    # Environment Policy
    environment_mode: str
    credentials_status: dict[str, Any]
    local_secrets: list[str]

    # Self-Healing Execution Loop Schema
    generated_code: str
    critic_result: dict[str, Any]
    heal_cycle_count: int
    heal_history: list[dict[str, Any]]
    heal_logs: list[str]
    escalation_info: dict[str, Any]
    target_symbol: str
    changed_lines: list[int]
    code_context: str
    filepath: str
    file_content: str

    # --- Autonomous Research Agent ---
    # TTL-cached doc chunks per project+product_type: key = f"{project_id}:{product_type}"
    doc_cache: dict[str, Any]
    # Official documentation URLs actually crawled this run
    knowledge_sources: list[str]
    # Discovered stable version hints: {"fastapi": "0.115.x", ...}
    stack_versions: dict[str, str]

    # --- Host Manager ---
    # Result of the host manager phase: {port, url, pid, health_ok, ...}
    hosted_app: dict[str, Any]
    # Assigned port for the running app (0 = not hosted)
    app_port: int
    # Live URL exposed to user e.g. "http://localhost:3000"
    app_url: str
    # Install step executed e.g. "pip install fastapi uvicorn"
    install_step: str
    # Host manager phase logs
    host_logs: list[str]

    # --- GitHub Sync Engine ---
    github_repo: str
    github_branch: str
    github_commits: dict[str, str]
    github_sync_status: str
    github_pr_url: str

    # --- Skill System ---
    active_skills: list[str]
    skill_instructions: list[str]
    skill_citations: list[str]
    forced_skills: list[str]
    disabled_skills: list[str]

    # --- Live Exploration Feed ---
    exploration_events: list[dict[str, Any]]
    exploration_summary: dict[str, Any]
    phase_explorations: dict[str, dict[str, Any]]
    explored_files: list[str]

