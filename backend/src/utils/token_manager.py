"""
ASEP — Token Manager & Per-Phase Budget System
==============================================
Provides centralized token tracking, per-phase budget enforcement,
over-budget interrupt generation, and efficiency comparison metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.utils.ast_slicer import estimate_tokens

logger = logging.getLogger(__name__)

# Default token quotas per workflow phase
DEFAULT_PHASE_BUDGETS: dict[str, int] = {
    "research": 1500,
    "clarification_gate": 500,
    "blueprint": 2000,
    "scaffold": 2500,
    "implement": 3500,
    "critic": 1500,
    "debugger": 2500,
    "test": 2000,
    "security_audit": 1500,
    "deploy_clarification_gate": 500,
    "deploy": 1000,
    "host_manager": 500,
    # Dynamic agentic phase budgets
    "capability_blueprint": 2000,
    "tool_design": 2000,
    "agent_loop_implementation": 3500,
    "memory_state_design": 2000,
    "sandbox_tests": 2500,
    "evaluation_runs": 2500,
    "goal_decomposition_design": 2000,
    "planner_executor_critic_architecture": 2500,
    "tool_integration": 2500,
    "multi_step_test_scenarios": 2500,
    "failure_recovery_tests": 2000,
    "workflow_mapping": 2000,
    "trigger_action_design": 2000,
    "integration_points": 2500,
    "end_to_end_automation_tests": 2500,
    "error_handling_paths": 2000,
}


@dataclass
class PhaseBudgetStatus:
    """Detailed status of a phase's token budget."""
    phase: str
    tokens_used: int
    budget: int
    percent_used: float
    is_exceeded: bool
    is_approved: bool
    interrupt_required: bool
    prompt_message: str | None = None


class TokenBudgetManager:
    """Tracks token expenditures across execution phases and enforces budgets."""

    @classmethod
    def evaluate_phase_budget(
        cls,
        phase: str,
        tokens_to_add: int,
        usage_map: dict[str, int] | None = None,
        budget_map: dict[str, int] | None = None,
        approvals: list[str] | None = None,
    ) -> PhaseBudgetStatus:
        """Evaluates whether adding tokens to a phase exceeds its budget.

        If exceeded and not pre-approved, flags that an orchestrator interrupt is required.
        """
        usage = dict(usage_map or {})
        budgets = dict(budget_map or DEFAULT_PHASE_BUDGETS)
        approved_phases = set(approvals or [])

        phase_budget = budgets.get(phase, DEFAULT_PHASE_BUDGETS.get(phase, 2500))
        current_used = usage.get(phase, 0)
        new_total = current_used + tokens_to_add
        percent_used = round((new_total / max(1, phase_budget)) * 100.0, 1)

        is_exceeded = new_total > phase_budget
        is_approved = phase in approved_phases
        interrupt_required = is_exceeded and not is_approved

        prompt_msg = None
        if interrupt_required:
            prompt_msg = (
                f"[Token Budget Exceeded] Phase '{phase}' consumed {new_total} tokens "
                f"(allocated budget: {phase_budget}, {percent_used}%). "
                f"Please approve budget continuation to proceed with execution."
            )

        return PhaseBudgetStatus(
            phase=phase,
            tokens_used=new_total,
            budget=phase_budget,
            percent_used=percent_used,
            is_exceeded=is_exceeded,
            is_approved=is_approved,
            interrupt_required=interrupt_required,
            prompt_message=prompt_msg,
        )

    @classmethod
    def get_comparison_breakdown(
        cls,
        usage_map: dict[str, int],
        budget_map: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Generates comparison chart telemetry rows for all phases."""
        budgets = dict(budget_map or DEFAULT_PHASE_BUDGETS)
        all_phases = list(dict.fromkeys(list(budgets.keys()) + list(usage_map.keys())))

        breakdown = []
        for p in all_phases:
            used = usage_map.get(p, 0)
            budget = budgets.get(p, DEFAULT_PHASE_BUDGETS.get(p, 2500))
            ratio = round((used / max(1, budget)) * 100.0, 1)
            breakdown.append({
                "phase": p,
                "label": p.replace("_", " ").title(),
                "used": used,
                "budget": budget,
                "percent": ratio,
                "status": "exceeded" if used > budget else "healthy" if ratio < 85 else "warning",
            })
        return breakdown
