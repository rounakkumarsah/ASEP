import re

with open('backend/src/api/routers/conversations.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('goal=payload.goal, research_mode=payload.research_mode', 'goal=payload.goal, research_mode=payload.research_mode, environment_mode=payload.environment_mode')

with open('backend/src/api/routers/conversations.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated start_run")
