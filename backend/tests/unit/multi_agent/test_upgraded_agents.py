import pytest
import tempfile
import os
from unittest.mock import MagicMock
from src.multi_agent.contracts import AgentRole, AgentState, AgentRequest
from src.multi_agent.registry import AgentRegistry
from src.multi_agent.research_agent import ResearchAgent
from src.multi_agent.coding_agent import CodingAgent
from src.governance.screenshot_debug import ScreenshotDebugger

@pytest.mark.asyncio
async def test_upgraded_research_agent_pipeline():
    agent = ResearchAgent()
    req = AgentRequest(
        execution_id="research-run-1",
        correlation_id="corr-1",
        input_data={"query": "Locate DB models"}
    )
    resp = await agent.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert "sources" in resp.output_data
    assert "GraphRAG" in resp.output_data["research_notes"]

@pytest.mark.asyncio
async def test_upgraded_coding_agent_screenshot_debugging():
    # Make sure filepath basename has 'error' or 'screenshot' in it
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "error_screenshot_test.png")
    with open(temp_path, "wb") as f:
        f.write(b"fake_image_bytes")

    try:
        agent = CodingAgent()
        req = AgentRequest(
            execution_id="coding-run-1",
            correlation_id="corr-2",
            input_data={
                "specification": "Fix DB connection failure",
                "action": "patch",
                "screenshot_path": temp_path
            }
        )
        resp = await agent.execute(req)
        assert resp.status == AgentState.COMPLETED
        assert "debug_results" in resp.output_data
        assert resp.output_data["debug_results"]["error_detected"] is True
        assert "ECONNREFUSED" in resp.output_data["generated_code"]
        assert "self_review" in resp.output_data
        assert resp.output_data["self_review"]["status"] == "approved"
    finally:
        os.remove(temp_path)
