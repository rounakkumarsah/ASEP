import re

with open('frontend/src/app/(dashboard)/settings/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

env_tab_ui = '''      case "environment":
        return (
          <AnimatedCard className="border-[#202833] bg-[#0D1117]/50 shadow-sm">
            <CardHeader className="border-b border-[#202833] pb-4">
              <CardTitle className="text-lg text-[#F5F7FA] flex items-center gap-2">
                <Lock className="h-5 w-5 text-[#22D3EE]" />
                Environment Policy ({environmentMode.toUpperCase()})
              </CardTitle>
              <CardDescription className="text-[#9CA6B5]">
                Manage auto-generated local secrets and check production key status.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8 pt-6">
              
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-[#F5F7FA]">Auto-Generated Local Secrets</h3>
                <p className="text-xs text-[#9CA6B5]">These are cryptographically secure random values used only for local development.</p>
                <div className="space-y-3">
                  {Object.entries(localSecrets).map(([key, value]) => (
                    <div key={key} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-[#202833] bg-[#0D1117]">
                      <span className="text-sm font-mono text-[#F5F7FA]">{key}</span>
                      <div className="flex items-center gap-3 mt-2 sm:mt-0">
                        <span className="text-xs font-mono bg-[#111720] px-2 py-1 rounded text-[#9CA6B5]">
                          ••••••••••••••••
                        </span>
                      </div>
                    </div>
                  ))}
                  {Object.keys(localSecrets).length === 0 && (
                    <div className="text-xs text-muted-foreground italic">No local secrets generated yet. Start a project run to initialize them.</div>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-medium text-[#F5F7FA]">Production Key Status</h3>
                <p className="text-xs text-[#9CA6B5]">Checklist of external dependencies required before deployment can proceed.</p>
                <div className="space-y-3">
                  {Object.entries(credentialsStatus).map(([key, value]) => {
                    const isMock = value === "mock";
                    return (
                      <div key={key} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-[#202833] bg-[#0D1117]">
                        <span className="text-sm font-medium text-[#F5F7FA]">{key}</span>
                        <div className="flex items-center gap-3 mt-2 sm:mt-0">
                          {isMock ? (
                            <span className="text-xs flex items-center gap-1.5 text-amber-500 bg-amber-500/10 px-2 py-1 rounded">
                              <AlertTriangle className="h-3.5 w-3.5" />
                              Running in Test Mode (Mock)
                            </span>
                          ) : (
                            <span className="text-xs flex items-center gap-1.5 text-[#2DD4A3] bg-[#2DD4A3]/10 px-2 py-1 rounded">
                              <Check className="h-3.5 w-3.5" />
                              Connected (LIVE)
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {Object.keys(credentialsStatus).length === 0 && (
                    <div className="text-xs text-muted-foreground italic">No external dependencies detected yet.</div>
                  )}
                </div>
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "delete_account":'''

content = content.replace('      case "delete_account":', env_tab_ui)

with open('frontend/src/app/(dashboard)/settings/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated settings/page.tsx renderTabContent")
