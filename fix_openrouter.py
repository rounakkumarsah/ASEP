import sys
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('\"model\": request.model,', '\"model\": \"deepseek/deepseek-r1\" if request.model == \"deepseek-r1\" else request.model,')
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
