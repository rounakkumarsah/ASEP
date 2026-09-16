import re

with open('src/runtime/runtime.py', 'r') as f:
    content = f.read()

new_imports = '''
from src.runtime.nodes import (
    NodeRegistry,
    orchestrator_node,
    research_phase_node,
    blueprint_phase_node,
    scaffold_phase_node,
    implement_phase_node,
    test_phase_node,
    security_audit_phase_node,
    deploy_phase_node,
    capability_blueprint_phase_node,
    tool_design_phase_node,
    agent_loop_implementation_phase_node,
    memory_state_design_phase_node,
    sandbox_tests_phase_node,
    evaluation_runs_phase_node,
    goal_decomposition_design_phase_node,
    planner_executor_critic_architecture_phase_node,
    tool_integration_phase_node,
    multi_step_test_scenarios_phase_node,
    failure_recovery_tests_phase_node,
    workflow_mapping_phase_node,
    trigger_action_design_phase_node,
    integration_points_phase_node,
    end_to_end_automation_tests_phase_node,
    error_handling_paths_phase_node,
    start_node_default,
    end_node_default,
)
'''

content = re.sub(r'from src\.runtime\.nodes import \([\s\S]*?\)', new_imports.strip(), content)

new_registers = '''
        # 2. Register agent node behaviors
        self.nodes.register("start", start_node_default)
        self.nodes.register("orchestrator", orchestrator_node)
        self.nodes.register("research", research_phase_node)
        self.nodes.register("blueprint", blueprint_phase_node)
        self.nodes.register("scaffold", scaffold_phase_node)
        self.nodes.register("implement", implement_phase_node)
        self.nodes.register("test", test_phase_node)
        self.nodes.register("security_audit", security_audit_phase_node)
        self.nodes.register("deploy", deploy_phase_node)
        self.nodes.register("capability_blueprint", capability_blueprint_phase_node)
        self.nodes.register("tool_design", tool_design_phase_node)
        self.nodes.register("agent_loop_implementation", agent_loop_implementation_phase_node)
        self.nodes.register("memory_state_design", memory_state_design_phase_node)
        self.nodes.register("sandbox_tests", sandbox_tests_phase_node)
        self.nodes.register("evaluation_runs", evaluation_runs_phase_node)
        self.nodes.register("goal_decomposition_design", goal_decomposition_design_phase_node)
        self.nodes.register("planner_executor_critic_architecture", planner_executor_critic_architecture_phase_node)
        self.nodes.register("tool_integration", tool_integration_phase_node)
        self.nodes.register("multi_step_test_scenarios", multi_step_test_scenarios_phase_node)
        self.nodes.register("failure_recovery_tests", failure_recovery_tests_phase_node)
        self.nodes.register("workflow_mapping", workflow_mapping_phase_node)
        self.nodes.register("trigger_action_design", trigger_action_design_phase_node)
        self.nodes.register("integration_points", integration_points_phase_node)
        self.nodes.register("end_to_end_automation_tests", end_to_end_automation_tests_phase_node)
        self.nodes.register("error_handling_paths", error_handling_paths_phase_node)
        self.nodes.register("end", end_node_default)
'''

content = re.sub(r'# 2\. Register agent node behaviors[\s\S]*?# 3\.', new_registers.strip() + '\\n\\n        # 3.', content)

with open('src/runtime/runtime.py', 'w') as f:
    f.write(content)
print("Updated runtime.py")

with open('src/runtime/graph.py', 'r') as f:
    graph_content = f.read()

new_router = '''
        def phase_router(state: AgentState) -> str:
            # The node advances to the next phase in the phase_map
            # Only if current phase criteria is met
            current = state.get("current_phase")
            phase_map = state.get("phase_map", [])
            status = state.get("status")
            
            if not current or not phase_map:
                return "end"
                
            if status != "verified":
                # Strict enforcement: if status is not verified, it is a hard error.
                # In real execution, we would log it and pause or retry. 
                # For this implementation, we loop back to current to retry.
                return current
                
            try:
                idx = phase_map.index(current)
                if idx + 1 < len(phase_map):
                    return phase_map[idx + 1]
                return "end"
            except ValueError:
                return "end"

        # The orchestrator decides the first phase
        self.workflow.add_conditional_edges("orchestrator", phase_router)
        
        # Register all possible phases in conditional edges
        all_phases = [
            "research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy",
            "capability_blueprint", "tool_design", "agent_loop_implementation", "memory_state_design",
            "sandbox_tests", "evaluation_runs", "goal_decomposition_design", "planner_executor_critic_architecture",
            "tool_integration", "multi_step_test_scenarios", "failure_recovery_tests", "workflow_mapping",
            "trigger_action_design", "integration_points", "end_to_end_automation_tests", "error_handling_paths"
        ]
        
        for phase in all_phases:
            if phase in self.nodes.get_all():
                self.workflow.add_conditional_edges(phase, phase_router)
'''

graph_content = re.sub(r'def phase_router\(state: AgentState\) -> str:[\s\S]*?self\.workflow\.add_edge\("end", END\)', new_router.strip() + '\\n                \\n        self.workflow.add_edge("end", END)', graph_content)

with open('src/runtime/graph.py', 'w') as f:
    f.write(graph_content)
print("Updated graph.py")
