import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('      let aiResponse = "";', '      let aiResponse = "";\n      const streamMessages: string[] = [];')
content = content.replace('      const streamMessages: string[] = [];\n\n      while (true) {', '\n      while (true) {')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed streamMessages")
