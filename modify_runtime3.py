import re

with open('backend/src/runtime/runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('clarification_gate_node,', 'clarification_gate_node,\n    deploy_clarification_gate_node,')
content = content.replace('self.nodes.register("clarification_gate", clarification_gate_node)', 'self.nodes.register("clarification_gate", clarification_gate_node)\n        self.nodes.register("deploy_clarification_gate", deploy_clarification_gate_node)')

with open('backend/src/runtime/runtime.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated runtime.py")
