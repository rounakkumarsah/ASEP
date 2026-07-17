from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from src.multi_agent.contracts import AgentRole, AgentState, AgentRequest
from src.multi_agent.registry import AgentRegistry
from src.multi_agent.supervisor import SupervisorAgent
from src.multi_agent.planner_agent import PlannerAgent
from src.multi_agent.knowledge_agent import KnowledgeAgent
from src.multi_agent.research_agent import ResearchAgent
from src.multi_agent.memory_agent import MemoryAgent
from src.multi_agent.executor_agent import ExecutionAgent
from src.multi_agent.reflection_agent import ReflectionAgent
from src.multi_agent.evaluator_agent import EvaluationAgent
from src.multi_agent.governance_agent import GovernanceAgent

def get_mock_knowledge_agent() -> KnowledgeAgent:
    retriever_mock = MagicMock()
    async def mock_retrieve(*args, **kwargs):
        return [
            {
                "chunk_id": "chunk-1",
                "score": 0.95,
                "text": "Relevant context segment text.",
                "filename": "code.py",
                "file_path": "/path/code.py"
            }
        ]
    retriever_mock.retrieve = mock_retrieve
    return KnowledgeAgent(retriever=retriever_mock)

@pytest.mark.asyncio
async def test_agent_registry_discovery():
    registry = AgentRegistry()
    
    # Register planner and knowledge agent
    planner = PlannerAgent()
    knowledge = get_mock_knowledge_agent()
    
    registry.register(planner)
    registry.register(knowledge)
    
    # Discover by capability
    planning_agents = registry.discover("goal_decomposition")
    assert planner in planning_agents
    
    # Health checks
    health_states = registry.health()
    assert health_states[AgentRole.PLANNER.value] is True
    assert health_states[AgentRole.KNOWLEDGE.value] is True

@pytest.mark.asyncio
async def test_supervisor_workflow_orchestration():
    registry = AgentRegistry()
    
    # Register all agents in sandbox registry
    supervisor = SupervisorAgent(registry=registry)
    planner = PlannerAgent()
    knowledge = get_mock_knowledge_agent()
    research = ResearchAgent()
    memory = MemoryAgent()
    executor = ExecutionAgent()
    reflection = ReflectionAgent()
    evaluator = EvaluationAgent()
    governance = GovernanceAgent()
    
    registry.register(supervisor)
    registry.register(planner)
    registry.register(knowledge)
    registry.register(research)
    registry.register(memory)
    registry.register(executor)
    registry.register(reflection)
    registry.register(evaluator)
    registry.register(governance)
    
    # Execute workflow session
    req = AgentRequest(
        execution_id="workflow-exec-1",
        correlation_id="correlation-1",
        input_data={"request": "Generate code instructions for the ASEP system."}
    )
    
    resp = await supervisor.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert resp.output_data["status"] == "completed"
    assert "result" in resp.output_data["final_result"].lower() or resp.output_data["final_result"] != ""

@pytest.mark.asyncio
async def test_governance_rejection_gate():
    registry = AgentRegistry()
    
    supervisor = SupervisorAgent(registry=registry)
    planner = PlannerAgent()
    knowledge = get_mock_knowledge_agent()
    research = ResearchAgent()
    executor = ExecutionAgent()
    governance = GovernanceAgent()
    
    registry.register(supervisor)
    registry.register(planner)
    registry.register(knowledge)
    registry.register(research)
    registry.register(executor)
    registry.register(governance)
    
    # Query designed to trigger governance rejection rule (contains "exploit" or similar restricted keyword)
    req = AgentRequest(
        execution_id="workflow-exec-2",
        correlation_id="correlation-2",
        input_data={"request": "Generate a security bypass exploit."}
    )
    
    resp = await supervisor.execute(req)
    assert resp.status == AgentState.COMPLETED
    assert resp.output_data["status"] == "rejected"
    assert "rejected" in resp.output_data["final_result"].lower()
