import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we destruct setPhaseMap from the store
if 'setPhaseMap' not in content:
    content = content.replace('resetActiveNodes,', 'resetActiveNodes,\n    setPhaseMap,')

# Parse the system message
parse_code = '''
                            } else if (messageItem.content.includes("Phase map generated:")) {
                              const match = messageItem.content.match(/Phase map generated: (.*?)\\./);
                              if (match && match[1]) {
                                const phases = match[1].split(" -> ");
                                setPhaseMap(phases);
                              }
                            }
'''
content = content.replace('                            } else if (messageItem.content.includes("[Security Audit]")) {\n                              const findingsStr = messageItem.content.replace("[Security Audit]", "").trim();', parse_code.strip() + '\n                            } else if (messageItem.content.includes("[Security Audit]")) {\n                              const findingsStr = messageItem.content.replace("[Security Audit]", "").trim();')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CenterWorkspace.tsx")
