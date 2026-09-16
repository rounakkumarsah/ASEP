import re

with open('frontend/src/components/playground/RightPanel.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

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
  const mapMsg = messages.find((m) => m.role === "system" && m.content.includes("Phase map generated:"));
  if (mapMsg) {
    const match = mapMsg.content.match(/Phase map generated: (.*?)\\./);
    if (match && match[1]) {
      const phases = match[1].split(" -> ");
      PIPELINE_STEPS = [
        { id: "orchestrator", label: "Orchestrator", desc: "Product classification & phase mapping" },
        ...phases.map(p => ({
          id: p,
          label: p.split("_").map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") + " Phase",
          desc: "Execution phase"
        }))
      ];
    }
  }
'''

content = re.sub(r'const PIPELINE_STEPS = \[[\s\S]*?\];', replacement.strip(), content)

with open('frontend/src/components/playground/RightPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated RightPanel.tsx")
