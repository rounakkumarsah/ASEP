import re

with open('frontend/src/lib/stores/playgroundStore.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Add to interface
interface_addition = '''
  // Workflow Graph Live Execution State
  phaseMap: string[];
  setPhaseMap: (map: string[]) => void;
  activeNode: string | null;
'''
content = content.replace('  // Workflow Graph Live Execution State\n  activeNode: string | null;', interface_addition)

# Add to implementation
impl_addition = '''
      setSelectedProjectName: (name) => set({ selectedProjectName: name }),

      phaseMap: [],
      setPhaseMap: (map) => set({ phaseMap: map }),

      activeNode: null,
'''
content = content.replace('      setSelectedProjectName: (name) => set({ selectedProjectName: name }),\n\n      activeNode: null,', impl_addition)

with open('frontend/src/lib/stores/playgroundStore.ts', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated playgroundStore.ts")
