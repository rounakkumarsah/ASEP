"""
ASEP — Token Efficiency Unit Tests
==================================
Verifies AST Slicing, Diff-Only Streaming, and Per-Phase Token Budget Enforcement.
Specifically tests modifying one function in a 500-line file and confirming
the agent receives ONLY that function's AST slice in logs and payloads.
"""

import pytest
import json
from src.utils.ast_slicer import ASTSlicer, estimate_tokens
from src.utils.diff_streamer import DiffStreamer
from src.utils.token_manager import TokenBudgetManager, DEFAULT_PHASE_BUDGETS
from src.runtime.nodes import (
    execute_phase_token_guard,
    orchestrator_node,
    implement_phase_node,
)


def _generate_500_line_file() -> str:
    """Generate a realistic 500-line Python service with 15 functions."""
    lines = [
        "\"\"\"Enterprise Transaction Processing Service.\"\"\"",
        "import os",
        "import sys",
        "import logging",
        "from typing import Any, Optional",
        "",
        "logger = logging.getLogger(__name__)",
        "",
    ]

    for i in range(1, 15):
        if i == 7:
            # Target function to modify
            lines.append("def process_payment(account_id: str, amount: float, currency: str = 'USD') -> dict[str, Any]:")
            lines.append("    \"\"\"Execute credit card payment through merchant gateway.\"\"\"")
            lines.append("    logger.info(f'Authorizing charge for {account_id}: {amount} {currency}')")
            lines.append("    if amount <= 0:")
            lines.append("        raise ValueError('Payment amount must be positive')")
            lines.append("    fee = amount * 0.029 + 0.30")
            lines.append("    net_amount = round(amount - fee, 2)")
            lines.append("    status = 'settled' if amount < 10000 else 'flagged_review'")
            lines.append("    return {")
            lines.append("        'account_id': account_id,")
            lines.append("        'gross_amount': amount,")
            lines.append("        'net_amount': net_amount,")
            lines.append("        'fee': fee,")
            lines.append("        'currency': currency,")
            lines.append("        'status': status,")
            lines.append("    }")
            lines.append("")
        else:
            lines.append(f"def auxiliary_helper_task_{i}(payload: dict[str, Any], flag: bool = True) -> list[str]:")
            lines.append(f"    \"\"\"Auxiliary processing function number {i}.\"\"\"")
            lines.append(f"    results = []")
            for step in range(1, 25):
                lines.append(f"    # Calculation step {step} for pipeline worker {i}")
                lines.append(f"    val_{step} = payload.get('field_{step}', {step} * 100)")
                lines.append(f"    results.append(str(val_{step} * {i}))")
            lines.append(f"    return results")
            lines.append("")

    return "\n".join(lines)


class TestASTSlicer:
    """Verifies AST Slicing eliminates redundant code context."""

    def test_500_line_file_ast_slice_targeting_single_function(self):
        """Test: Modify one function in a 500-line file and confirm agent receives only that AST slice."""
        code_500 = _generate_500_line_file()
        total_lines = code_500.count("\n") + 1
        assert total_lines >= 500, f"Expected >= 500 lines, got {total_lines}"

        # Slice targeting process_payment
        slice_result = ASTSlicer.slice_code(
            source_code=code_500,
            filename="payment_service.py",
            target_symbol="process_payment",
        )

        assert slice_result.is_sliced is True
        assert slice_result.original_lines >= 500
        assert slice_result.sliced_lines < 40, f"Expected < 40 lines, got {slice_result.sliced_lines}"
        assert slice_result.token_reduction_pct > 85.0

        # Verify exact symbol containment
        assert "def process_payment" in slice_result.sliced_content
        assert "auxiliary_helper_task_1" not in slice_result.sliced_content
        assert "auxiliary_helper_task_14" not in slice_result.sliced_content
        assert "payment_service.py" in slice_result.sliced_content
        assert "AST Slice: process_payment" in slice_result.sliced_content
        assert slice_result.extracted_symbols == ["process_payment"]

    def test_ast_slice_with_changed_lines(self):
        """Test slicing by changed line numbers."""
        code = (
            "def alpha():\n    return 1\n\n"
            "def beta():\n    x = 10\n    y = 20\n    return x + y\n\n"
            "def gamma():\n    return 3\n"
        )
        res = ASTSlicer.slice_code(code, "test.py", changed_lines=[5])
        assert res.is_sliced is True
        assert "def beta" in res.sliced_content
        assert "def alpha" not in res.sliced_content
        assert "def gamma" not in res.sliced_content


