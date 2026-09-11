"use client";

import * as React from "react";

export default function PlaygroundClient() {
  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] w-full bg-[#0A0A0A] text-white overflow-hidden">
      {/* 1. Top Header Bar */}
      <header className="flex items-center justify-between h-14 px-4 border-b border-gray-800 bg-[#111]">
        <div className="flex items-center space-x-4">
          <span className="font-bold text-sm">Acme Corp ▾</span>
          <span className="text-gray-400 text-sm">/</span>
          <span className="font-semibold text-sm">Engineering Workspace</span>
          <span className="px-2 py-1 bg-gray-800 text-xs rounded-md text-gray-300">No Project Linked</span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-xs text-yellow-500">⚡ 1.2s Latency</span>
          <span className="text-xs text-green-400">💰 $0.02 Cost</span>
          <div className="flex -space-x-2">
            <div className="w-6 h-6 rounded-full bg-blue-500 border border-[#111]"></div>
            <div className="w-6 h-6 rounded-full bg-red-500 border border-[#111]"></div>
          </div>
          <button className="text-xs bg-white text-black px-3 py-1 rounded-md font-medium">+ Invite</button>
        </div>
      </header>

      {/* 2. Main Workspace Area (3-Panel Layout) */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Panel A: Left Sidebar (Config) - Fixed Width */}
        <aside className="w-[320px] flex-shrink-0 border-r border-gray-800 flex flex-col bg-[#111]">
          <div className="flex border-b border-gray-800 text-sm">
            <button className="flex-1 py-2 text-center border-b-2 border-blue-500 text-white">Model</button>
            <button className="flex-1 py-2 text-center text-gray-400 hover:text-white">System Prompt</button>
            <button className="flex-1 py-2 text-center text-gray-400 hover:text-white">Tools</button>
          </div>
          <div className="p-4 flex-1 overflow-y-auto">
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Model Selection</label>
                <select className="w-full bg-[#0A0A0A] border border-gray-800 rounded p-2 text-sm text-white">
                  <option>Claude 3.5 Sonnet</option>
                  <option>GPT-4o</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Temperature (0.7)</label>
                <div className="w-full h-1 bg-gray-800 rounded mt-2">
                  <div className="w-[70%] h-full bg-blue-500 rounded"></div>
                </div>
              </div>
              <div className="pt-4 border-t border-gray-800 mt-4">
                <p className="text-sm text-gray-300">Left Panel Content (Placeholder for more settings...)</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Panel B: Center Workspace - Flexible Width */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#0A0A0A] relative">
          <div className="flex border-b border-gray-800 text-sm px-4 space-x-6">
            <button className="py-2 border-b-2 border-blue-500 text-white">Chat</button>
            <button className="py-2 text-gray-400 hover:text-white">Artifacts</button>
            <button className="py-2 text-gray-400 hover:text-white">Diff Viewer</button>
            <button className="py-2 text-gray-400 hover:text-white">Terminal</button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 flex flex-col justify-end pb-24">
            <div className="space-y-4 max-w-3xl mx-auto w-full">
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white p-3 rounded-lg rounded-tr-none max-w-[80%] text-sm">
                  Build me a Python script to scrape a website.
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-gray-800 text-white p-3 rounded-lg rounded-tl-none max-w-[80%] text-sm">
                  I will write a script using BeautifulSoup and Requests. Here is the plan...
                </div>
              </div>
            </div>
          </div>
          
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A] to-transparent">
            <div className="max-w-3xl mx-auto flex items-center bg-[#111] border border-gray-800 rounded-lg p-2">
              <button className="p-2 text-gray-400 hover:text-white">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
              </button>
              <input type="text" placeholder="Ask the agent to build, debug, or analyze..." className="flex-1 bg-transparent border-none outline-none px-3 text-sm text-white" />
              <button className="p-2 bg-blue-600 rounded text-white ml-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
          </div>
        </main>

        {/* Panel C: Right Sidebar (Agent Trace) - Fixed Width */}
        <aside className="w-[350px] flex-shrink-0 border-l border-gray-800 flex flex-col bg-[#111] overflow-y-auto">
          <div className="p-4 border-b border-gray-800">
            <h2 className="font-semibold text-sm">Agent Trace</h2>
          </div>
          
          <div className="p-4 space-y-6 flex-1 overflow-y-auto">
            {/* Execution Timeline */}
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Execution Timeline</h3>
              <div className="space-y-3">
                <div className="flex items-center text-sm">
                  <div className="w-5 h-5 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center mr-3 text-xs">✓</div>
                  <span className="text-gray-300">Planner created strategy</span>
                </div>
                <div className="flex items-center text-sm">
                  <div className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center mr-3 text-xs border border-blue-500/50">
                    <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></div>
                  </div>
                  <span className="text-white font-medium">Searching GitHub...</span>
                </div>
                <div className="flex items-center text-sm">
                  <div className="w-5 h-5 rounded-full bg-gray-800 text-gray-500 flex items-center justify-center mr-3 text-xs"></div>
                  <span className="text-gray-500">Generating code</span>
                </div>
              </div>
            </div>

            {/* Tool Calls Log */}
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Live Tool Calls</h3>
              <div className="bg-[#0A0A0A] border border-gray-800 rounded p-3 text-xs font-mono text-gray-400 space-y-1 h-32 overflow-y-auto">
                <div>&gt; _call: default_api:search_web</div>
                <div className="text-green-400">  {"{"}&quot;query&quot;: &quot;beautifulsoup tutorial&quot;{"}"}</div>
                <div>&gt; _response: success</div>
                <div>&gt; _call: default_api:write_to_file</div>
                <div className="text-yellow-400">  {"{"}&quot;targetFile&quot;: &quot;scraper.py&quot;{"}"}</div>
              </div>
            </div>

            {/* Sources Panel */}
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Sources (3)</h3>
              <div className="space-y-2">
                <div className="bg-[#0A0A0A] border border-gray-800 rounded p-2 text-xs text-blue-400 flex items-center">
                  <span className="truncate">https://pypi.org/project/beautifulsoup4/</span>
                </div>
                <div className="bg-[#0A0A0A] border border-gray-800 rounded p-2 text-xs text-blue-400 flex items-center">
                  <span className="truncate">https://docs.python-requests.org/</span>
                </div>
              </div>
            </div>

            {/* Confidence & Cost Meters */}
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Confidence Score</span>
                  <span className="text-green-400">95%</span>
                </div>
                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div className="w-[95%] h-full bg-green-500"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Estimated Cost</span>
                  <span className="text-yellow-400">$0.02 / $1.00 limit</span>
                </div>
                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div className="w-[2%] h-full bg-yellow-500"></div>
                </div>
              </div>
            </div>
          </div>
        </aside>

      </div>
    </div>
  );
}
