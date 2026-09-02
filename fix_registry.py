import sys
with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = \"\"\"
        # Always fallback to mock if everything else is broken
        if \"mock\" in self.providers and self.providers[\"mock\"] not in chain:
            chain.append(self.providers[\"mock\"])
\"\"\"
text = text.replace(target, '')

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\registry.py', 'w', encoding='utf-8') as f:
    f.write(text)
