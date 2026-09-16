import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('    setGithubActiveFile,\n  } = usePlaygroundStore();', '    setGithubActiveFile,\n    environmentMode,\n    setLocalSecrets,\n    setCredentialsStatus,\n  } = usePlaygroundStore();')
content = content.replace('research_mode: researchMode,\n          }),', 'research_mode: researchMode,\n            environment_mode: environmentMode,\n          }),')

# Also handle new SSE markers: [Local Secrets] and [Credentials Status]
sse_parser = '''                          } else if (messageItem.content.includes("[Metrics]")) {'''
new_sse_parser = '''                          } else if (messageItem.content.includes("[Local Secrets]")) {
                            try {
                                setLocalSecrets(JSON.parse(messageItem.content.replace("[Local Secrets]", "").trim()));
                            } catch {}
                          } else if (messageItem.content.includes("[Credentials Status]")) {
                            try {
                                setCredentialsStatus(JSON.parse(messageItem.content.replace("[Credentials Status]", "").trim()));
                            } catch {}
                          } else if (messageItem.content.includes("[Metrics]")) {'''

content = content.replace(sse_parser, new_sse_parser)

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated CenterWorkspace.tsx")
