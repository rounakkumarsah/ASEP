"""
ASEP — Production Multi-LLM LangGraph Supervisor
================================================
Routes sub-agent tasks to optimal LLM providers based on task type:
  - Code Writing   → Groq (fastest inference, 30k TPM)
  - Code Review    → Gemini (deepest reasoning, 2M tokens/min)
  - Test Gen       → OpenRouter (cost-effective auto-routing)

Features:
  - 3 retries with exponential backoff per provider.
  - Multi-tier fallback chain (Primary → Secondary → Tertiary → Explicit Error).
  - Strict policy: NO silent mock or static template fallbacks.
  - Context retrieval via Qdrant vector memory.
  - Token consumption tracking logged to PostgreSQL user_quota_logs table.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import time
import uuid
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy import delete, func, select

from src.agents.planner import planner_node
from src.agents.state import AgentState
from src.ai_runtime.contracts import CompletionRequest, Message
from src.ai_runtime.registry import ProviderRegistry
from src.config.settings import get_settings
from src.db.models.queue_job import QueueJob
from src.db.models.user_quota_log import UserQuotaLog
from src.db.postgres import _get_session_factory

logger = logging.getLogger(__name__)

# Registered worker agent roles
WORKER_AGENTS: list[str] = [
    "code_writer",
    "code_reviewer",
    "test_runner",
]


class MultiLLMRouter:
    """
    Intelligent router dispatching tasks across Groq, Gemini, and OpenRouter.
    Handles retries, fallback chains, vector memory retrieval, and quota logging.
    """

    PROVIDER_ROUTING: dict[str, list[dict[str, str]]] = {
        "code_writer": [
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"provider": "gemini", "model": "gemini-2.0-flash"},
            {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
        ],
        "code_reviewer": [
            {"provider": "gemini", "model": "gemini-2.0-flash"},
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
        ],
        "test_runner": [
            {"provider": "openrouter", "model": "openrouter/auto"},
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"provider": "gemini", "model": "gemini-2.0-flash"},
        ],
    }

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.settings = get_settings()
        self.max_retries = getattr(self.settings, "LLM_RETRY_ATTEMPTS", 3)

    async def get_vector_context(self, query: str, limit: int = 3) -> str:
        """Fetch semantic code context from Qdrant vector memory if available."""
        if not query:
            return ""
        try:
            from src.vector.qdrant import get_qdrant_client
            from src.vector.vector_service import VectorService

            client = get_qdrant_client()
            svc = VectorService(client)
            results = await svc.search(query=query, limit=limit)
            if results:
                items = [str(r.payload.get("text", "")).strip() for r in results if r.payload]
                return "\n".join(f"- {item}" for item in items if item)
        except Exception as exc:
            logger.debug("Qdrant context retrieval skipped: %s", exc)
        return ""

    async def log_quota_usage(
        self,
        user_id: uuid.UUID | str | None,
        tokens_used: int,
        provider_name: str,
    ) -> None:
        """Persist consumed token count to the user_quota_logs table."""
        if not user_id or tokens_used <= 0:
            return
        try:
            parsed_uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
            session_factory = _get_session_factory()
            async with session_factory() as session:
                entry = UserQuotaLog(
                    user_id=parsed_uid,
                    tokens_used=tokens_used,
                    provider_name=provider_name,
                )
                session.add(entry)
                await session.commit()
        except Exception as exc:
            logger.warning("Failed to log token usage to user_quota_logs: %s", exc)

    async def _execute_provider_with_retry(
        self,
        provider_name: str,
        model_name: str,
        messages: list[Message],
        temperature: float = 0.3,
    ) -> tuple[str, int, int, int]:
        """Call a single provider with exponential backoff retries.
        Returns: (output_text, total_tokens, prompt_tokens, completion_tokens)
        """
        provider = self.registry.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found in registry")

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                req = CompletionRequest(
                    messages=messages,
                    model=model_name,
                    temperature=temperature,
                )
                resp = await provider.complete(req)
                tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                if getattr(resp, "usage", None):
                    tokens = getattr(resp.usage, "total_tokens", 0)
                    prompt_tokens = getattr(resp.usage, "prompt_tokens", 0)
                    completion_tokens = getattr(resp.usage, "completion_tokens", 0)
                    if tokens == 0 and (prompt_tokens > 0 or completion_tokens > 0):
                        tokens = prompt_tokens + completion_tokens
                    elif (prompt_tokens == 0 and completion_tokens == 0) and tokens > 0:
                        prompt_tokens = int(tokens * 0.4)
                        completion_tokens = tokens - prompt_tokens
                return resp.text, tokens, prompt_tokens, completion_tokens
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "LLM provider %s call failed (attempt %d/%d): %s",
                    provider_name,
                    attempt + 1,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries - 1:
                    delay = min(0.2 * (2**attempt), 2.0)
                    await asyncio.sleep(delay)

        raise RuntimeError(
            f"Provider {provider_name} exhausted {self.max_retries} retries: {last_exc}"
        ) from last_exc

    async def execute_task(
        self,
        task_type: str,
        user_prompt: str,
        system_prompt: str,
        context_query: str = "",
        user_id: uuid.UUID | str | None = None,
        workspace_id: str | None = None,
    ) -> tuple[str, int, str]:
        """
        Execute task through the fallback chain for the specified task type.
        Returns: (output_text, tokens_used, active_provider)
        """
        chain = self.PROVIDER_ROUTING.get(task_type, self.PROVIDER_ROUTING["code_writer"])

        # Augment with Qdrant vector memory if relevant
        semantic_context = await self.get_vector_context(context_query or user_prompt)
        full_system_prompt = system_prompt
        if semantic_context:
            full_system_prompt += f"\n\nRelevant Codebase Context:\n{semantic_context}"

        messages = [
            Message(role="system", content=full_system_prompt),
            Message(role="user", content=user_prompt),
        ]

        errors: list[str] = []
        for step in chain:
            provider = step["provider"]
            model = step["model"]
            try:
                logger.info(
                    "Routing %s to %s (%s)",
                    task_type,
                    provider,
                    model,
                )
                output, tokens, prompt_tokens, completion_tokens = await self._execute_provider_with_retry(
                    provider_name=provider,
                    model_name=model,
                    messages=messages,
                )
                # Log quota usage to database
                await self.log_quota_usage(user_id, tokens, provider)

                # Log granular token meter & cost attribution
                if user_id:
                    try:
                        from src.services.token_meter import TokenMeter

                        cost = TokenMeter.estimate_cost(provider, prompt_tokens, completion_tokens)
                        await TokenMeter.log_usage(
                            user_id=user_id,
                            workspace_id=workspace_id or "default",
                            provider=provider,
                            tokens_input=prompt_tokens,
                            tokens_output=completion_tokens,
                            cost_usd=cost,
                        )
                    except Exception as meter_exc:
                        logger.warning("TokenMeter.log_usage failed in supervisor: %s", meter_exc)

                return output, tokens, provider
            except Exception as exc:
                err_msg = f"{provider}({model}): {exc}"
                logger.warning("Fallback step failed: %s", err_msg)
                errors.append(err_msg)

        # Explicit failure — NO silent fallback templates
        raise RuntimeError(
            f"All providers in fallback chain failed for {task_type}. Errors: {'; '.join(errors)}"
        )


# Global router singleton
router = MultiLLMRouter()


async def code_write_node(state: AgentState) -> dict[str, Any]:
    """
    Code Writer Node — Dispatches to Groq (fast generation).
    Generates implementation code from goal/plan.
    """
    goal = state.get("goal", "")
    current_step = state.get("current_step", 0)
    user_id = state.get("user_id")
    workspace_id = state.get("workspace_id", "default")

    prompt = f"Goal: {goal}\nWrite complete, clean, production-ready code fulfilling this objective."
    system = "You are an expert autonomous code writer. Write clean, robust, and well-commented code. Do not output markdown fences or pleasantries, only valid code."

    try:
        code_output, tokens, provider = await router.execute_task(
            task_type="code_writer",
            user_prompt=prompt,
            system_prompt=system,
            context_query=goal,
            user_id=user_id,
            workspace_id=workspace_id,
        )

        msg = {
            "role": "assistant",
            "sender": f"code_writer({provider})",
            "content": code_output,
            "tokens": tokens,
        }

        # Validate syntax & sandbox constraints before progressing
        from src.services.restricted_code_sandbox import RestrictedExecutor

        is_valid, syntax_error = RestrictedExecutor.validate_syntax(code_output)
        if not is_valid:
            logger.warning("code_write_node syntax validation failed: %s", syntax_error)
            return {
                "error": f"Syntax validation failed: {syntax_error}",
                "is_complete": False,
            }

        return {
            "code": code_output,
            "messages": [msg],
            "current_step": current_step + 1,
            "error": None,
        }
    except Exception as exc:
        logger.error("code_write_node failed: %s", exc)
        return {
            "error": f"code_write_node error: {exc}",
            "is_complete": False,
        }


async def code_review_node(state: AgentState) -> dict[str, Any]:
    """
    Code Reviewer Node — Dispatches to Gemini (deep reasoning).
    Critiques code for correctness, security vulnerabilities, and design flaws.
    """
    code = state.get("code", "")
    goal = state.get("goal", "")
    current_step = state.get("current_step", 0)
    user_id = state.get("user_id")
    workspace_id = state.get("workspace_id", "default")

    prompt = f"Goal: {goal}\nReview the following code for bugs, edge cases, and performance:\n\n{code}"
    system = "You are an elite code reviewer and security auditor. Provide structured, actionable critique with specific improvement recommendations."

    try:
        review_output, tokens, provider = await router.execute_task(
            task_type="code_reviewer",
            user_prompt=prompt,
            system_prompt=system,
            context_query=goal,
            user_id=user_id,
            workspace_id=workspace_id,
        )

        msg = {
            "role": "assistant",
            "sender": f"code_reviewer({provider})",
            "content": review_output,
            "tokens": tokens,
        }
        return {
            "review": review_output,
            "messages": [msg],
            "current_step": current_step + 1,
            "error": None,
        }
    except Exception as exc:
        logger.error("code_review_node failed: %s", exc)
        return {
            "error": f"code_review_node error: {exc}",
            "is_complete": False,
        }


async def test_gen_node(state: AgentState) -> dict[str, Any]:
    """
    Test Runner / Generator Node — Dispatches to OpenRouter (cost-effective fallback).
    Produces comprehensive unit and integration tests.
    """
    code = state.get("code", "")
    review = state.get("review", "")
    goal = state.get("goal", "")
    current_step = state.get("current_step", 0)
    user_id = state.get("user_id")
    workspace_id = state.get("workspace_id", "default")

    prompt = (
        f"Goal: {goal}\n"
        f"Code:\n{code}\n"
        f"Review Feedback:\n{review}\n"
        "Generate a complete pytest test suite covering normal, edge, and error scenarios."
    )
    system = "You are a senior QA automation engineer. Generate clean pytest test suites with thorough assertions."

    try:
        test_output, tokens, provider = await router.execute_task(
            task_type="test_runner",
            user_prompt=prompt,
            system_prompt=system,
            context_query=goal,
            user_id=user_id,
            workspace_id=workspace_id,
        )

        msg = {
            "role": "assistant",
            "sender": f"test_runner({provider})",
            "content": test_output,
            "tokens": tokens,
        }

        # Run generated tests via RestrictedExecutor sandbox with 30-second timeout
        from src.services.restricted_code_sandbox import RestrictedExecutor

        test_result = await RestrictedExecutor.execute(
            code=code,
            test_code=test_output,
            timeout=30.0,
        )

        if not test_result.get("success"):
            err_msg = test_result.get("error") or "Sandbox test execution failed"
            logger.warning("RestrictedExecutor sandbox test execution failed: %s", err_msg)
            return {
                "error": f"RestrictedExecutor test failure: {err_msg}",
                "is_complete": False,
            }

        final_summary = (
            f"=== Execution Complete ===\n"
            f"Code generated and reviewed.\n"
            f"Tests generated by {provider} and passed sandbox verification ({round(test_result.get('execution_time_ms', 0), 1)}ms).\n"
        )
        return {
            "tests": test_output,
            "test_results": test_result,
            "final_output": final_summary,
            "messages": [msg],
            "current_step": current_step + 1,
            "error": None,
            "is_complete": True,
        }
    except Exception as exc:
        logger.error("test_gen_node failed: %s", exc)
        return {
            "error": f"test_gen_node error: {exc}",
            "is_complete": False,
        }

# Explicitly instruct pytest not to collect test_gen_node as a test case
test_gen_node.__test__ = False


async def supervisor_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node: Supervisor.
    Orchestrates the sequential flow: code_writer → code_reviewer → test_runner.
    Terminates graph if errors occur or all steps complete.
    """
    run_id = str(state.get("run_id", "default-run"))
    current_step = state.get("current_step", 0)
    error = state.get("error")

    logger.info(
        "Supervisor node invoked",
        extra={"run_id": run_id, "current_step": current_step, "error": error},
    )

    if error:
        logger.error("Supervisor: error encountered in execution: %s", error)
        return {"is_complete": True}

    if current_step >= 3 or state.get("is_complete"):
        logger.info("Supervisor: all workflow steps completed", extra={"run_id": run_id})
        return {"is_complete": True}

    return {"is_complete": False}


