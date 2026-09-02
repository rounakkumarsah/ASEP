with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''        elif "deepseek" in model_lower:''',
'''        elif "deepseek" in model_lower or "openrouter" in model_lower:'''
)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'w', encoding='utf-8') as f:
    f.write(text)
