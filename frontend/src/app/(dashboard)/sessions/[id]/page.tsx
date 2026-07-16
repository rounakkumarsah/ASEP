"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "@/lib/api/hooks/use-sessions";
import { SessionStatusBadge } from "@/components/dashboard/sessions/session-status-badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Bot,
  PlayCircle,
  Clock,
  Activity,
  TerminalSquare,
  Loader2,
} from "lucide-react";

export default function SessionDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: session, isLoading, isError } = useSession(id);

  if (isLoading) {
    return (
      <div className="h-[500px] w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Connecting to session stream...</p>
      </div>
    );
  }

  if (isError || !session) {
    return (
      <div className="h-[500px] w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg">
        <p className="font-medium mb-4">
          Session not found or connection lost.
        </p>
        <Button onClick={() => router.push("/sessions")} variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Sessions
        </Button>
      </div>
    );
  }

  const startedAtDate = new Date(session.startedAt);
  const timeElapsed = Math.floor(
    (Date.now() - startedAtDate.getTime()) / 60000,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/sessions")}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight font-mono">
                {session.sessionId}
              </h1>
              <SessionStatusBadge status={session.status} />
            </div>
            <div className="flex items-center text-sm text-muted-foreground gap-4 mt-1">
              <span className="flex items-center gap-1.5">
                <Activity className="h-4 w-4" /> {session.runId}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="h-4 w-4" /> Started {timeElapsed}m ago
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="destructive" size="sm">
            Halt Execution
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="flex flex-col h-[500px]">
            <CardHeader className="border-b border-border/50 pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TerminalSquare className="h-5 w-5 text-primary" /> Execution
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 flex-1 bg-muted/20 relative">
              {/* Timeline Placeholder */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground p-8 text-center">
                <Loader2 className="h-10 w-10 animate-spin text-muted-foreground/30 mb-4" />
                <h3 className="font-semibold text-foreground mb-1">
                  Live streaming not yet connected
                </h3>
                <p className="text-sm max-w-sm">
                  In a future phase, this area will stream live execution logs,
                  agent reasoning traces, and standard output.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Status & Context */}
        <div className="space-y-6">
          {/* Progress Card */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Overall Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">
              <div className="flex justify-between items-end mb-2">
                <span className="text-3xl font-bold tracking-tighter">
                  {session.progress}%
                </span>
                <span className="text-sm font-medium text-primary mb-1">
                  {session.stage}
                </span>
              </div>
              <Progress value={session.progress} className="h-2.5" />
            </CardContent>
          </Card>

          {/* Active Agent Card */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Bot className="h-4 w-4" /> Active Agent
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded bg-primary/10 flex items-center justify-center border border-primary/20">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">{session.activeAgent}</p>
                  <p className="text-xs text-muted-foreground">
                    Operating autonomously
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Current Task Card */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <PlayCircle className="h-4 w-4" /> Current Task
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5">
              <p className="text-sm leading-relaxed border-l-2 border-primary pl-4 py-1">
                {session.currentTask}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
