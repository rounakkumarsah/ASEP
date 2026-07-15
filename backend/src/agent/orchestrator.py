"""
ASEP — Agent Orchestrator

Coordinates the Planner → Executor → ToolRouter lifecycle.
The Executor interacts with the ToolRouter exclusively through the HandlerRegistry adapter.
"""

import logging
from typing import TYPE_CHECKING, AsyncGenerator

from src.executor.dispatcher import HandlerRegistry
from src.executor.executor import Executor
from src.executor.result import ProgressEvent
from src.executor.retries import RetryPolicy
from src.planner.models import DecomposedPlan
from src.tools.schemas import ToolExecutionOutput

if TYPE_CHECKING:
    from src.agent.session import AgentSession
    from src.memory.memory_manager import MemoryManager
    from src.planner.planner import Planner
    from src.tools.router import ToolRouter

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinates Planner and Executor, wiring the ToolRouter through a HandlerRegistry adapter.

    Design constraints enforced here:
      - The Executor NEVER touches ToolRouter directly.
      - The plan is NEVER modified after planning.
      - All memory interactions go through MemoryManager.
    """

    def __init__(
        self,
        planner: "Planner",
        memory_manager: "MemoryManager",
        tool_router: "ToolRouter",
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._planner = planner
        self._memory = memory_manager
        self._tool_router = tool_router
        self._retry_policy = retry_policy or RetryPolicy()
        self._executor: Executor | None = None

    # ──────────────────────────────────────────────────────────────────────────
    # Planning
    # ──────────────────────────────────────────────────────────────────────────

    async def plan(self, enriched_goal: str) -> DecomposedPlan:
        """Run the Planner to produce a validated, topologically-sorted DecomposedPlan."""
        logger.info("Orchestrator: invoking Planner")
        return await self._planner.create_plan(enriched_goal)

    # ──────────────────────────────────────────────────────────────────────────
    # Execution
    # ──────────────────────────────────────────────────────────────────────────

    async def execute(
        self,
        plan: DecomposedPlan,
        session: "AgentSession",
        granted_permissions: list[str],
    ) -> AsyncGenerator[ProgressEvent, None]:
        """Stream ProgressEvents by running the Executor with a ToolRouter-backed HandlerRegistry."""
        registry = self._build_handler_registry(granted_permissions)

        self._executor = Executor(
            plan=plan,
            memory_manager=self._memory,
            run_id=session.run_id,
            handler_registry=registry,
            retry_policy=self._retry_policy,
        )

        async for event in self._executor.execute():
            yield event

    # ──────────────────────────────────────────────────────────────────────────
    # Control surface (delegated to active Executor)
    # ──────────────────────────────────────────────────────────────────────────

    def pause(self) -> None:
        if self._executor:
            self._executor.pause()

    def resume(self) -> None:
        if self._executor:
            self._executor.resume()

    def cancel(self) -> None:
        if self._executor:
            self._executor.cancel()

    # ──────────────────────────────────────────────────────────────────────────
    # Internal — ToolRouter adapter
    # ──────────────────────────────────────────────────────────────────────────

    def _build_handler_registry(self, granted_permissions: list[str]) -> HandlerRegistry:
        """Build a HandlerRegistry whose default handler resolves tools via task metadata.

        Resolution strategy: use `task.tool_name` if set; otherwise succeed immediately
        with a noop payload (no tool configured for this task).
        """
        tool_router = self._tool_router

        async def tool_router_handler(task, context) -> dict:
            tool_name: str | None = getattr(task, "tool_name", None)
            if not tool_name:
                logger.debug(f"[{task.id}] No tool_name configured — noop execution")
                return {"noop": True, "task_id": task.id}

            logger.info(f"[{task.id}] Invoking tool '{tool_name}' via ToolRouter")
            result: ToolExecutionOutput = await tool_router.execute(
                tool_name=tool_name,
                arguments={"task": task.model_dump()},
                granted_permissions=granted_permissions,
            )
            return result.model_dump()

        registry = HandlerRegistry(default_handler=tool_router_handler)
        return registry
