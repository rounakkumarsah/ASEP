import re

with open('frontend/src/lib/stores/playgroundStore.ts', 'r', encoding='utf-8') as f:
    content = f.read()

state_addition = '''  // Environment Mode
  environmentMode: "local" | "deploy";
  setEnvironmentMode: (mode: "local" | "deploy") => void;
  localSecrets: Record<string, string>;
  setLocalSecrets: (secrets: Record<string, string>) => void;
  credentialsStatus: Record<string, string | boolean>;
  setCredentialsStatus: (status: Record<string, string | boolean>) => void;

  // System Prompt'''

content = content.replace('  // System Prompt', state_addition)

impl_addition = '''  // Environment Mode
  environmentMode: "local",
  setEnvironmentMode: (mode) => set({ environmentMode: mode }),
  localSecrets: {},
  setLocalSecrets: (secrets) => set({ localSecrets: secrets }),
  credentialsStatus: {},
  setCredentialsStatus: (status) => set({ credentialsStatus: status }),

  // System Prompt'''

content = content.replace('  // System Prompt', impl_addition)

with open('frontend/src/lib/stores/playgroundStore.ts', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated playgroundStore.ts")
