import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add states
state_addition = '''
  const [clarificationPrompt, setClarificationPrompt] = React.useState<string | null>(null);
  const [clarificationThreadId, setClarificationThreadId] = React.useState<string | null>(null);
  const [clarificationInput, setClarificationInput] = React.useState<string>("");
'''
content = content.replace('  const [toastMessage, setToastMessage] = React.useState<string | null>(null);', '  const [toastMessage, setToastMessage] = React.useState<string | null>(null);\n' + state_addition.strip())

# Add parsing logic
parse_code = '''
                          } else if (messageItem.content.includes("Phase map generated:")) {
                            const match = messageItem.content.match(/Phase map generated: (.*?)\\./);
                            if (match && match[1]) {
                              const phases = match[1].split(" -> ");
                              setPhaseMap(phases);
                            }
                          } else if (messageItem.content.includes("[Clarification Required]")) {
                            setClarificationPrompt(messageItem.content.replace("[Clarification Required]", "").trim());
                            // Extract threadId if not explicitly provided, we fallback to the global one
                            // But actually, we don't know the threadId here directly!
                            // wait, we can store it when calling fetch
                          } else if (messageItem.content.includes("[Security Audit]")) {
'''
content = content.replace('                          } else if (messageItem.content.includes("Phase map generated:")) {\n                            const match = messageItem.content.match(/Phase map generated: (.*?)\\./);\n                            if (match && match[1]) {\n                              const phases = match[1].split(" -> ");\n                              setPhaseMap(phases);\n                            }\n                          } else if (messageItem.content.includes("[Security Audit]")) {', parse_code.strip() + ' {')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CenterWorkspace.tsx states")
