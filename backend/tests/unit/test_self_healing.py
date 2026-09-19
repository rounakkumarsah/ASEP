"""
ASEP — Self-Healing Execution Loop Unit Tests
=============================================
Verifies:
1. Critic Node: Executes code in isolated sandbox, captures stdout/stderr/exit code/trace.
2. Planted Bug Verification: Planted bug (undefined variable) is detected, patched via
   unified diff, and re-run without user intervention until success (exit code 0, tests pass).
3. AST Slicing in Error Context: Failing function is isolated and sliced for the debugger.
4. Attempt History: Debugger consults last 3 attempts to avoid repeating failed patches.
5. Max 5 Retry Limit: Escalates to operator when 5 attempts fail.
6. Execution Trace Logging: Logs formatted as "heal cycle #N: <error> → <fix summary>".
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.self_healing import (
    SandboxRunner,
    SandboxRunResult,
    TracebackAnalyzer,
    SelfHealingDebugger,
    UnifiedDiffPatcher,
    FailingFunctionInfo,
)
from src.runtime.nodes import critic_node, debugger_node, implement_phase_node
from src.runtime.state import AgentState


class TestSandboxRunner:
    """Tests for isolated sandbox execution."""

    def test_successful_code_execution(self):
        code = "def add(a, b):\n    return a + b\n\nprint('Result:', add(2, 3))\n"
        result = SandboxRunner.run_code(code)
        assert result.exit_code == 0
        assert result.success is True
        assert result.tests_passed is True
        assert len(result.warnings) == 0
        assert "Result: 5" in result.stdout

    def test_planted_bug_detection(self):
        # Planted bug: undefined variable
        code = "def multiply(a):\n    return a * factor\n\nprint(multiply(10))\n"
        result = SandboxRunner.run_code(code)
        assert result.exit_code != 0
        assert result.success is False
        assert "NameError" in (result.stack_trace or result.stderr)
        assert "factor" in (result.stack_trace or result.stderr)


class TestTracebackAnalyzer:
    """Tests for traceback parsing and AST slicing of failing frames."""

    def test_traceback_analysis_with_ast_slice(self):
        source_code = (
            "import os\n"
            "def calculate_total(price, tax_rate):\n"
            "    subtotal = price * tax_rate\n"
            "    grand_total = subtotal + surcharge\n"
            "    return grand_total\n"
            "\n"
            "print(calculate_total(100, 0.08))\n"
        )
        run_res = SandboxRunner.run_code(source_code)
        assert run_res.exit_code != 0

        analysis = TracebackAnalyzer.analyze(run_res.stack_trace, source_code)
        assert analysis.error_type == "NameError"
        assert "surcharge" in analysis.error_message
        assert analysis.function_name == "calculate_total"
        assert analysis.line_number == 4
        assert analysis.ast_slice is not None
        assert "def calculate_total" in analysis.ast_slice.sliced_content


class TestUnifiedDiffPatcher:
    """Tests applying unified diff patches."""

    def test_apply_unified_diff(self):
        original = "def greet(name):\n    print('Hello ' + name)\n"
        patch_text = (
            "--- a/main.py\n"
            "+++ b/main.py\n"
            "@@ -1,2 +1,3 @@\n"
            " def greet(name):\n"
            "+    name = name.strip()\n"
            "     print('Hello ' + name)\n"
        )
        patched = UnifiedDiffPatcher.apply_patch(original, patch_text)
        assert "name = name.strip()" in patched
        assert "print('Hello ' + name)" in patched


class TestSelfHealingLoop:
    """Tests autonomous detection, diff-only patching, and re-run with planted bugs."""

    def test_planted_bug_autonomous_heal(self):
        """Planted bug: undefined variable `multiplier`.
        System detects it, patches it with unified diff, and re-runs to exit 0.
        """
        planted_bug_code = (
            "def calculate_tax(amount):\n"
            "    tax = amount * multiplier\n"
            "    return tax\n"
            "\n"
            "print(calculate_tax(500))\n"
        )

        # 1. Critic runs and detects failure
        critic_run_1 = SandboxRunner.run_code(planted_bug_code)
        assert critic_run_1.exit_code != 0
        assert critic_run_1.success is False

        # 2. Traceback analysis extracts failing function and AST slice
        analysis = TracebackAnalyzer.analyze(critic_run_1.stack_trace, planted_bug_code)
        assert analysis.error_type == "NameError"
        assert "multiplier" in analysis.error_message

        # 3. Debugger produces a unified diff patch ONLY
        patch, fix_summary = SelfHealingDebugger.generate_patch(
            source_code=planted_bug_code,
            failing_info=analysis,
            past_attempts=[],
        )
        assert "--- a/main.py" in patch
        assert "+++ b/main.py" in patch
        assert "multiplier" in patch
        assert "multiplier" in fix_summary.lower()

        # 4. Patch is applied
        healed_code = UnifiedDiffPatcher.apply_patch(planted_bug_code, patch)

        # 5. Critic re-runs healed code -> exit code 0, tests pass, 0 warnings
        critic_run_2 = SandboxRunner.run_code(healed_code)
        assert critic_run_2.exit_code == 0
        assert critic_run_2.success is True
        assert critic_run_2.tests_passed is True
        assert len(critic_run_2.warnings) == 0
        assert critic_run_2.stdout.strip() == "500"

    def test_history_avoids_repeating_failed_fixes(self):
        """Verify debugger checks last 3 attempts to avoid repeating failed fixes."""
        source_code = "def worker():\n    return undefined_ref\n"
        failing_info = FailingFunctionInfo(
            error_type="NameError",
            error_message="name 'undefined_ref' is not defined",
            failing_file="main.py",
            line_number=2,
            function_name="worker",
            raw_traceback="...",
        )

        # Attempt 1
        _, summary_1 = SelfHealingDebugger.generate_patch(source_code, failing_info, past_attempts=[])

        # Attempt 2 with attempt 1 in history
        _, summary_2 = SelfHealingDebugger.generate_patch(
            source_code,
            failing_info,
            past_attempts=[{"fix_summary": summary_1}],
        )

        # Summaries must differ (alternative strategy chosen)
        assert summary_1 != summary_2
        assert "Alternative Strategy" in summary_2

    def test_various_error_type_patches(self):
        """Test unified diff patch generation for ZeroDivisionError, KeyError, and SyntaxError."""
        # ZeroDivisionError
        z_info = FailingFunctionInfo(
            error_type="ZeroDivisionError",
            error_message="division by zero",
            failing_file="main.py",
            line_number=2,
            function_name="div",
            raw_traceback="...",
        )
        z_patch, z_sum = SelfHealingDebugger.generate_patch("def div(a, b):\n    return a / b\n", z_info)
        assert "zero" in z_sum.lower()
        assert "--- a/main.py" in z_patch

        # KeyError
        k_info = FailingFunctionInfo(
            error_type="KeyError",
            error_message="'user_id'",
            failing_file="main.py",
            line_number=2,
            function_name="get_user",
            raw_traceback="...",
        )
        k_patch, k_sum = SelfHealingDebugger.generate_patch("def get_user(d):\n    return d['user_id']\n", k_info)
        assert "get('user_id')" in k_patch or "get" in k_sum

    @pytest.mark.asyncio
    async def test_critic_node_and_debugger_node_transitions(self):
        """Test LangGraph node execution: implement -> critic (fails) -> debugger (heals) -> critic (passes)."""
        buggy_code = (
            "def compute(x):\n"
            "    return x * multiplier\n"
            "\n"
            "print(compute(21))\n"
        )

        # State entering critic node with planted bug
        state_1: AgentState = {
            "generated_code": buggy_code,
            "filepath": "main.py",
            "heal_cycle_count": 0,
            "heal_history": [],
            "heal_logs": [],
            "variables": {},
        }

        # 1. Critic node detects bug
        critic_res_1 = await critic_node(state_1)
        assert critic_res_1["status"] == "healing"
        assert "critic_analysis" in critic_res_1["variables"]

        # Merge state for debugger
        state_2: AgentState = {
            **state_1,
            **critic_res_1,
        }

        # 2. Debugger node produces unified diff patch
        debug_res = await debugger_node(state_2)
        assert debug_res["status"] == "retest"
        assert debug_res["heal_cycle_count"] == 1
        assert len(debug_res["heal_logs"]) == 1
        # Format requirement: "heal cycle #N: <error> → <fix summary>"
        assert debug_res["heal_logs"][0].startswith("heal cycle #1: NameError")
        assert "→" in debug_res["heal_logs"][0]

        # Merge state for critic re-test
        state_3: AgentState = {
            **state_2,
            **debug_res,
        }

        # 3. Critic re-tests healed code
        critic_res_2 = await critic_node(state_3)
        assert critic_res_2["status"] == "verified"
        assert any("Sandbox Output" in m["content"] or "passed" in m["content"] for m in critic_res_2["messages"])

    @pytest.mark.asyncio
    async def test_critic_escalation_at_max_retries(self):
        """Test that after 5 retry attempts, critic node transitions to 'escalated'."""
        stubborn_error_code = "raise RuntimeError('Persistent hardware failure')\n"
        state: AgentState = {
            "generated_code": stubborn_error_code,
            "filepath": "main.py",
            "heal_cycle_count": 5,  # Already at max 5
            "heal_history": [{"cycle": i} for i in range(1, 6)],
            "heal_logs": [],
            "variables": {},
        }

        critic_res = await critic_node(state)
        assert critic_res["status"] == "escalated"
        assert "escalation_info" in critic_res
        assert critic_res["escalation_info"]["error_type"] == "RuntimeError"
        assert any("Escalation Required" in m["content"] for m in critic_res["messages"])

    @pytest.mark.asyncio
    async def test_deprecated_fastapi_syntax_online_research_and_heal(self):
        """Test verification: requested code uses deprecated FastAPI syntax (@app.on_event).
        Critic detects deprecation warning / error.
        Debugger performs online research / docs lookup BEFORE patch.
        Execution trace records web search / knowledge query events and citations.
        Debugger applies unified diff patch converting to modern lifespan handler.
        Critic re-tests and passes cleanly (exit code 0).
        """
        deprecated_fastapi_code = (
            "import warnings\n"
            "warnings.simplefilter('error', DeprecationWarning)\n"
            "from fastapi import FastAPI\n"
            "\n"
            "app = FastAPI()\n"
            "\n"
            "@app.on_event('startup')\n"
            "async def startup():\n"
            "    print('FastAPI application started')\n"
            "\n"
            "@app.on_event('shutdown')\n"
            "async def shutdown():\n"
            "    print('FastAPI application stopped')\n"
            "\n"
            "print('App setup completed')\n"
        )

        state_1: AgentState = {
            "generated_code": deprecated_fastapi_code,
            "filepath": "main.py",
            "heal_cycle_count": 0,
            "heal_history": [],
            "heal_logs": [],
            "variables": {},
        }

        # 1. Critic node runs code in sandbox and detects the DeprecationWarning
        critic_res_1 = await critic_node(state_1)
        assert critic_res_1["status"] == "healing"
        assert "critic_analysis" in critic_res_1["variables"]
        analysis = critic_res_1["variables"]["critic_analysis"]
        assert analysis["error_type"] == "DeprecationWarning"
        assert "on_event is deprecated" in analysis["error_message"]

        # 2. Merge state into debugger node
        state_2: AgentState = {
            **state_1,
            **critic_res_1,
        }

        # 3. Debugger node runs: performs online research lookup BEFORE patch
        debug_res = await debugger_node(state_2)
        assert debug_res["status"] == "retest"
        assert debug_res["heal_cycle_count"] == 1

        # Check online research / knowledge query events in messages & execution trace
        messages = debug_res["messages"]
        msg_contents = [m.get("content", "") for m in messages]

        # Must show web search or knowledge query event
        has_web_search = any("[Web Search]" in c for c in msg_contents)
        has_knowledge_query = any("[Knowledge Query]" in c for c in msg_contents)
        has_citation = any("[FROM: https://fastapi.tiangolo.com" in c for c in msg_contents)
        has_explore_search_event = any("[Explore Event]" in c and "search" in c for c in msg_contents)

        assert has_web_search, "Execution Trace must include [Web Search] event"
        assert has_knowledge_query, "Execution Trace must include [Knowledge Query] event"
        assert has_citation, "Execution Trace must include documentation citation [FROM: ...]"
        assert has_explore_search_event, "Explore Feed must receive search ExploreEvent"

        # Check heal log entry formatting with research lookup
        heal_log = debug_res["heal_logs"][0]
        assert "heal cycle #1:" in heal_log
        assert "DeprecationWarning" in heal_log
        assert "[Researched: FastAPI on_event deprecated lifespan" in heal_log
        assert "lifespan" in heal_log.lower()

        # Check the patched code: must be upgraded to modern lifespan handler
        healed_code = debug_res["generated_code"]
        assert "@asynccontextmanager" in healed_code
        assert "async def lifespan(app: FastAPI):" in healed_code
        assert "lifespan=lifespan" in healed_code
        assert "@app.on_event" not in healed_code

        # 4. Merge state and route back to Critic for re-test
        state_3: AgentState = {
            **state_2,
            **debug_res,
        }
        critic_res_2 = await critic_node(state_3)
        assert critic_res_2["status"] == "verified"
        assert critic_res_2["critic_result"]["exit_code"] == 0
        assert critic_res_2["critic_result"]["tests_passed"] is True
        assert len(critic_res_2["critic_result"]["warnings"]) == 0
        assert "App setup completed" in critic_res_2["critic_result"]["stdout"]
