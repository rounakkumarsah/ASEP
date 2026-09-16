import re

with open('backend/src/api/routers/conversations.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('research_mode: str = Field(\n        default="balanced",\n        description="The research mode/persona to use for this execution."\n    )', 'research_mode: str = Field(\n        default="balanced",\n        description="The research mode/persona to use for this execution."\n    )\n    environment_mode: str = Field(\n        default="local",\n        description="Target environment: local or deploy."\n    )')

with open('backend/src/api/routers/conversations.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated RunRequest schema")
