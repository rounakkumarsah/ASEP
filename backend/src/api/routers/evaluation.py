"""
ASEP — API Router for Evaluations Subsystem
"""

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.evaluation.registry import get_evaluation_registry
from src.evaluation.evaluator import Evaluator, EvaluationResult
from src.evaluation.reports import ReportBuilder, EvaluationReport
from src.agent.events import AgentEvent, AgentEventType

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

# Mock history data to populate /history endpoint
_evaluation_history: List[EvaluationReport] = []


class EvaluationRunRequest(BaseModel):
    dataset_name: str


@router.get("", response_model=List[Dict[str, Any]])
async def list_evaluations() -> List[Dict[str, Any]]:
    """Retrieve all registered evaluation datasets."""
    registry = get_evaluation_registry()
    datasets = registry.discover()
    return [registry.metadata(ds.name) for ds in datasets if registry.metadata(ds.name)]


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history() -> List[Dict[str, Any]]:
    """Retrieve past evaluation runs and summaries."""
    return [
        {
            "dataset_name": r.summary.dataset_name,
            "total_cases": r.summary.total_cases,
            "passed": r.summary.passed,
            "pass_rate": r.summary.pass_rate,
            "avg_overall_score": r.summary.avg_overall_score,
            "generated_at": r.generated_at
        }
        for r in _evaluation_history
    ]


@router.get("/{dataset_name}")
async def get_evaluation(dataset_name: str) -> Dict[str, Any]:
    """Retrieve details of a specific registered evaluation dataset."""
    registry = get_evaluation_registry()
    meta = registry.metadata(dataset_name)
    if not meta:
        raise HTTPException(status_code=404, detail="Evaluation dataset not found.")
    return meta


@router.post("/run", response_model=Dict[str, Any])
async def run_evaluation(req: EvaluationRunRequest) -> Dict[str, Any]:
    """Execute evaluation cases in a dataset and return the summary report."""
    registry = get_evaluation_registry()
    dataset = registry.lookup(req.dataset_name)
    if not dataset:
        raise HTTPException(status_code=404, detail="Evaluation dataset not found.")

    # Create dummy events generator for executing runner
    async def dummy_runner(goal: str):
        session_id = str(uuid.uuid4())
        yield AgentEvent(
            event_type=AgentEventType.SESSION_STARTED,
            session_id=session_id,
            payload={"run_id": "run-1", "thread_id": "thread-1"}
        )
        yield AgentEvent(
            event_type=AgentEventType.CONTEXT_BUILT,
            session_id=session_id,
            payload={}
        )
        yield AgentEvent(
            event_type=AgentEventType.PLAN_CREATED,
            session_id=session_id,
            payload={"task_count": 2, "tasks": [{"id": "task-1", "depends_on": []}, {"id": "task-2", "depends_on": ["task-1"]}]}
        )
        yield AgentEvent(
            event_type=AgentEventType.TASK_STARTED,
            session_id=session_id,
            payload={"task_id": "task-1"}
        )
        yield AgentEvent(
            event_type=AgentEventType.TASK_COMPLETED,
            session_id=session_id,
            payload={"task_id": "task-1", "status": "success"}
        )
        yield AgentEvent(
            event_type=AgentEventType.SESSION_COMPLETED,
            session_id=session_id,
            payload={}
        )

    evaluator = Evaluator(runner=dummy_runner)
    results = await evaluator.evaluate_dataset(dataset)

    builder = ReportBuilder()
    report = builder.build(dataset.name, results)
    _evaluation_history.append(report)

    return {
        "status": "completed",
        "dataset_name": req.dataset_name,
        "summary": report.summary.model_dump(),
        "report_id": req.dataset_name
    }


@router.get("/report/{dataset_name}")
async def get_report(dataset_name: str, format: str = Query("json", regex="^(json|markdown|html)$")) -> Any:
    """Retrieve formatted report for the given dataset/run."""
    report = next((r for r in _evaluation_history if r.summary.dataset_name == dataset_name), None)
    if not report:
        # Generate on the fly if not run yet
        registry = get_evaluation_registry()
        dataset = registry.lookup(dataset_name)
        if not dataset:
            raise HTTPException(status_code=404, detail="Report or dataset not found.")

        # Re-run or return mock report
        builder = ReportBuilder()
        report = builder.build(dataset_name, [])
        _evaluation_history.append(report)

    builder = ReportBuilder()
    if format == "markdown":
        return builder.to_markdown(report)
    elif format == "html":
        return builder.to_html(report)
    return builder.to_dict(report)
