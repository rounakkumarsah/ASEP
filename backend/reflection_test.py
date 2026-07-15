import asyncio
from src.reflection import Reflector, ReflectionPolicy, ReflectionTrigger, ReflectionReport
from src.evaluation.metrics import SessionMetrics
from src.evaluation.scoring import AllScores
from src.evaluation.trajectory import Trajectory
from src.planner.provider import LLMProvider

class MockLLM(LLMProvider):
    async def chat_complete(self, messages, json_output=False):
        return '''{
            "passed": false,
            "failure_analysis": {
                "category": "tool_failure",
                "contributing_factors": ["network timeout"]
            },
            "items": [
                {
                    "category": "tool_usage",
                    "failure_description": "API call timed out.",
                    "root_cause": "No retry logic for network requests.",
                    "evidence": "Step 3 shows timeout.",
                    "recommendation": "Always use exponential backoff.",
                    "confidence": 0.95
                }
            ]
        }'''

class MockMemoryManager:
    class Procedural:
        def __init__(self):
            self.added = 0
        async def add_procedure(self, name, description, steps, metadata):
            self.added += 1
            print(f"Mock procedural memory received: {name}")
    def __init__(self):
        self.procedural = self.Procedural()

async def run_integration_test():
    llm = MockLLM()
    memory = MockMemoryManager()
    reflector = Reflector(llm, memory)

    policy = ReflectionPolicy(trigger=ReflectionTrigger.ALWAYS, min_confidence_threshold=0.9, update_procedural_memory=True)
    traj = Trajectory(session_id="s1", run_id="r1", thread_id="s1", trace_id="t1")
    metrics = SessionMetrics(session_id="s1", run_id="r1", thread_id="s1", trace_id="t1")
    scores = AllScores(passed=False)

    report = await reflector.reflect(
        session_id="s1",
        run_id="r1",
        trajectory=traj,
        metrics=metrics,
        scores=scores,
        policy=policy
    )

    assert report is not None
    assert report.session_id == "s1"
    assert report.passed is False
    assert len(report.items) == 1
    assert report.items[0].confidence == 0.95
    assert memory.procedural.added == 1, "Memory writer should have added 1 procedure"
    
    policy_never = ReflectionPolicy(trigger=ReflectionTrigger.NEVER)
    report_none = await reflector.reflect("s1", "r1", traj, metrics, scores, policy_never)
    assert report_none is None

    print("Integration test passed!")

asyncio.run(run_integration_test())
