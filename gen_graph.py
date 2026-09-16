import json
import copy

all_phases = [
    "research", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy",
    "capability_blueprint", "tool_design", "agent_loop_implementation", "memory_state_design",
    "sandbox_tests", "evaluation_runs", "goal_decomposition_design", "planner_executor_critic_architecture",
    "tool_integration", "multi_step_test_scenarios", "failure_recovery_tests", "workflow_mapping",
    "trigger_action_design", "integration_points", "end_to_end_automation_tests", "error_handling_paths"
]

nodes = [
    {
      "id": "start",
      "type": "agentNode",
      "position": { "x": 60, "y": 160 },
      "data": {
        "id": "start",
        "label": "Run Initializer",
        "role": "Lifecycle",
        "description": "Initializes run session and execution context",
        "icon": "Play",
        "color": "#3B82F6",
        "stepIndex": 1
      }
    },
    {
      "id": "orchestrator",
      "type": "agentNode",
      "position": { "x": 340, "y": 160 },
      "data": {
        "id": "orchestrator",
        "label": "Orchestrator",
        "role": "Routing",
        "description": "Classifies goal & generates phase map",
        "icon": "Cpu",
        "color": "#8B5CF6",
        "stepIndex": 2
      }
    }
]

edges = [
    {
      "id": "e-start-orchestrator",
      "source": "start",
      "target": "orchestrator",
      "animated": True,
      "style": { "stroke": "#3B82F6", "strokeWidth": 2 }
    }
]

# Just lay them out in a grid starting from x=620, y=50
x_start = 620
y_start = 50
x_step = 280
y_step = 120

for i, phase in enumerate(all_phases):
    row = i // 3
    col = i % 3
    nodes.append({
      "id": phase,
      "type": "agentNode",
      "position": { "x": x_start + col * x_step, "y": y_start + row * y_step },
      "data": {
        "id": phase,
        "label": phase.replace("_", " ").title(),
        "role": "Phase Node",
        "description": "Dynamically routed phase execution",
        "icon": "CheckCircle2",
        "color": "#10B981",
        "stepIndex": 3 + i
      }
    })
    
    # Connect orchestrator to all possible first phases, and each phase to deploy (just a dummy edge so it's not disconnected, or orchestrator connects to all to show routing)
    edges.append({
      "id": f"e-orch-{phase}",
      "source": "orchestrator",
      "target": phase,
      "animated": True,
      "style": { "stroke": "#9CA3AF", "strokeWidth": 1, "opacity": 0.3 }
    })

graph = {"nodes": nodes, "edges": edges}
with open('frontend/src/lib/workflow-graph.json', 'w') as f:
    json.dump(graph, f, indent=2)

print("Updated workflow-graph.json")
