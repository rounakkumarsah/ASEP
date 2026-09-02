import sys
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\service.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = \"\"\"            logger.warn(\"Failover\", provider=provider.name, error=str(last_error))\"\"\"
replacement = \"\"\"            logger.warn(\"Failover\", provider=provider.name, error=str(last_error))
            if provider.name == 'gemini':
                raise RuntimeError(f\"Gemini Error: {str(last_error)}\") from last_error\"\"\"

text = text.replace(target, replacement)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\service.py', 'w', encoding='utf-8') as f:
    f.write(text)
