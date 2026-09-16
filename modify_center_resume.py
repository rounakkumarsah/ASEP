import re

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add handleResume
handle_resume = '''
  const handleResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarificationInput.trim() || !clarificationThreadId || isThinking) return;

    addMessage({
      role: 'user',
      content: clarificationInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    const decision = clarificationInput;
    setClarificationInput("");
    setClarificationPrompt(null);
    setIsThinking(true);

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token")
        : null;

      const apiBase = process.env.NEXT_PUBLIC_API_URL
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\\/+$/, "")
        : "";
      const endpoint = ${apiBase}/api/v1/conversations//resume;

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = Bearer ;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify({ decision }),
      });

      if (!res.ok) throw new Error(API returned HTTP : );
      if (!res.body) return;

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let aiResponse = "";
      const streamMessages: string[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") break;
            try {
              const data = JSON.parse(dataStr);
              if (data.event) {
                const nodeEntries = Object.entries(data.event);
                for (const [nodeName, updateVal] of nodeEntries) {
                  setActiveNode(nodeName);
                  addCompletedNode(nodeName);
                  const updateObj = updateVal as Record<string, unknown>;
                  const msg = updateObj.messages;
                  if (msg && Array.isArray(msg) && msg.length > 0) {
                    for (const m of msg) {
                      const messageItem = m as { role?: string; type?: string; name?: string; content?: string };
                      if (messageItem.role === "assistant" && messageItem.content && typeof messageItem.content === "string") {
                        aiResponse = messageItem.content;
                      } else if (messageItem.role === "system" && messageItem.content && typeof messageItem.content === "string") {
                        if (messageItem.content.includes("[Auto Router Toast]")) {
                          setToastMessage(messageItem.content.replace("[Auto Router Toast]", "").trim());
                          setTimeout(() => setToastMessage(null), 6000);
                        } else if (messageItem.content.includes("Phase map generated:")) {
                          const match = messageItem.content.match(/Phase map generated: (.*?)\\./);
                          if (match && match[1]) {
                            const phases = match[1].split(" -> ");
                            setPhaseMap(phases);
                          }
                        } else if (messageItem.content.includes("[Clarification Required]")) {
                          setClarificationPrompt(messageItem.content.replace("[Clarification Required]", "").trim());
                        } else if (messageItem.content.includes("[Security Audit]")) {
                          const findingsStr = messageItem.content.replace("[Security Audit]", "").trim();
                          try {
                              setSecurityFindings(JSON.parse(findingsStr));
                              setActiveCenterTab("security");
                          } catch {}
                        } else if (messageItem.content.includes("[Metrics]")) {
                          const metricsStr = messageItem.content.replace("[Metrics]", "").trim();
                          try {
                              const metrics = JSON.parse(metricsStr);
                              usePlaygroundStore.getState().setSessionMetrics(metrics);
                          } catch {}
                        }
                      }
                    }
                  }
                }
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      addMessage({
        role: "assistant",
        content: aiResponse || "Resumed execution.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } catch (error) {
      addMessage({
        role: "assistant",
        content: Error resuming run: ,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } finally {
      setIsThinking(false);
      setActiveNode(null);
    }
  };
'''

content = content.replace('  const handleSend = async (e: React.FormEvent) => {', handle_resume + '\n  const handleSend = async (e: React.FormEvent) => {')

# Capture threadId in handleSend
content = content.replace('const currentInput = input;\n    setInput("");', 'const currentInput = input;\n    setInput("");\n    const newThreadId = "playground-session-" + Date.now();\n    setClarificationThreadId(newThreadId);')
content = content.replace('thread_id: "playground-session-" + Date.now(),', 'thread_id: newThreadId,')

# Add UI for blocking card
ui_addition = '''
                      {clarificationPrompt && (
                        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 my-4 max-w-[85%]">
                          <div className="flex gap-3 mb-3 text-amber-500 font-medium">
                            <ShieldAlert className="h-5 w-5" />
                            <span>Action Required</span>
                          </div>
                          <div className="text-sm text-foreground mb-4">
                            {clarificationPrompt}
                          </div>
                          <form onSubmit={handleResume} className="flex gap-2">
                            <input
                              type="text"
                              value={clarificationInput}
                              onChange={(e) => setClarificationInput(e.target.value)}
                              placeholder="Enter credentials or type 'mock'..."
                              className="flex-1 bg-background/50 border border-border rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500/50"
                              disabled={isThinking}
                            />
                            <Button type="submit" disabled={isThinking || !clarificationInput.trim()} className="bg-amber-500 hover:bg-amber-600 text-white shrink-0">
                              Submit
                            </Button>
                          </form>
                        </div>
                      )}
'''
content = content.replace('                    {isThinking && (', ui_addition + '\n                    {isThinking && (')

with open('frontend/src/components/playground/CenterWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected resume handling and UI")
