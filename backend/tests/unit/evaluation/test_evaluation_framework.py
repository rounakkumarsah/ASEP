"""
ASEP — Unit and Integration Tests for Enterprise Evaluation Framework
"""

import pytest
from httpx import AsyncClient

from src.evaluation.registry import get_evaluation_registry, EvaluationRegistry
from src.evaluation.datasets import EvaluationDataset, EvaluationCase
from src.evaluation.reports import ReportBuilder


def test_evaluation_registry_registration():
    """Verify registry add, lookup, and metadata discovery flows."""
    registry = EvaluationRegistry()
    
    custom_dataset = EvaluationDataset(
        name="test_dataset_alpha",
        version="1.0",
        description="Integration testing dataset",
        dataset_type="golden",
        cases=[
            EvaluationCase(
                id="test_case_1",
                goal="Write tests for the registry",
                tags=["alpha", "test"],
                expected_min_tasks=1,
                expected_tool_names=["mock_tool"],
                pass_threshold=0.75
            )
        ]
    )

    # Test registration and metadata
    registry.register(custom_dataset)
    assert registry.lookup("test_dataset_alpha") is not None
    assert registry.version("test_dataset_alpha") == "1.0"
    
    meta = registry.metadata("test_dataset_alpha")
    assert meta is not None
    assert meta["dataset_type"] == "golden"
    assert meta["case_count"] == 1

    # Test unregister
    registry.unregister("test_dataset_alpha")
    assert registry.lookup("test_dataset_alpha") is None


def test_evaluation_exporters():
    """Verify Markdown and HTML reports are formatted correctly."""
    registry = get_evaluation_registry()
    dataset = registry.lookup("asep_sample")
    assert dataset is not None

    builder = ReportBuilder()
    report = builder.build(dataset.name, [])

    md_content = builder.to_markdown(report)
    html_content = builder.to_html(report)

    assert "# Evaluation Summary Report — asep_sample" in md_content
    assert "<html><body>" in html_content


@pytest.mark.asyncio
async def test_evaluation_api_endpoints(async_client: AsyncClient):
    """Test all five REST API endpoints for evaluations."""
    # 1. GET /api/v1/evaluations
    resp_list = await async_client.get("/api/v1/evaluations")
    assert resp_list.status_code == 200
    data = resp_list.json()
    assert len(data) >= 1
    assert data[0]["name"] == "asep_sample"

    # 2. GET /api/v1/evaluations/{id}
    resp_get = await async_client.get("/api/v1/evaluations/asep_sample")
    assert resp_get.status_code == 200
    assert resp_get.json()["dataset_type"] == "custom"

    # 3. POST /api/v1/evaluations/run
    resp_run = await async_client.post(
        "/api/v1/evaluations/run",
        json={"dataset_name": "asep_sample"}
    )
    assert resp_run.status_code == 200
    run_data = resp_run.json()
    assert run_data["status"] == "completed"
    assert run_data["summary"]["total_cases"] == 3

    # 4. GET /api/v1/evaluations/report/{id}
    resp_report_json = await async_client.get("/api/v1/evaluations/report/asep_sample")
    assert resp_report_json.status_code == 200
    assert "summary" in resp_report_json.json()

    resp_report_md = await async_client.get("/api/v1/evaluations/report/asep_sample?format=markdown")
    assert resp_report_md.status_code == 200
    assert resp_report_md.json().startswith("# Evaluation Summary")

    resp_report_html = await async_client.get("/api/v1/evaluations/report/asep_sample?format=html")
    assert resp_report_html.status_code == 200
    assert "<html>" in resp_report_html.json()

    # 5. GET /api/v1/evaluations/history
    resp_history = await async_client.get("/api/v1/evaluations/history")
    assert resp_history.status_code == 200
    assert len(resp_history.json()) >= 1
