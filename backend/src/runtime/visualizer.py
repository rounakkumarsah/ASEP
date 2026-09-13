import logging
from typing import Any
from src.runtime.runtime import get_langgraph_runtime

logger = logging.getLogger(__name__)

NODE_METADATA: dict[str, dict[str, str]] = {
    'start': {
        'label': 'Run Initializer',
        'role': 'Lifecycle',
        'description': 'Initializes run session and execution context',
        'icon': 'Play',
        'color': '#3B82F6',
    },
    'supervisor': {
        'label': 'Supervisor Agent',
        'role': 'Orchestrator',
        'description': 'Analyzes objective, classifies intent and determines agent routes',
        'icon': 'ShieldAlert',
        'color': '#8B5CF6',
    },
    'planner': {
        'label': 'Planner Agent',
        'role': 'Decomposer',
        'description': 'Decomposes objective into sequential executable subtasks',
        'icon': 'ListTodo',
        'color': '#06B6D4',
    },
    'research': {
        'label': 'Research Swarm (MCP)',
        'role': 'Context Discovery',
        'description': 'Searches web documentation and calls external MCP server tools',
        'icon': 'Globe',
        'color': '#F59E0B',
    },
    'rag': {
        'label': 'RAG Engine (MAG)',
        'role': 'Memory Retrieval',
        'description': 'Retrieves codebase AST and semantic vector embeddings',
        'icon': 'Database',
        'color': '#10B981',
    },
    'coding': {
        'label': 'Coding Agent',
        'role': 'Synthesis',
        'description': 'Synthesizes code solution using LLM with assembled context',
        'icon': 'Code2',
        'color': '#EC4899',
    },
    'validate': {
        'label': 'Human-in-the-Loop Gate',
        'role': 'Governance',
        'description': 'Applies security policy and halts on risky container actions',
        'icon': 'CheckCircle2',
        'color': '#EF4444',
    },
    'end': {
        'label': 'Run Finalizer',
        'role': 'Lifecycle',
        'description': 'Finalizes task state, registers metrics and returns solution',
        'icon': 'Flag',
        'color': '#10B981',
    }
}

def parse_graph_to_react_flow() -> dict[str, Any]:
    """Parses the current LangGraph StateGraph into React Flow nodes and edges."""
    runtime = get_langgraph_runtime()
    g = runtime.graph.get_graph()

    ordered_ids = ['start', 'supervisor', 'planner', 'research', 'rag', 'coding', 'validate', 'end']
    nodes = []

    spacing_x = 280
    start_x = 60
    start_y = 160

    for idx, node_id in enumerate(ordered_ids):
        meta = NODE_METADATA.get(node_id, {
            'label': node_id.capitalize(),
            'role': 'Agent',
            'description': f'LangGraph node {node_id}',
            'icon': 'Cpu',
            'color': '#22D3EE',
        })

        nodes.append({
            'id': node_id,
            'type': 'agentNode',
            'position': {'x': start_x + (idx * spacing_x), 'y': start_y},
            'data': {
                'id': node_id,
                'label': meta['label'],
                'role': meta['role'],
                'description': meta['description'],
                'icon': meta['icon'],
                'color': meta['color'],
                'stepIndex': idx + 1,
            }
        })

    edges = []
    for e in g.edges:
        src = e.source
        tgt = e.target
        if src == '__start__' or tgt == '__end__':
            continue
        edge_id = f'edge_{src}_{tgt}'
        edges.append({
            'id': edge_id,
            'source': src,
            'target': tgt,
            'animated': True,
            'style': {'stroke': '#22D3EE', 'strokeWidth': 2},
            'data': {'conditional': e.conditional}
        })

    # Add loop-back edge for human rejection
    edges.append({
        'id': 'edge_validate_coding_loopback',
        'source': 'validate',
        'target': 'coding',
        'animated': True,
        'style': {'stroke': '#EF4444', 'strokeWidth': 2, 'strokeDasharray': '5 5'},
        'data': {'label': 'Rejection / Revision'}
    })

    return {'nodes': nodes, 'edges': edges}