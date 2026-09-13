import json
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.runtime.visualizer import parse_graph_to_react_flow

if __name__ == '__main__':
    result = parse_graph_to_react_flow()
    target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/src/lib/workflow-graph.json'))
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    with open(target_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    n_nodes = len(result['nodes'])
    n_edges = len(result['edges'])
    print(f"Successfully exported graph JSON with {n_nodes} nodes and {n_edges} edges to {target_path}")