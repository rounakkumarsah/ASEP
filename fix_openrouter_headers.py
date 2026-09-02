import sys
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'headers = {\"Authorization\": f\"Bearer {self.api_key}\"}'
replacement = 'headers = {\"Authorization\": f\"Bearer {self.api_key}\", \"HTTP-Referer\": \"https://asep-ai.vercel.app\", \"X-Title\": \"ASEP Agent\"}'

text = text.replace(target, replacement)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
