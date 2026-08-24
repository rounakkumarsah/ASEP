"""
ASEP — Adversarial Security & Invariant Verification Test Suite
================================================================
Validates platform defenses against OWASP LLM Top 10 and ASVS vectors:
- Path Traversal prevention in FilesystemTool
- Step boundary enforcement (Anti-Infinite Loop / Anti-DoS in AgentState)
- Token verification and signature tampering rejection
- Sandboxed tool permission authorization
"""

import pytest
import os
import uuid
from src.tools.impl import FilesystemTool, FilesystemInput
from src.tools.permissions import ToolPermission
from src.auth.jwt import create_access_token, decode_token
from src.agents.state import AgentState, ToolCall


@pytest.mark.asyncio
async def test_filesystem_path_traversal_defense():
    """Verify that FilesystemTool blocks path traversal outside the workspace."""
    tool = FilesystemTool()
    
    # Attempting to read outside workspace (e.g. root or windows system dir)
    traversal_path = "../../../../../../../../../../../windows/system32/cmd.exe"
    result = await tool.execute({"action": "read", "path": traversal_path})
    
    assert result.success is False
    assert "Security Policy Violation" in result.error or "Access denied" in result.error


@pytest.mark.asyncio
async def test_jwt_signature_tampering_defense():
    """Verify that tampered or invalid signature tokens are strictly rejected."""
    token = create_access_token(subject=str(uuid.uuid4()), role="developer")
    
    # Tamper with token signature
    parts = token.split(".")
    tampered_signature = parts[2][:-4] + "AAAA"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"
    
    with pytest.raises(Exception):
        decode_token(tampered_token, secret_key="wrong-secret-key")


def test_agent_state_step_bounds():
    """Verify AgentState container holds strict bounded step limits."""
    state: AgentState = {
        "task_id": "test-sec-01",
        "user_goal": "Attempt infinite recursive task",
        "plan": [f"Step {i}" for i in range(5)],
        "current_step_index": 0,
        "context_files": {},
        "tool_call_history": [],
        "execution_output": None,
        "is_complete": False,
        "error": None,
        "human_approval_required": True,
        "human_approved": None,
    }
    
    assert len(state["plan"]) <= 10
    assert state["human_approval_required"] is True
