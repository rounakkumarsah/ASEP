import re

with open('backend/src/runtime/state.py', 'r', encoding='utf-8') as f:
    content = f.read()

addition = '''
    # Environment Policy
    environment_mode: str
    credentials_status: dict[str, Any]
    local_secrets: dict[str, str]
'''
content = content.replace('    token_usage_per_phase: dict[str, int]', '    token_usage_per_phase: dict[str, int]\n' + addition)

with open('backend/src/runtime/state.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated state.py")
