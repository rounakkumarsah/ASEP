"""
ASEP — Single Autonomous Agent Facade

The Agent is the single entry-point for autonomous goal execution.
It orchestrates the full lifecycle: session → context → reasoning → planning → execution → memory.

Design constraints:
  - No multi-agent, delegation, supervisor, or swarm patterns.
  - No reflection or self-improvement loops.
  - Permissions are resolved from the RBAC layer, not from caller parameters.
  - All memory interactions go through MemoryManager.
  - Executor interacts with ToolRouter only through the HandlerRegistry adapter.
  - Every agent session maps 1:1 to a LangGraph thread_id for checkpoint/resume support.
"""

import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from src.agent.context_builder import ContextBuilder, ContextSnapshot
from src.agent.events import AgentEvent, AgentEventType, make_event
from src.agent.orchestrator import AgentOrchestrator
from src.agent.reasoning import ReasoningEngine
from src.agent.session import AgentSession, SessionManager
from src.agent.state import AgentSessionStatus
from src.auth.policies import ROLE_PERMISSIONS
from src.auth.roles import Role
from src.executor.result import TaskStatus
from src.memory.memory_manager import MemoryManager
from src.planner.planner import Planner
from src.tools.discovery import ToolDiscovery
from src.tools.permissions import ToolPermission
from src.tools.router import ToolRouter

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# RBAC → Tool permission scope mapping
# ─────────────────────────────────────────────────────────────────────────────

# Maps RBAC Role to the set of tool-level permission scopes the agent may use.
# This is intentionally conservative: tool permissions are separate from API permissions.
_ROLE_TOOL_PERMISSIONS: dict[Role, list[str]] = {
    Role.VIEWER:    [],
    Role.OPERATOR:  [ToolPermission.SYS_INFO],
    Role.DEVELOPER: [ToolPermission.SYS_INFO, ToolPermission.FS_READ],
    Role.ADMIN:     [ToolPermission.SYS_INFO, ToolPermission.FS_READ, ToolPermission.FS_WRITE, ToolPermission.WEB_SEARCH],
    Role.SYSTEM:    [ToolPermission.SYS_INFO, ToolPermission.FS_READ, ToolPermission.FS_WRITE, ToolPermission.WEB_SEARCH],
}


def _resolve_tool_permissions(role: Role) -> list[str]:
    """Derive the agent's allowed tool permission scopes from the user's RBAC role."""
    return _ROLE_TOOL_PERMISSIONS.get(role, [])


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────