class TestDiffStreamer:
    """Verifies Diff-Only Streaming converts subsequent updates to unified diffs."""

    def test_diff_only_streaming_lifecycle(self):
        streamer = DiffStreamer()
        file_path = "backend/src/payments.py"

        # Larger file so diff is smaller than full file
        v1 = "def pay():\n    # initial implementation\n" + "\n".join(f"    line_{i} = {i}" for i in range(50)) + "\n    return 'v1'\n"
        v2 = "def pay():\n    # initial implementation\n" + "\n".join(f"    line_{i} = {i}" for i in range(50)) + "\n    return 'v2_updated'\n"

        # Revision 1: initial version transmitted fully
        res1 = streamer.process_file_content(file_path, v1)
        assert res1.is_diff is False
        assert "DIFF STREAM INITIAL" in res1.payload
        assert "return 'v1'" in res1.payload

        # Revision 2: subsequent version transmitted strictly as unified diff
        res2 = streamer.process_file_content(file_path, v2)
        assert res2.is_diff is True
        assert "DIFF-ONLY STREAM ACTIVE" in res2.payload
        assert "--- a/backend/src/payments.py" in res2.payload
        assert "+++ b/backend/src/payments.py" in res2.payload
        assert "-    return 'v1'" in res2.payload
        assert "+    return 'v2_updated'" in res2.payload
        assert res2.tokens_saved > 0


class TestTokenBudgetManager:
    """Verifies per-phase token budgets and over-budget pause interrupts."""

    def test_budget_within_limits(self):
        status = TokenBudgetManager.evaluate_phase_budget(
            phase="research",
            tokens_to_add=500,
            usage_map={"research": 200},
        )
        assert status.is_exceeded is False
        assert status.interrupt_required is False
        assert status.tokens_used == 700

    def test_budget_exceeded_triggers_interrupt(self):
        # Default implement budget is 3500
        status = TokenBudgetManager.evaluate_phase_budget(
            phase="implement",
            tokens_to_add=4000,
            usage_map={"implement": 0},
        )
        assert status.is_exceeded is True
        assert status.interrupt_required is True
        assert "[Token Budget Exceeded]" in (status.prompt_message or "")
        assert "implement" in (status.prompt_message or "")

    def test_pre_approved_budget_does_not_interrupt(self):
        status = TokenBudgetManager.evaluate_phase_budget(
            phase="implement",
            tokens_to_add=4500,
            usage_map={"implement": 0},
            approvals=["implement"],
        )
        assert status.is_exceeded is True
        assert status.is_approved is True
        assert status.interrupt_required is False

    def test_comparison_breakdown(self):
        breakdown = TokenBudgetManager.get_comparison_breakdown(
            usage_map={"research": 150, "implement": 3800},
        )
        assert len(breakdown) >= 2
        implement_row = next(r for r in breakdown if r["phase"] == "implement")
        assert implement_row["status"] == "exceeded"
        assert implement_row["used"] == 3800


@pytest.mark.asyncio
class TestNodeTokenEfficiencyIntegration:
    """Tests orchestrator and implement phase nodes with token efficiency."""

    async def test_orchestrator_initializes_token_telemetry(self):
        state = {"goal": "Build payment microservice", "variables": {}}
        out = await orchestrator_node(state)
        assert "token_budget_per_phase" in out
        assert "token_usage_per_phase" in out
        assert "token_savings" in out
        msg_contents = [m["content"] for m in out["messages"]]
        assert any("[Token Budgets]" in c for c in msg_contents)
        assert any("[Token Usage]" in c for c in msg_contents)
        assert any("[Token Savings]" in c for c in msg_contents)

    async def test_implement_node_receives_only_ast_slice(self):
        """Confirm implement_phase_node receives only the AST slice when given a 500-line file."""
        code_500 = _generate_500_line_file()
        state = {
            "goal": "Update payment processor",
            "code_context": code_500,
            "target_symbol": "process_payment",
            "filepath": "payment_service.py",
            "token_budget_per_phase": DEFAULT_PHASE_BUDGETS.copy(),
            "token_usage_per_phase": {},
            "token_savings": {"ast_slicing": 0, "diff_streaming": 0, "total_saved": 0},
            "file_history": {},
            "budget_approvals": [],
        }

        result = await implement_phase_node(state)
        assert result["status"] == "verified"
        assert result["current_phase"] == "implement"
        assert result["token_savings"]["ast_slicing"] > 500

        # Verify assistant message only contains the AST slice, not 500 lines!
        assistant_msgs = [m["content"] for m in result["messages"] if m.get("role") == "assistant"]
        assert len(assistant_msgs) > 0
        code_payload = assistant_msgs[0]
        assert "def process_payment" in code_payload
        assert "auxiliary_helper_task_1" not in code_payload
        assert "auxiliary_helper_task_14" not in code_payload
        assert code_payload.count("\n") < 50
