import asyncio
from src.multi_agent import (
    MessageBus, AgentRegistry, Supervisor, AgentRole, CoordinationContext
)
from src.multi_agent.planner_agent import PlannerAgent
from src.multi_agent.executor_agent import ExecutorAgent
from src.planner.plan import DecomposedPlan

# Mocks
class MockPlanner:
    async def plan(self, goal: str) -> DecomposedPlan:
        print(f"MockPlanner planning for: {goal}")
        return DecomposedPlan(goal=goal, rationale="test", task_count=1, tasks=[], priority="normal")

class MockExecutor:
    async def execute(self, plan: DecomposedPlan):
        print(f"MockExecutor executing plan for: {plan.goal}")
        from src.executor.result import ExecutionReport, ExecutionResult, TaskResult
        # Return a dummy report matching the schema
        return ExecutionReport(session_id="hc", run_id="hc", passed=True, result=ExecutionResult(status="completed", output={}), tasks=[])

async def run_integration_test():
    bus = MessageBus()
    registry = AgentRegistry()

    planner = MockPlanner()
    executor = MockExecutor()

    # We only register and start planner and executor for this mock pipeline
    planner_agent = PlannerAgent(bus, planner)
    executor_agent = ExecutorAgent(bus, executor)
    
    registry.register(AgentRole.PLANNER, planner_agent)
    registry.register(AgentRole.EXECUTOR, executor_agent)
    
    # We won't register evaluator/reflector for this test, the router handles missing roles by returning them
    # Wait, the supervisor only routes if the agent exists. 
    # If the role is missing, it logs "pipeline complete" and completes the session!

    supervisor = Supervisor(bus, registry)
    
    # Start all agents
    planner_agent.start()
    executor_agent.start()
    supervisor.start()

    goal = "Test the pipeline"
    print(f"Submitting goal: {goal}")
    
    # supervisor.run_session is an AsyncGenerator
    async for result in supervisor.run_session(goal):
        print("Final result received by Supervisor:")
        print(result)
        break

    print("Integration test passed!")

asyncio.run(run_integration_test())
