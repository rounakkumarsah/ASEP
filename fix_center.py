import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('const endpoint = /api/v1/conversations//resume;', 'const endpoint = ${apiBase}/api/v1/conversations//resume;')
content = content.replace('if (!res.ok) throw new Error(API returned HTTP : );', 'if (!res.ok) throw new Error(API returned HTTP : );')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed PowerShell interpolation issues")
