"use client";

import * as React from "react";
import { useMemories } from "@/lib/api/hooks/use-memory";
import { MemoryType } from "@/lib/api/types";
import { SearchToolbar } from "@/components/dashboard/shared/search-toolbar";
import { MemoryCard } from "@/components/dashboard/memory/memory-card";
import { Loader2, BrainCircuit } from "lucide-react";
import { Button } from "@/components/ui/button";

const TABS: { id: MemoryType; label: string }[] = [
  { id: "working", label: "Working Memory" },
  { id: "episodic", label: "Episodic Memory" },
  { id: "semantic", label: "Semantic Memory" },
  { id: "procedural", label: "Procedural Memory" },
];

export default function MemoryWorkspacePage() {
  const [activeTab, setActiveTab] = React.useState<MemoryType>("working");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");

  // Simple debounce
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data, isLoading, isError, refetch } = useMemories(
    activeTab,
    debouncedQuery,
  );
  const memories = data?.items || [];

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Memory Workspace
          </h1>
          <p className="text-muted-foreground mt-1">
            Explore the cognitive storage architecture and autonomous memory
            banks.
          </p>
        </div>
      </div>

      <SearchToolbar
        placeholder={`Search ${activeTab} memory...`}
        value={searchQuery}
        onChange={setSearchQuery}
      />

      <div className="flex flex-col flex-1 gap-6">
        {/* Custom Tabs */}
        <div className="border-b border-border w-full">
          <nav className="-mb-px flex space-x-6 overflow-x-auto pb-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-h-[400px]">
          {isLoading ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
              <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
              <p>Scanning memory banks...</p>
            </div>
          ) : isError ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
              <p className="font-medium">Failed to retrieve memories</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                className="mt-4"
              >
                Retry Connection
              </Button>
            </div>
          ) : memories.length === 0 ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
              <div className="bg-muted h-12 w-12 rounded-full flex items-center justify-center mb-4">
                <BrainCircuit className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="font-semibold text-foreground">
                No memories found
              </h3>
              <p className="text-sm mt-1 max-w-sm text-center">
                {searchQuery
                  ? `No results match your search in ${activeTab} memory.`
                  : `The ${activeTab} memory bank is currently empty.`}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-10">
              {memories.map((item) => (
                <MemoryCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
