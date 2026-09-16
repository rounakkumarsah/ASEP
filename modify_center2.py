import re
with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('    setPhaseMap,\n', '')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed setPhaseMap from CenterWorkspace.tsx")