def build_supervisor_graph() -> Any:
    """
    Constructs and compiles the production LangGraph StateGraph.
    Flow: planner → supervisor → [code_writer → supervisor → code_reviewer → supervisor → test_runner → supervisor] → END.
    """
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("code_writer", code_write_node)
    graph.add_node("code_reviewer", code_review_node)
    graph.add_node("test_runner", test_gen_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "supervisor")

    def route_supervisor(state: AgentState) -> str:
        if state.get("error") or state.get("is_complete"):
            return END
        step = state.get("current_step", 0)
        if step == 0:
            return "code_writer"
        elif step == 1:
            return "code_reviewer"
        elif step == 2:
            return "test_runner"
        return END

    graph.add_conditional_edges("supervisor", route_supervisor)

    # Return loop back to supervisor after each worker node
    graph.add_edge("code_writer", "supervisor")
    graph.add_edge("code_reviewer", "supervisor")
    graph.add_edge("test_runner", "supervisor")

    return graph.compile()


async def execute_graph(initial_state: dict[str, Any] | AgentState) -> dict[str, Any]:
    """
    Executes the compiled LangGraph supervisor graph asynchronously.
    Returns the final accumulated AgentState dictionary containing code, review, and tests.
    """
    graph = build_supervisor_graph()
    logger.info("Executing LangGraph supervisor graph asynchronously...")
    result: dict[str, Any] = await graph.ainvoke(initial_state)
    logger.info(
        "LangGraph supervisor graph execution finished",
        extra={
            "is_complete": result.get("is_complete"),
            "current_step": result.get("current_step"),
            "has_error": bool(result.get("error")),
        },
    )
    return result


