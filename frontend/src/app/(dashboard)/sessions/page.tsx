"use client";

import * as React from "react";
import { useSessions } from "@/lib/api/hooks/use-sessions";
import { SessionCard } from "@/components/dashboard/sessions/session-card";
import { Loader2, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SessionsPage() {
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
          <Button size="sm">
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
        <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg">
          <div className="bg-muted h-12 w-12 rounded-full flex items-center justify-center mb-4">
            <Bot className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-foreground">No active sessions</h3>
          <p className="text-sm mt-1 mb-4">
            Start a new agent execution to see it here.
          </p>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Session
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <SessionCard key={session.sessionId} session={session} />
          ))}
        </div>
      )}
    </div>
  );
}

// Just importing Bot inside the file if missing
import { Bot } from "lucide-react";
