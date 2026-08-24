"""
ASEP — Unit and Integration Tests for Enterprise Evaluation Framework
"""

import pytest
from httpx import AsyncClient

from src.evaluation.datasets import EvaluationCase, EvaluationDataset
from src.evaluation.registry import EvaluationRegistry, get_evaluation_registry
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

    test_dataset = EvaluationDataset(
        name="test_export_dataset",
        version="1.0",
        description="Testing exporters",
        dataset_type="custom",
        cases=[]
    )
    registry.register(test_dataset)

    try:
        dataset = registry.lookup("test_export_dataset")
        assert dataset is not None

        builder = ReportBuilder()
        report = builder.build(dataset.name, [])

        md_content = builder.to_markdown(report)
        html_content = builder.to_html(report)

        assert "# Evaluation Summary Report — test_export_dataset" in md_content
        assert "<html><body>" in html_content
    finally:
        registry.unregister("test_export_dataset")


@pytest.mark.asyncio
async def test_evaluation_api_endpoints(async_client: AsyncClient):
    """Test all five REST API endpoints for evaluations."""
    registry = get_evaluation_registry()

    test_dataset = EvaluationDataset(
        name="test_api_dataset",
        version="1.0",
        description="Testing APIs",
        dataset_type="custom",
        cases=[
            EvaluationCase(
                id="test_case_1",
                goal="Test API",
                tags=["api"],
                expected_min_tasks=0,
                expected_tool_names=[],
                pass_threshold=0.0
            )
        ]
    )
    registry.register(test_dataset)

    try:
        # 1. GET /api/v1/evaluations
        resp_list = await async_client.get("/api/v1/evaluations")
        assert resp_list.status_code == 200
        data = resp_list.json()
        assert len(data) >= 1

        # Make sure our dataset is in the list
        dataset_names = [d["name"] for d in data]
        assert "test_api_dataset" in dataset_names

        # 2. GET /api/v1/evaluations/{id}
        resp_get = await async_client.get("/api/v1/evaluations/test_api_dataset")
        assert resp_get.status_code == 200
        assert resp_get.json()["dataset_type"] == "custom"

        # 3. POST /api/v1/evaluations/run
        resp_run = await async_client.post(
            "/api/v1/evaluations/run",
            json={"dataset_name": "test_api_dataset"}
        )
        assert resp_run.status_code == 200
        run_data = resp_run.json()
        assert run_data["status"] == "completed"
        assert run_data["summary"]["total_cases"] == 1

        # 4. GET /api/v1/evaluations/report/{id}
        resp_report_json = await async_client.get("/api/v1/evaluations/report/test_api_dataset")
        assert resp_report_json.status_code == 200
        assert "summary" in resp_report_json.json()

        resp_report_md = await async_client.get("/api/v1/evaluations/report/test_api_dataset?format=markdown")
        assert resp_report_md.status_code == 200
        assert resp_report_md.json().startswith("# Evaluation Summary")

        resp_report_html = await async_client.get("/api/v1/evaluations/report/test_api_dataset?format=html")
        assert resp_report_html.status_code == 200
        assert "<html>" in resp_report_html.json()

        # 5. GET /api/v1/evaluations/history
        resp_history = await async_client.get("/api/v1/evaluations/history")
        assert resp_history.status_code == 200
        assert len(resp_history.json()) >= 1
    finally:
        registry.unregister("test_api_dataset")
