from fastapi import APIRouter, Depends, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.db.postgres import get_db_session
from src.utils.metrics import metrics_store
from src.db.models.agent_run import AgentRun
from src.db.models.task import Task

router = APIRouter()

@router.get("/metrics")
async def get_metrics(
    response: Response,
    accept: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session)
):
    # Query current DB status metrics
    active_sessions = await db.scalar(
        select(func.count(AgentRun.id)).where(AgentRun.status == "running")
    ) or 0
    pending_tasks = await db.scalar(
        select(func.count(Task.id)).where(Task.status == "pending")
    ) or 0
    
    system_stats = metrics_store.get_system_metrics()
    
    # Calculate error rate
    error_rate = 0.0
    if metrics_store.request_count > 0:
        error_rate = metrics_store.error_count / metrics_store.request_count

    # If Accept header contains text/plain, return Prometheus format
    if accept and "text/plain" in accept:
        prometheus_data = [
            f"# HELP asep_requests_total Total number of HTTP requests processed.",
            f"# TYPE asep_requests_total counter",
            f"asep_requests_total {metrics_store.request_count}",
            f"# HELP asep_request_latency_seconds_sum Cumulative sum of request latencies.",
            f"# TYPE asep_request_latency_seconds_sum counter",
            f"asep_request_latency_seconds_sum {round(metrics_store.request_latency_sum, 4)}",
            f"# HELP asep_errors_total Total number of HTTP 5xx errors.",
            f"# TYPE asep_errors_total counter",
            f"asep_errors_total {metrics_store.error_count}",
            f"# HELP asep_error_rate Ratio of HTTP 5xx errors to total requests.",
            f"# TYPE asep_error_rate gauge",
            f"asep_error_rate {round(error_rate, 4)}",
            f"# HELP asep_active_sessions Active running agent sessions.",
            f"# TYPE asep_active_sessions gauge",
            f"asep_active_sessions {active_sessions}",
            f"# HELP asep_pending_tasks Number of tasks pending execution in the queue.",
            f"# TYPE asep_pending_tasks gauge",
            f"asep_pending_tasks {pending_tasks}",
            f"# HELP asep_process_memory_rss_bytes Resident memory size of the process.",
            f"# TYPE asep_process_memory_rss_bytes gauge",
            f"asep_process_memory_rss_bytes {system_stats['process_memory_rss_bytes']}",
            f"# HELP asep_process_cpu_percent CPU utilization percentage of the process.",
            f"# TYPE asep_process_cpu_percent gauge",
            f"asep_process_cpu_percent {system_stats['process_cpu_percent']}",
        ]
        return Response(content="\n".join(prometheus_data) + "\n", media_type="text/plain")

    # Otherwise return clean JSON
    return {
        "requests_total": metrics_store.request_count,
        "request_latency_sum": round(metrics_store.request_latency_sum, 4),
        "errors_total": metrics_store.error_count,
        "error_rate": round(error_rate, 4),
        "active_sessions": active_sessions,
        "pending_tasks": pending_tasks,
        "system": system_stats
    }
