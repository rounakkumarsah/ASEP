import re

with open('frontend/src/components/dashboard/header.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add usePlaygroundStore import
content = content.replace('import { useSidebarStore } from "@/lib/stores/sidebarStore";', 'import { useSidebarStore } from "@/lib/stores/sidebarStore";\nimport { usePlaygroundStore } from "@/lib/stores/playgroundStore";')

# Get environmentMode
content = content.replace('  const { isMainSidebarOpen, toggleMainSidebar } = useSidebarStore();', '  const { isMainSidebarOpen, toggleMainSidebar } = useSidebarStore();\n  const { environmentMode, setEnvironmentMode, credentialsStatus } = usePlaygroundStore();')

# UI for the badge
ui = '''          <span className="text-[#667085]">/</span>
          <span className="text-[#F5F7FA] font-semibold tracking-wide mr-2">{breadcrumb}</span>
          
          <div className="relative group">
            <button 
              onClick={() => {
                if (environmentMode === 'local') {
                  const mocks = Object.values(credentialsStatus).filter(v => v === 'mock').length;
                  if (mocks > 0) {
                    if (confirm(Deploy Mode Activation:\\n\\n local mocks will be replaced with real services.\\nYou will be prompted for LIVE keys during deployment.\\n\\nProceed?)) {
                      setEnvironmentMode('deploy');
                    }
                  } else {
                    setEnvironmentMode('deploy');
                  }
                } else {
                  setEnvironmentMode('local');
                }
              }}
              className={px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase transition-colors cursor-pointer border }
              title="Click to toggle environment mode"
            >
              [{environmentMode}]
            </button>
          </div>'''
          
content = content.replace('          <span className="text-[#667085]">/</span>\n          <span className="text-[#F5F7FA] font-semibold tracking-wide">{breadcrumb}</span>', ui)

with open('frontend/src/components/dashboard/header.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated header.tsx")
