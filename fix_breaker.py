import sys
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('if self.circuit_breakers[primary_name].allow_request():', 'if True:')
text = text.replace('if name in self.providers and self.circuit_breakers[name].allow_request():', 'if name in self.providers:')

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'w', encoding='utf-8') as f:
    f.write(text)
