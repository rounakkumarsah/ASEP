import re

with open('backend/src/runtime/nodes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add to clarification_gate_node
old_clarification = '            "messages": [{"role": "system", "content": msg}]\n        }'
new_clarification = '''            "messages": [
                {"role": "system", "content": f"[Local Secrets] {json.dumps(local_secrets)}"},
                {"role": "system", "content": f"[Credentials Status] {json.dumps(clarifications_gathered)}"},
                {"role": "system", "content": msg}
            ]
        }'''
content = content.replace('            "messages": [{"role": "system", "content": msg}]\n        }', new_clarification)

old_deploy = '            "messages": [{"role": "system", "content": "Deploy Clarification Gate: 100% Production keys secured. Swapping .env to production values."}]\n    }'
new_deploy = '''            "messages": [
                {"role": "system", "content": f"[Credentials Status] {json.dumps(credentials_status)}"},
                {"role": "system", "content": "Deploy Clarification Gate: 100% Production keys secured. Swapping .env to production values."}
            ]
    }'''
content = content.replace(old_deploy, new_deploy)

with open('backend/src/runtime/nodes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated nodes.py to emit secrets")