class Agent:
    """Single autonomous agent driving goal → plan → execution with full memory integration.

    Usage::

        agent = Agent(memory_manager=mm, planner=p, tool_router=tr, tool_discovery=td)

        async for event in agent.run(goal="Analyse the codebase", user_role=Role.DEVELOPER):
            print(event.event_type, event.payload)
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        planner: Planner,
        tool_router: ToolRouter,
        tool_discovery: ToolDiscovery,
    ) -> None:
        self._memory = memory_manager
        self._session_manager = SessionManager(memory_manager)
        self._context_builder = ContextBuilder(memory_manager, tool_discovery)
        self._reasoning = ReasoningEngine()
        self._orchestrator = AgentOrchestrator(
            planner=planner,
            memory_manager=memory_manager,
            tool_router=tool_router,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────────────────────────

    async def run(
        self,
        goal: str,
        user_role: Role = Role.OPERATOR,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Execute a goal end-to-end, yielding strongly typed AgentEvents.

        Lifecycle:
          1. Create session (working memory) → SESSION_STARTED
          2. Build context (4 memory layers + tool catalog) → CONTEXT_BUILT
          3. Enrich goal + assemble planner prompt (ReasoningEngine — no LLM)
          4. Plan (Planner → LLM) → PLAN_CREATED
          5. Execute (Executor + ToolRouter via HandlerRegistry) → TASK_* events
          6. Write episodic session summary → MEMORY_UPDATED
          7. SESSION_COMPLETED / SESSION_FAILED / SESSION_CANCELLED
        """
        # ── 1. Session ───────────────────────────────────────────────────────
        session = await self._session_manager.create_session(goal)
        await self._session_manager.update_status(session, AgentSessionStatus.IDLE)

        granted_permissions = _resolve_tool_permissions(user_role)

        yield make_event(
            AgentEventType.SESSION_STARTED,
            session.session_id,
            run_id=session.run_id,
            thread_id=session.thread_id,
            goal=goal,
            user_role=user_role.value,
            granted_tool_permissions=granted_permissions,
        )

        try:
            # ── 2. Context ───────────────────────────────────────────────────
            context: ContextSnapshot = await self._context_builder.build(
                goal=goal, session_id=session.session_id
            )
            yield make_event(
                AgentEventType.CONTEXT_BUILT,
                session.session_id,
                episodes=len(context.recent_episodes),
                concepts=len(context.relevant_concepts),
                procedures=len(context.relevant_procedures),
                tools=len(context.available_tools),
            )

            # ── 3. Reasoning — pure string enrichment, no LLM ───────────────
            enriched_goal = self._reasoning.enrich_goal(goal, context)
            planner_prompt = self._reasoning.build_planner_prompt(enriched_goal, context)

            # ── 4. Plan ──────────────────────────────────────────────────────
            await self._session_manager.update_status(session, AgentSessionStatus.PLANNING)
            plan = await self._orchestrator.plan(planner_prompt)

            yield make_event(
                AgentEventType.PLAN_CREATED,
                session.session_id,
                task_count=len(plan.tasks),
                rationale=plan.rationale,
                tasks=[{"id": t.id, "title": t.title, "tool_name": t.tool_name} for t in plan.tasks],
            )

            # Record plan in episodic memory
            try:
                await self._memory.episodic.record(
                    session_id=session.session_id,
                    content=f"Plan created with {len(plan.tasks)} tasks: {plan.rationale}",
                    memory_type="episodic",
                )
                yield make_event(AgentEventType.MEMORY_UPDATED, session.session_id, layer="episodic", event="plan_recorded")
            except Exception as exc:
                logger.warning(f"[{session.session_id}] Failed to record plan in episodic memory: {exc}")

            # ── 5. Execute ───────────────────────────────────────────────────
            await self._session_manager.update_status(session, AgentSessionStatus.EXECUTING)

            async for progress_event in self._orchestrator.execute(plan, session, granted_permissions):
                # Map ProgressEvents → AgentEvents
                event_type_map = {
                    "task_started":   AgentEventType.TASK_STARTED,
                    "task_succeeded": AgentEventType.TASK_COMPLETED,
                    "task_failed":    AgentEventType.TASK_FAILED,
                    "task_skipped":   AgentEventType.TASK_SKIPPED,
                    "plan_completed": None,   # handled below
                }
                mapped = event_type_map.get(progress_event.event_type)
                if mapped:
                    yield make_event(
                        mapped,
                        session.session_id,
                        task_id=progress_event.task_id,
                        status=progress_event.status.value if progress_event.status else None,
                        detail=progress_event.detail,
                    )

            # ── 6. Memory — post-execution summary ───────────────────────────
            try:
                report = self._orchestrator._executor.get_report()  # type: ignore[union-attr]
                summary = (
                    f"Session {session.session_id} completed. "
                    f"Tasks: {report.total_tasks}, Succeeded: {report.succeeded}, "
                    f"Failed: {report.failed}, Cancelled: {report.cancelled}."
                )
                await self._memory.episodic.record(
                    session_id=session.session_id,
                    content=summary,
                    memory_type="episodic",
                )
                yield make_event(AgentEventType.MEMORY_UPDATED, session.session_id, layer="episodic", event="session_summary_recorded")
            except Exception as exc:
                logger.warning(f"[{session.session_id}] Post-execution memory write failed: {exc}")

            # ── 7. Session completed ─────────────────────────────────────────
            final_status = AgentSessionStatus.COMPLETED
            if self._orchestrator._executor and self._orchestrator._executor.context.is_cancelled():  # type: ignore[union-attr]
                final_status = AgentSessionStatus.CANCELLED

            await self._session_manager.update_status(session, final_status)

            outcome_event = (
                AgentEventType.SESSION_CANCELLED if final_status == AgentSessionStatus.CANCELLED
                else AgentEventType.SESSION_COMPLETED
            )
            yield make_event(
                outcome_event,
                session.session_id,
                run_id=session.run_id,
                end_time=datetime.now(tz=timezone.utc).isoformat(),
            )

        except Exception as exc:
            logger.exception(f"[{session.session_id}] Agent run failed: {exc}")
            await self._session_manager.update_status(session, AgentSessionStatus.FAILED)
            yield make_event(
                AgentEventType.SESSION_FAILED,
                session.session_id,
                error=str(exc),
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Control surface
    # ──────────────────────────────────────────────────────────────────────────

    def pause(self) -> None:
        """Cooperatively pause the active execution wave."""
        self._orchestrator.pause()

    def resume(self) -> None:
        """Resume a paused execution."""
        self._orchestrator.resume()

    def cancel(self) -> None:
        """Signal cancellation to the active executor."""
        self._orchestrator.cancel()
