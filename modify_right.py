import re

with open('frontend/src/components/playground/RightPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Update RightPanel destructs
content = content.replace('const { messages, isThinking, activeNode, completedNodes, sessionMetrics } = usePlaygroundStore();', 'const { messages, isThinking, activeNode, completedNodes, sessionMetrics, phaseMap } = usePlaygroundStore();')

# Revert my bad mapMsg code and use phaseMap
replacement = '''
  const DEFAULT_PIPELINE_STEPS = [
    { id: "orchestrator", label: "Orchestrator", desc: "Product classification & phase mapping" },
    { id: "research", label: "Research Phase", desc: "Gather requirements & context" },
    { id: "blueprint", label: "Blueprint Phase", desc: "Architecture & system design" },
    { id: "scaffold", label: "Scaffold Phase", desc: "Boilerplate & foundation setup" },
    { id: "implement", label: "Implement Phase", desc: "Core logic & module construction" },
    { id: "test", label: "Test Phase", desc: "Unit & integration testing" },
    { id: "security_audit", label: "Security Audit", desc: "Vulnerability scanning" },
    { id: "deploy", label: "Deploy Phase", desc: "Release & deployment prep" },
  ];

  let PIPELINE_STEPS = DEFAULT_PIPELINE_STEPS;
  if (phaseMap && phaseMap.length > 0) {
    PIPELINE_STEPS = [
      { id: "orchestrator", label: "Orchestrator", desc: "Product classification & phase mapping" },
      ...phaseMap.map(p => ({
        id: p,
        label: p.split("_").map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") + " Phase",
        desc: "Execution phase"
      }))
    ];
  }
'''

content = re.sub(r'const DEFAULT_PIPELINE_STEPS = \[[\s\S]*?\}\s*\}', replacement.strip(), content)

with open('frontend/src/components/playground/RightPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated RightPanel.tsx")
