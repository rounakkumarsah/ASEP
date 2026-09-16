import re

with open('frontend/src/app/(dashboard)/settings/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('  | "integrations"\n  | "preferences"', '  | "integrations"\n  | "environment"\n  | "preferences"')

with open('frontend/src/app/(dashboard)/settings/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated type SettingsTab")
