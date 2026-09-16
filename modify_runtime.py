import re

with open('backend/src/runtime/runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
import_statement = '    orchestrator_node,\n    clarification_gate_node,'
content = content.replace('    orchestrator_node,', import_statement)

# Register node
register_statement = '        self.nodes.register("research", research_phase_node)\n        self.nodes.register("clarification_gate", clarification_gate_node)'
content = content.replace('        self.nodes.register("research", research_phase_node)', register_statement)

with open('backend/src/runtime/runtime.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated runtime.py")
