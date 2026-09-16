import re

with open('src/runtime/nodes.py', 'r') as f:
    content = f.read()

orchestrator_code = '''
async def orchestrator_node(state: AgentState) -> dict[str, Any]:
    goal = state.get("goal", "")
    logger.info("ORCHESTRATOR analyzing request: %s", goal)
    
    goal_lower = goal.lower()
    
    # Classify product type based on keywords
    if "ai agent" in goal_lower:
        product_type = "ai_agent"
        phase_map = ["research", "capability_blueprint", "tool_design", "agent_loop_implementation", "memory_state_design", "sandbox_tests", "evaluation_runs", "security_audit", "deploy"]
    elif "agentic ai" in goal_lower or "multi-agent" in goal_lower:
        product_type = "agentic_ai"
        phase_map = ["research", "goal_decomposition_design", "planner_executor_critic_architecture", "tool_integration", "multi_step_test_scenarios", "failure_recovery_tests", "security_audit", "deploy"]
    elif "automation" in goal_lower or "workflow" in goal_lower:
        product_type = "ai_automation"
        phase_map = ["research", "workflow_mapping", "trigger_action_design", "integration_points", "end_to_end_automation_tests", "error_handling_paths", "security_audit", "deploy"]
    elif "api" in goal_lower: 
        product_type = "api"
        phase_map = ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]
    elif "bot" in goal_lower: 
        product_type = "bot"
        phase_map = ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]
    elif "website" in goal_lower: 
        product_type = "website"
        phase_map = ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]
    elif "app" in goal_lower: 
        product_type = "app"
        phase_map = ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]
    else:
        product_type = "web-app"
        phase_map = ["research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"]

    # No Hallucination Rules constraints injected into system message
    hallucination_rules = (
        "NO HALLUCINATION RULES:\\n"
        "- NEVER claim a feature works without running it in the sandbox first.\\n"
        "- NEVER invent API methods or library functions. Verify external APIs in docs.\\n"
        "- NEVER hardcode fake data in final artifacts.\\n"
        "- Every generated file must pass syntax/lint checks.\\n"
        "- Ship partial-but-real over complete-but-fake."
    )

    return {
        "status": "orchestrating",
        "product_type": product_type,
        "phase_map": phase_map,
        "current_phase": phase_map[0] if phase_map else "end",
        "messages": [
            {
                "role": "system",
                "content": f"Orchestrator classified product as '{product_type}'. Phase map generated: {' -> '.join(phase_map)}.\\n\\n{hallucination_rules}"
            }
        ]
    }
'''

content = re.sub(r'async def orchestrator_node.*?return \{\s*"status": "orchestrating".*?\}\s*\}', orchestrator_code, content, flags=re.DOTALL)

with open('src/runtime/nodes.py', 'w') as f:
    f.write(content)

print("Replaced orchestrator_node.")
