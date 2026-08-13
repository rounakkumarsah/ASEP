"use client";

import * as React from "react";
import { useSessions } from "@/lib/api/hooks/use-sessions";
import { SessionCard } from "@/components/dashboard/sessions/session-card";
import { Loader2, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { AnimatedModal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter } from "@/components/ui/animated-modal";

export default function SessionsPage() {
  const [isNewSessionOpen, setIsNewSessionOpen] = React.useState(false);
  const {
    data: sessions,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useSessions();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Sessions</h1>
          <p className="text-muted-foreground">
            Monitor and manage live autonomous agent executions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setIsNewSessionOpen(true)} className="bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] font-bold">
            <Plus className="mr-2 h-4 w-4" />
            New Session
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
          <p>Loading active sessions...</p>
        </div>
      ) : isError ? (
        <div className="h-[400px] w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg">
          <p className="font-medium">Failed to load sessions</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="mt-4"
          >
            Try again
          </Button>
        </div>
      ) : !sessions || sessions.length === 0 ? (
        <EmptyState
          icon={Bot}
          title="No active sessions"
          description="Start a new agent execution to monitor live runtime telemetry."
          action={
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Session
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <SessionCard key={session.sessionId} session={session} />
          ))}
        </div>
      )}

      <AnimatedModal isOpen={isNewSessionOpen} onClose={() => setIsNewSessionOpen(false)}>
        <ModalHeader>
          <ModalTitle>Deploy New Agent Session</ModalTitle>
          <ModalDescription>Initialize a new autonomous execution environment with specific tooling and policies.</ModalDescription>
        </ModalHeader>
        <ModalContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#F5F7FA]">Objective</label>
            <input 
              type="text" 
              className="w-full bg-[#090B0F] border border-[#202833] rounded-md px-3 py-2 text-sm text-[#F5F7FA] focus:outline-none focus:border-[#22D3EE] transition-colors"
              placeholder="e.g. Refactor API endpoints"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#F5F7FA]">Base Image Runtime</label>
            <select className="w-full bg-[#090B0F] border border-[#202833] rounded-md px-3 py-2 text-sm text-[#F5F7FA] focus:outline-none focus:border-[#22D3EE] transition-colors">
              <option>Ubuntu 22.04 + Node 18</option>
              <option>Alpine + Python 3.11</option>
              <option>Debian + Rust 1.70</option>
            </select>
          </div>
        </ModalContent>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsNewSessionOpen(false)} className="border-[#202833] bg-transparent text-[#F5F7FA] hover:bg-[#202833]">
            Cancel
          </Button>
          <Button onClick={() => setIsNewSessionOpen(false)} className="bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] font-semibold">
            Deploy Session
          </Button>
        </ModalFooter>
      </AnimatedModal>
    </div>
  );
}

// Just importing Bot inside the file if missing
import { Bot } from "lucide-react";
