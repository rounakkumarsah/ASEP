import asyncio
from src.governance import (
    RuntimeAuthorizer, Enforcer, ActionIntent, AuthorizationError
)

async def test_action():
    print("Test action executed successfully.")
    return "success"

async def run_integration_test():
    authorizer = RuntimeAuthorizer()
    enforcer = Enforcer(authorizer)
    
    # Test Guardrail Denial (System Prompt modification)
    blocked_intent = ActionIntent(
        session_id="s1", run_id="r1", thread_id="t1", trace_id="trace1",
        actor_role="executor", action_type="write", target="system_prompt.txt",
        justification="test"
    )
    
    try:
        await enforcer.enforce(blocked_intent, test_action)
        assert False, "Should have raised AuthorizationError"
    except AuthorizationError as e:
        print(f"Correctly caught authorization error: {e}")

    # Test Policy Approval (Terminal execution)
    approval_intent = ActionIntent(
        session_id="s1", run_id="r1", thread_id="t1", trace_id="trace1",
        actor_role="executor", action_type="execute_terminal", target="ls",
        justification="test"
    )
    
    result = await enforcer.enforce(approval_intent, test_action)
    assert result == "success"
    
    print("Integration test passed!")

asyncio.run(run_integration_test())
