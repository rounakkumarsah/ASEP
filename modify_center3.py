import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('resetActiveNodes,', 'resetActiveNodes,\n    setPhaseMap,')

parse_code = '''
                            } else if (messageItem.content.includes("Phase map generated:")) {
                              const match = messageItem.content.match(/Phase map generated: (.*?)\\./);
                              if (match && match[1]) {
                                const phases = match[1].split(" -> ");
                                setPhaseMap(phases);
                              }
                            } else if (messageItem.content.includes("[Security Audit]")) {
'''
content = content.replace('                            } else if (messageItem.content.includes("[Security Audit]")) {', parse_code.strip() + ' {')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CenterWorkspace.tsx to properly use setPhaseMap")