async def notify_job_update(job_id: str, payload: dict[str, Any]) -> None:
    """Dispatches real-time WebSocket and webhook updates to clients."""
    try:
        from src.routes.agents import job_connection_manager

        await job_connection_manager.broadcast_job_update(job_id, payload)
    except Exception as exc:
        logger.debug("Job status notification skipped: %s", exc)


async def cleanup_completed_jobs(retention_days: int = 7) -> int:
    """
    Auto-cleanup completed and failed jobs older than retention_days (default: 7 days).
    Deletes obsolete records from queue_jobs table to maintain database hygiene.
    """
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)
    session_factory = _get_session_factory()
    async with session_factory() as session:
        stmt = delete(QueueJob).where(
            QueueJob.completed_at.is_not(None),
            QueueJob.completed_at <= cutoff,
            QueueJob.status.in_(["completed", "failed"]),
        )
        res = await session.execute(stmt)
        await session.commit()
        deleted_count = res.rowcount
        logger.info(
            "Auto-cleanup: purged %d completed/failed jobs older than %d days.",
            deleted_count,
            retention_days,
        )
        return deleted_count


async def execute_agent_background_task(job_id: str | uuid.UUID) -> dict[str, Any]:
    """
    Asynchronous background task runner for agent execution.
    Wraps supervisor.execute_graph(), logs execution metrics to queue_jobs table,
    enforces 2x auto-retry with exponential backoff on failure, and triggers WebSocket events.
    """
    jid = uuid.UUID(str(job_id))
    session_factory = _get_session_factory()

    # 1. Fetch job and mark as running
    async with session_factory() as session:
        stmt = select(QueueJob).where(QueueJob.id == jid)
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            logger.error("execute_agent_background_task: Job %s not found.", jid)
            return {"error": f"Job {jid} not found"}

        if job.status == "completed":
            logger.info("Job %s is already completed. Skipping.", jid)
            return job.result or {}

        job.status = "running"
        await session.commit()

    await notify_job_update(str(jid), {"job_id": str(jid), "status": "running"})

    start_time = time.perf_counter()
    initial_state = {
        "run_id": jid,
        "session_id": str(job.user_id),
        "user_id": str(job.user_id),
        "goal": job.spec.get("prompt") or job.spec.get("goal") or "Execute autonomous software engineering task",
        "current_step": 0,
        "messages": [],
        "is_complete": False,
        "error": None,
    }

    try:
        final_state = await execute_graph(initial_state)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Aggregate consumed tokens from agent messages
        total_tokens = 0
        for msg in final_state.get("messages", []):
            if isinstance(msg, dict) and "tokens" in msg:
                total_tokens += int(msg.get("tokens", 0))

        graph_error = final_state.get("error")
        if graph_error:
            raise RuntimeError(str(graph_error))

        result_payload = {
            "code": final_state.get("code", ""),
            "review": final_state.get("review", ""),
            "tests": final_state.get("tests", ""),
            "final_output": final_state.get("final_output", ""),
        }
        metrics_payload = {
            "duration_ms": duration_ms,
            "total_tokens": total_tokens,
            "step_count": final_state.get("current_step", 0),
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        # Update database with success
        async with session_factory() as session:
            stmt = select(QueueJob).where(QueueJob.id == jid)
            res = await session.execute(stmt)
            db_job = res.scalar_one_or_none()
            if db_job:
                db_job.status = "completed"
                db_job.result = result_payload
                db_job.metrics = metrics_payload
                db_job.error = None
                db_job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                await session.commit()

        await notify_job_update(
            str(jid),
            {
                "job_id": str(jid),
                "status": "completed",
                "result": result_payload,
                "metrics": metrics_payload,
            },
        )
        return result_payload

    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error("Job %s execution failed: %s", jid, exc, exc_info=True)

        async with session_factory() as session:
            stmt = select(QueueJob).where(QueueJob.id == jid)
            res = await session.execute(stmt)
            db_job = res.scalar_one_or_none()
            if not db_job:
                return {"error": str(exc)}

            if db_job.retry_count < db_job.max_retries:
                db_job.retry_count += 1
                db_job.status = "pending"
                db_job.error = f"Attempt {db_job.retry_count} failed: {exc}. Retrying..."
                await session.commit()

                from src.services.task_queue_service import get_task_queue, run_agent_job

                queue = get_task_queue()
                retry_delay = 2 ** db_job.retry_count
                queue.scheduler.add_job(
                    run_agent_job,
                    "date",
                    run_date=datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(seconds=retry_delay),
                    args=[str(jid)],
                    id=f"{jid}_retry_{db_job.retry_count}",
                    replace_existing=True,
                )

                await notify_job_update(
                    str(jid),
                    {
                        "job_id": str(jid),
                        "status": "retrying",
                        "retry_count": db_job.retry_count,
                        "error": str(exc),
                    },
                )
                return {"status": "retrying", "error": str(exc)}

            # All retries exhausted -> terminal failure
            db_job.status = "failed"
            db_job.error = str(exc)
            db_job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db_job.metrics = {
                "duration_ms": duration_ms,
                "failed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            await session.commit()

        await notify_job_update(
            str(jid),
            {
                "job_id": str(jid),
                "status": "failed",
                "error": str(exc),
            },
        )
        return {"status": "failed", "error": str(exc)}

