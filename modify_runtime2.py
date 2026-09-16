import re

with open('backend/src/runtime/runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('self, run_id: str, thread_id: str, goal: str = "", research_mode: str = "balanced"', 'self, run_id: str, thread_id: str, goal: str = "", research_mode: str = "balanced", environment_mode: str = "local"')
content = content.replace('"goal": goal,\n            "messages": [{"role": "user", "content": goal}] if goal else [],', '"goal": goal,\n            "messages": [{"role": "user", "content": goal}] if goal else [],\n            "environment_mode": environment_mode,\n            "credentials_status": {},\n            "local_secrets": {},')

with open('backend/src/runtime/runtime.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated runtime.py")
