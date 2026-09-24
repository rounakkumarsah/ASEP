import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai_runtime.registry import ProviderRegistry
from src.runtime.nodes import orchestrator_node
from src.runtime.runtime import LangGraphRuntime


@pytest.mark.asyncio
async def test_all_orchestrator_phases_have_edges_no_dead_ends():
    """
    FIX 2 Regression Test:
    Assert that EVERY phase the orchestrator can emit has a registered node handler
    and an outgoing router/edge in StateGraph, guaranteeing dead ends cannot ship.
    """
    representative_goals = [
        "Build an AI agent that chats with users",
        "Create an agentic AI multi-agent workflow system",
        "Automate business processes with workflow triggers",
        "Build a REST API backend with FastAPI",
        "Create a Discord bot for customer support",
        "Build a landing page website with Tailwind",
        "Develop a cross-platform mobile app",
        "Create a web application with full stack features",
    ]

    all_emitted_phases: set[str] = set()
    for goal in representative_goals:
        res = await orchestrator_node({"goal": goal})
        phase_map = res.get("phase_map", [])
        assert len(phase_map) > 0, f"Orchestrator returned empty phase_map for goal: {goal}"
        for phase in phase_map:
            all_emitted_phases.add(phase)

    runtime = LangGraphRuntime(MagicMock())
    registered_nodes = set(runtime.nodes.get_all().keys())
    branch_nodes = set(runtime.wrapper.workflow.branches.keys())
    edge_src_nodes = {src for src, _ in runtime.wrapper.workflow.edges}

    # Verify both clarification gates are explicitly among emitted phases
    assert "clarification_gate" in all_emitted_phases
    assert "deploy_clarification_gate" in all_emitted_phases

    for phase in all_emitted_phases:
        assert phase in registered_nodes, f"Phase '{phase}' emitted by orchestrator is not registered in runtime nodes!"
        assert (
            phase in branch_nodes or phase in edge_src_nodes
        ), f"DEAD END: Phase '{phase}' emitted by orchestrator has no outgoing edge or conditional branch router!"


def test_clarification_gate_and_deploy_clarification_gate_routing():
    """
    Verify clarification_gate routes to the next phase (blueprint/capability_blueprint)
    and deploy_clarification_gate routes to deploy path.
    """
    runtime = LangGraphRuntime(MagicMock())
    gate_branch = runtime.wrapper.workflow.branches["clarification_gate"]["phase_router"]
    phase_router = gate_branch.path.func

    # 1. Normal web-app phase map progression
    state_standard = {
        "current_phase": "clarification_gate",
        "status": "verified",
        "phase_map": ["research", "clarification_gate", "blueprint", "scaffold", "deploy_clarification_gate", "deploy", "host_manager"],
    }
    assert phase_router(state_standard) == "blueprint"

    # 2. Agentic phase map progression
    state_agentic = {
        "current_phase": "clarification_gate",
        "status": "verified",
        "phase_map": ["research", "clarification_gate", "capability_blueprint", "tool_design"],
    }
    assert phase_router(state_agentic) == "capability_blueprint"

    # 3. Fallback when not in phase map
    state_fallback = {
        "current_phase": "clarification_gate",
        "status": "verified",
        "phase_map": ["research", "implement"],
    }
    assert phase_router(state_fallback) == "blueprint"

    # 4. Deploy clarification gate normal progression
    deploy_state = {
        "current_phase": "deploy_clarification_gate",
        "status": "verified",
        "phase_map": ["security_audit", "deploy_clarification_gate", "deploy", "host_manager"],
    }
    assert phase_router(deploy_state) == "deploy"

    # 5. Deploy clarification gate fallback
    deploy_fallback = {
        "current_phase": "deploy_clarification_gate",
        "status": "verified",
        "phase_map": ["security_audit", "host_manager"],
    }
    assert phase_router(deploy_fallback) == "deploy"


def test_provider_priority_default_and_resolution():
    """
    FIX 3 Unit Test:
    Verify default AI_PROVIDER_PRIORITY is 'gemini,groq,openrouter,openai,ollama',
    and helper methods correctly resolve keys and default model.
    """
    with patch.dict("os.environ", {}, clear=False):
        # Remove any ambient env override
        import os
        os.environ.pop("AI_PROVIDER_PRIORITY", None)
        registry = ProviderRegistry()
        assert registry.priority == ["gemini", "groq", "openrouter", "openai", "ollama"]
        assert registry.priority[-1] == "ollama"

        # Check key presence booleans (does not return values)
        assert isinstance(registry.is_key_present("gemini"), bool)
        assert isinstance(registry.is_key_present("groq"), bool)
        assert isinstance(registry.is_key_present("openrouter"), bool)
        assert registry.is_key_present("ollama") is True
        assert registry.is_key_present("mock") is True

        # Default model should be resolved without error
        default_model = registry.get_default_model()
        assert isinstance(default_model, str)
        assert len(default_model) > 0


@pytest.mark.asyncio
async def test_extract_and_store_durable_memories_uses_resolved_model():
    """
    FIX 3 Unit Test:
    Assert extract_and_store_durable_memories resolves model dynamically instead of hardcoding gpt-4o-mini.
    """
    import uuid
    from src.runtime.memory_hooks import extract_and_store_durable_memories

    completed_requests = []

    async def mock_complete(req):
        completed_requests.append(req)
        mock_resp = MagicMock()
        mock_resp.text = '[{"type": "SEMANTIC", "content": "ASEP is robust", "importance": 0.9}]'
        return mock_resp

    with patch("src.runtime.memory_hooks.AIRuntimeService") as mock_ai_cls, \
         patch("src.runtime.memory_hooks._ensure_agent_run", return_value=uuid.uuid4()), \
         patch("src.runtime.memory_hooks.MemoryService") as mock_mem_cls:
        
        mock_ai_instance = MagicMock()
        mock_ai_instance.registry.get_default_model.return_value = "gemini-2.0-flash"
        mock_ai_instance.complete = AsyncMock(side_effect=mock_complete)
        mock_ai_cls.return_value = mock_ai_instance

        mock_mem_instance = MagicMock()
        mock_mem_instance.store_memory = AsyncMock()
        mock_mem_cls.return_value = mock_mem_instance

        await extract_and_store_durable_memories(
            run_id=str(uuid.uuid4()),
            org_id=uuid.uuid4(),
            transcript="Agent goal: build app. Action: created files."
        )

        assert len(completed_requests) == 1
        req = completed_requests[0]
        # Must NOT be hardcoded gpt-4o-mini; must be the resolved model
        assert req.model != "gpt-4o-mini"
        assert req.model == "gemini-2.0-flash"


@pytest.mark.asyncio
async def test_execute_step_durability_and_pending_nodes():
    """
    FIX 1 Unit Test:
    Assert execute_step correctly persists synchronously with durability='sync',
    yielding events and leaving pending_nodes correctly populated in state.next
    without prematurely marking the run done.
    """
    import uuid
    mock_mem = MagicMock()
    mock_mem.working.set_state = AsyncMock()
    mock_mem.working.get_state = AsyncMock(return_value=None)
    runtime = LangGraphRuntime(mock_mem)

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    res = await runtime.execute_step(
        run_id=run_id,
        thread_id=thread_id,
        goal="Build a microservice",
        is_first=True,
    )

    assert res.get("status") == "running"
    assert len(res.get("events", [])) == 1
    
    # State checkpoint must reflect real pending nodes
    state = await runtime.graph.aget_state({"configurable": {"thread_id": thread_id}})
    assert state is not None
    assert len(state.next) > 0
    assert "orchestrator" in state.next

