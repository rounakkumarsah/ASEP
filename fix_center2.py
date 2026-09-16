import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

bad_pattern = r'                          \} else if \(messageItem\.content\.includes\("\[Security Audit\]"\)\) \{ \{\n.*?setActiveCenterTab\("security"\);\n.*?\} catch \{\}'
content = re.sub(bad_pattern, '', content, flags=re.DOTALL)

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed syntax error")
